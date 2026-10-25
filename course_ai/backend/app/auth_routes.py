"""Roster-gated registration and browser-device authentication."""

import asyncio
import secrets
import time
import re
from collections import defaultdict, deque
from datetime import datetime, timezone
from html import escape

from fastapi import APIRouter, Depends, Form, HTTPException, Request
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, Field
from sqlalchemy import select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from .auth import CourseSession, current_session, issue_token, ph, token_hash, verify_password
from .config import get_settings
from .database import get_db
from .models import CourseDevice, CourseRegistration, Student
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
    id_last6: str = Field(min_length=1)
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
        if not verify_password(existing.password_hash, body.id_last6):
            raise HTTPException(401, "身份证后六位与已有注册信息不符")
        registration = await db.scalar(select(CourseRegistration).where(
            CourseRegistration.student_id == existing.student_id,
            CourseRegistration.assistant_id == body.assistant_id))
        if registration:
            raise HTTPException(409, "该学号已在本课程注册，请直接登录")
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
    student = await db.scalar(select(Student).where(Student.student_no == body.student_no))
    if student:
        if not verify_password(student.password_hash, body.id_last6):
            raise HTTPException(401, "身份证后六位与已有注册信息不符")
        registration = await db.scalar(select(CourseRegistration).where(
            CourseRegistration.student_id == student.student_id,
            CourseRegistration.assistant_id == body.assistant_id))
        if registration:
            raise HTTPException(409, "该学号已在本课程注册，请直接登录")
    else:
        student = Student(student_no=body.student_no, name=row["name"],
                          password_hash=ph.hash(body.id_last6), status="active")
        db.add(student)
    try:
        await db.flush()
        db.add(CourseRegistration(student_id=student.student_id, assistant_id=body.assistant_id))
        await db.commit()
    except IntegrityError as exc:
        await db.rollback()
        raise HTTPException(409, "该学号已在本课程注册，请直接登录") from exc
    save_devices(body.assistant_id, body.student_no, [])
    return {"status": "registered", "message": "注册成功，请登录"}


async def _device_rows(db: AsyncSession, student: Student, assistant_id: str) -> list[dict]:
    now = datetime.now(timezone.utc)
    devices = (await db.scalars(select(CourseDevice).where(CourseDevice.student_id == student.student_id,
                                                          CourseDevice.assistant_id == assistant_id,
                                                          CourseDevice.revoked_at.is_(None),
                                                          CourseDevice.expires_at > now))).all()
    return [{"device_id": str(item.device_id), "last_seen_at": item.last_seen_at.isoformat(),
             "browser": (item.user_agent or "")[:100]} for item in devices]


async def _sync_student_devices(db: AsyncSession, student: Student, assistant_id: str) -> None:
    save_devices(assistant_id, student.student_no, await _device_rows(db, student, assistant_id))


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
    if body.student_no != "admin":
        registration = await db.scalar(select(CourseRegistration).where(
            CourseRegistration.student_id == student.student_id,
            CourseRegistration.assistant_id == body.assistant_id))
        if not registration:
            rate_limit(request, body.student_no)
            raise HTTPException(403, "尚未在本课程注册，请先完成注册")
    async with login_lock:
        now = datetime.now(timezone.utc)
        former_student = None
        if body.previous_token:
            old = await db.scalar(select(CourseDevice).where(
                CourseDevice.token_hash == token_hash(body.previous_token),
                CourseDevice.assistant_id == body.assistant_id,
                CourseDevice.revoked_at.is_(None)))
            if old:
                former_student = await db.get(Student, old.student_id)
                old.revoked_at = now
                await db.flush()
        active = await _device_rows(db, student, body.assistant_id)
        if len(active) >= 5:
            await db.rollback()
            raise HTTPException(403, "此账号已登录 5 台设备，请联系教师解除旧设备")
        raw, digest, expiry = issue_token()
        db.add(CourseDevice(student_id=student.student_id, assistant_id=body.assistant_id,
                            token_hash=digest, expires_at=expiry,
                            user_agent=request.headers.get("user-agent", "")[:500],
                            first_ip=request.client.host if request.client else None,
                            last_ip=request.client.host if request.client else None))
        await db.commit()
    await _sync_student_devices(db, student, body.assistant_id)
    if former_student and former_student.student_id != student.student_id:
        await _sync_student_devices(db, former_student, body.assistant_id)
    return {"token": raw, "student_no": student.student_no, "name": row["name"],
            "class_name": row["class_name"], "is_admin": student.student_no == "admin"}


@router.get("/api/auth/me")
async def me(assistant_id: str, session: CourseSession = Depends(current_session)):
    student = session.student_for(assistant_id)
    row = allowed(assistant_id, student.student_no)
    return {"student_no": student.student_no, "name": row["name"],
            "class_name": row["class_name"], "is_admin": student.student_no == "admin"}


