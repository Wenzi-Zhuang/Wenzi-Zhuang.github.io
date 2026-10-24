"""Roster-gated registration and browser-device authentication."""

import asyncio
import secrets
import time
import re
from collections import defaultdict, deque
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, Form, HTTPException, Request
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from .auth import current_student, issue_token, ph, token_hash, verify_password
from .config import get_settings
from .database import get_db
from .models import Device, Student
from .services.assistant_context import ASSISTANTS
from .services.student_files import roster_entry, roster_rows, save_devices, upsert_roster

router = APIRouter()
attempts: dict[str, deque[float]] = defaultdict(deque)
login_lock = asyncio.Lock()


def rate_limit(request: Request, student_no: str, record: bool = True) -> None:
    key = f"{request.client.host if request.client else 'unknown'}:{student_no}"
    recent = attempts[key]
    now = time.monotonic()
    while recent and recent[0] < now - 900:
        recent.popleft()
    if len(recent) >= 8:
        raise HTTPException(429, "验证次数过多，请 15 分钟后再试")
    if record:
        recent.append(now)


def allowed(assistant_id: str, student_no: str) -> dict:
    if assistant_id not in ASSISTANTS:
        raise HTTPException(404, "AI 助手不存在")
    row = roster_entry(assistant_id, student_no)
    if not row and student_no != "admin":
        raise HTTPException(403, "该学号不在本平台的学生名单中")
    return row or {"student_no": "admin", "name": "教师", "class_name": "管理员"}


class Credentials(BaseModel):
    assistant_id: str
    student_no: str = Field(pattern=r"^(?:\d{5,20}|admin)$")
    id_last6: str = Field(min_length=6, max_length=128)
    previous_token: str = ""


class RosterRecord(BaseModel):
    assistant_id: str
    student_no: str = Field(pattern=r"^\d{5,20}$")
    name: str = Field(min_length=1, max_length=100)
    class_name: str = Field(min_length=1, max_length=100)


@router.post("/api/auth/preview")
async def preview(body: Credentials, request: Request, db: AsyncSession = Depends(get_db)):
    rate_limit(request, body.student_no)
    if not re.fullmatch(r"\d{6}", body.id_last6):
        raise HTTPException(400, "请输入身份证后六位数字")
    if body.student_no == "admin":
        raise HTTPException(400, "管理员无需注册")
    row = allowed(body.assistant_id, body.student_no)
    existing = await db.scalar(select(Student).where(Student.student_no == body.student_no))
    if existing:
        raise HTTPException(409, "该学号已经注册，请直接登录")
    return {"student_no": body.student_no, "name": row["name"],
            "class_name": row["class_name"], "id_last6": body.id_last6}


@router.post("/api/auth/register")
async def register(body: Credentials, request: Request, db: AsyncSession = Depends(get_db)):
    rate_limit(request, body.student_no)
    if not re.fullmatch(r"\d{6}", body.id_last6):
        raise HTTPException(400, "请输入身份证后六位数字")
    if body.student_no == "admin":
        raise HTTPException(400, "管理员无需注册")
    row = allowed(body.assistant_id, body.student_no)
    student = Student(student_no=body.student_no, name=row["name"],
                      password_hash=ph.hash(body.id_last6), status="active")
    db.add(student)
    try:
        await db.commit()
    except IntegrityError as exc:
        await db.rollback()
        raise HTTPException(409, "该学号已经注册，请直接登录") from exc
    return {"status": "registered", "message": "注册成功，请登录"}


async def _device_rows(db: AsyncSession, student: Student) -> list[dict]:
    now = datetime.now(timezone.utc)
    devices = (await db.scalars(select(Device).where(Device.student_id == student.student_id,
                                                    Device.revoked_at.is_(None), Device.expires_at > now))).all()
    return [{"device_id": str(item.device_id), "last_seen_at": item.last_seen_at.isoformat(),
             "browser": (item.user_agent or "")[:100]} for item in devices]


async def _sync_student_devices(db: AsyncSession, student: Student) -> None:
    rows = await _device_rows(db, student)
    for assistant_id in ASSISTANTS:
        if roster_entry(assistant_id, student.student_no) or student.student_no == "admin":
            save_devices(assistant_id, student.student_no, rows)