@router.post("/api/auth/logout")
async def logout(session: CourseSession = Depends(current_session),
                 db: AsyncSession = Depends(get_db)):
    session.device.revoked_at = datetime.now(timezone.utc)
    await db.commit()
    await _sync_student_devices(db, session.student, session.assistant_id)
    return {"status": "logged_out"}


@router.get("/api/admin/roster")
async def get_roster(assistant_id: str, session: CourseSession = Depends(current_session)):
    student = session.student_for(assistant_id)
    if student.student_no != "admin":
        raise HTTPException(403, "仅教师可查看学生名单")
    allowed(assistant_id, "admin")
    return {"students": roster_rows(assistant_id)}


@router.post("/api/admin/roster")
async def put_roster(body: RosterRecord, session: CourseSession = Depends(current_session)):
    student = session.student_for(body.assistant_id)
    if student.student_no != "admin":
        raise HTTPException(403, "仅教师可管理学生名单")
    allowed(body.assistant_id, "admin")
    upsert_roster(body.assistant_id, body.student_no, body.name.strip(), body.class_name.strip())
    return {"status": "saved"}


ADMIN_SETUP_PAGE = """<!doctype html><html lang='zh-CN'><meta charset='utf-8'><meta name='viewport' content='width=device-width,initial-scale=1'><title>教师账号设置</title><style>body{margin:0;background:#f3f7f4;color:#17211d;font:16px/1.7 system-ui,-apple-system,'PingFang SC',sans-serif}.box{box-sizing:border-box;width:min(480px,calc(100% - 32px));margin:8vh auto;padding:32px;background:#fff;border:1px solid #dfe7e2;border-radius:16px;box-shadow:0 18px 50px rgba(22,45,36,.08)}h1{margin:0 0 8px;font-size:25px}p{color:#65716b;font-size:14px}label{display:grid;gap:6px;margin-top:18px;color:#45564c;font-size:14px}input{box-sizing:border-box;width:100%;min-height:44px;padding:10px 12px;border:1px solid #cbd8d1;border-radius:8px;font:inherit}button{width:100%;min-height:45px;margin-top:24px;color:#fff;font-weight:700;background:#176b52;border:0;border-radius:8px}.error{color:#a43a36}</style><main class='box'><h1>教师账号设置</h1><p>账号固定为 admin。首次设置或修改口令都在这里完成；教师口令只需输入一次，没有长度或复杂度要求。NAS 设置码仅用于确认你有权修改账号。</p><p class='error' role='alert'>{{error}}</p><form method='post' autocomplete='off'><label>NAS 设置码<input name='setup_code' type='password' required autocomplete='off'></label><label>教师登录口令<input name='password' type='password' required autocomplete='new-password'></label><button type='submit'>保存教师口令</button></form></main>"""


@router.get("/setup/admin", response_class=HTMLResponse)
async def admin_setup_page():
    return ADMIN_SETUP_PAGE.replace("{{error}}", "")


@router.post("/setup/admin", response_class=HTMLResponse)
async def admin_setup(request: Request, setup_code: str = Form(...), password: str = Form(...),
                      db: AsyncSession = Depends(get_db)):
    rate_limit(request, "admin-setup")
    cfg = get_settings()
    if cfg.setup_code == "CHANGE_ME" or not secrets.compare_digest(setup_code, cfg.setup_code):
        message = "NAS 设置码不正确；请核对 /volume1/docker/course-ai/.env 中 SETUP_CODE 等号后的值。"
        return HTMLResponse(ADMIN_SETUP_PAGE.replace("{{error}}", escape(message)), status_code=403)
    if not password:
        return HTMLResponse(ADMIN_SETUP_PAGE.replace("{{error}}", "请输入教师登录口令。"), status_code=400)
    admin = await db.scalar(select(Student).where(Student.student_no == "admin"))
    if admin:
        admin.password_hash = ph.hash(password)
        await db.execute(update(CourseDevice).where(
            CourseDevice.student_id == admin.student_id,
            CourseDevice.revoked_at.is_(None)).values(revoked_at=datetime.now(timezone.utc)))
    else:
        db.add(Student(student_no="admin", name="教师", password_hash=ph.hash(password), status="active"))
    await db.commit()
    if admin:
        for assistant_id in ASSISTANTS:
            save_devices(assistant_id, "admin", [])
    return "<meta charset='utf-8'><main style='font:16px/1.7 system-ui;max-width:460px;margin:8vh auto;padding:24px'><h1>教师口令已保存</h1><p>请返回任一课程 AI 页面，使用 admin 和新口令登录。此前的教师登录凭证已失效。</p></main>"