@router.post("/api/auth/login")
async def login(body: Credentials, request: Request, db: AsyncSession = Depends(get_db)):
    rate_limit(request, body.student_no, record=False)
    if body.student_no != "admin" and not re.fullmatch(r"\d{6}", body.id_last6):
        raise HTTPException(400, "请输入身份证后六位数字")
    row = allowed(body.assistant_id, body.student_no)
    student = await db.scalar(select(Student).where(Student.student_no == body.student_no,
                                                    Student.status == "active"))
    if not student:
        rate_limit(request, body.student_no)
        raise HTTPException(403, "尚未注册，请先完成注册" if body.student_no != "admin" else "管理员尚未设置")
    if not verify_password(student.password_hash, body.id_last6):
        rate_limit(request, body.student_no)
        raise HTTPException(401, "学号或身份证后六位不正确")
    async with login_lock:
        now = datetime.now(timezone.utc)
        former_student = None
        if body.previous_token:
            old = await db.scalar(select(Device).where(Device.token_hash == token_hash(body.previous_token),
                                                       Device.revoked_at.is_(None)))
            if old:
                former_student = await db.get(Student, old.student_id)
                old.revoked_at = now
                await db.flush()
        active = await _device_rows(db, student)
        if len(active) >= 5:
            await db.rollback()
            raise HTTPException(403, "此账号已登录 5 台设备，请联系教师解除旧设备")
        raw, digest, expiry = issue_token()
        db.add(Device(student_id=student.student_id, token_hash=digest, expires_at=expiry,
                      user_agent=request.headers.get("user-agent", "")[:500],
                      first_ip=request.client.host if request.client else None,
                      last_ip=request.client.host if request.client else None))
        await db.commit()
    await _sync_student_devices(db, student)
    if former_student and former_student.student_id != student.student_id:
        await _sync_student_devices(db, former_student)
    return {"token": raw, "student_no": student.student_no, "name": row["name"],
            "class_name": row["class_name"], "is_admin": student.student_no == "admin"}


@router.get("/api/auth/me")
async def me(assistant_id: str, student: Student = Depends(current_student)):
    row = allowed(assistant_id, student.student_no)
    return {"student_no": student.student_no, "name": row["name"],
            "class_name": row["class_name"], "is_admin": student.student_no == "admin"}


@router.post("/api/auth/logout")
async def logout(request: Request, student: Student = Depends(current_student),
                 db: AsyncSession = Depends(get_db)):
    token = request.headers.get("authorization", "").removeprefix("Bearer ")
    device = await db.scalar(select(Device).where(Device.token_hash == token_hash(token)))
    if device:
        device.revoked_at = datetime.now(timezone.utc)
        await db.commit()
        await _sync_student_devices(db, student)
    return {"status": "logged_out"}


@router.get("/api/admin/roster")
async def get_roster(assistant_id: str, student: Student = Depends(current_student)):
    if student.student_no != "admin":
        raise HTTPException(403, "仅教师可查看学生名单")
    allowed(assistant_id, "admin")
    return {"students": roster_rows(assistant_id)}


@router.post("/api/admin/roster")
async def put_roster(body: RosterRecord, student: Student = Depends(current_student)):
    if student.student_no != "admin":
        raise HTTPException(403, "仅教师可管理学生名单")
    allowed(body.assistant_id, "admin")
    upsert_roster(body.assistant_id, body.student_no, body.name.strip(), body.class_name.strip())
    return {"status": "saved"}


ADMIN_SETUP_PAGE = """<!doctype html><html lang='zh-CN'><meta charset='utf-8'><title>教师账号初始化</title><body style='font:16px/1.7 system-ui;max-width:460px;margin:8vh auto;padding:24px'><h1>教师账号初始化</h1><p>请在自己的设备上输入 NAS 设置码，并设置至少 12 位的新口令。不要使用聊天中出现过的 140210。</p><form method='post'><label>NAS 设置码<input name='setup_code' type='password' required></label><br><label>教师新口令<input name='password' type='password' minlength='12' required></label><br><button>保存</button></form></body>"""


@router.get("/setup/admin", response_class=HTMLResponse)
async def admin_setup_page():
    return ADMIN_SETUP_PAGE


@router.post("/setup/admin", response_class=HTMLResponse)
async def admin_setup(request: Request, setup_code: str = Form(...), password: str = Form(...),
                      db: AsyncSession = Depends(get_db)):
    rate_limit(request, "admin-setup")
    cfg = get_settings()
    if cfg.setup_code == "CHANGE_ME" or not secrets.compare_digest(setup_code, cfg.setup_code):
        raise HTTPException(403, "设置码错误")
    if len(password) < 12 or password == "140210":
        raise HTTPException(400, "教师口令至少 12 位，且不能使用公开的初始数字")
    admin = await db.scalar(select(Student).where(Student.student_no == "admin"))
    if admin:
        raise HTTPException(409, "教师账号已设置；如需重置，请由 NAS 管理员在私有环境中处理")
    else:
        db.add(Student(student_no="admin", name="教师", password_hash=ph.hash(password), status="active"))
    await db.commit()
    return "<meta charset='utf-8'><p>教师账号已设置。请返回任一 AI 页面，使用 admin 和新口令登录。</p>"
