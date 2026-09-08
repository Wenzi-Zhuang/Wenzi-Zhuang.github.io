import asyncio
import json
import time
from collections import defaultdict
from datetime import datetime, timezone

from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from .auth import current_student, issue_token, token_hash, verify_course_password
from .config import get_settings
from .database import Base, engine, get_db
from .models import Device, Student
from .services.deepseek import stream_answer
from .services.rag import retrieve

cfg = get_settings()
app = FastAPI(title=f"{cfg.course_name} AI API", docs_url=None if cfg.app_env == "production" else "/docs")
app.add_middleware(CORSMiddleware, allow_origins=[cfg.frontend_origin], allow_credentials=False,
                   allow_methods=["GET", "POST"], allow_headers=["Authorization", "Content-Type"])
student_locks: dict[str, asyncio.Lock] = defaultdict(asyncio.Lock)


class RegisterBody(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    student_no: str = Field(min_length=1, max_length=64)
    course_password: str
    platform: str | None = None
    language: str | None = None
    timezone: str | None = None


class ChatBody(BaseModel):
    question: str = Field(min_length=1, max_length=8000)
    skill: str = Field(default="课程知识解释", max_length=50)


@app.on_event("startup")
async def startup():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


@app.get("/health")
async def health(db: AsyncSession = Depends(get_db)):
    database = "ok"
    try:
        await db.execute(text("select 1"))
    except Exception:
        database = "error"
    return {"status": "ok" if database == "ok" else "degraded", "database": database,
            "course_library": "ok" if cfg.course_root.is_dir() else "missing",
            "deepseek_configured": bool(cfg.deepseek_api_key and cfg.deepseek_api_key != "CHANGE_ME")}


@app.post("/api/auth/register-device")
async def register(body: RegisterBody, request: Request, db: AsyncSession = Depends(get_db)):
    if not verify_course_password(body.course_password):
        raise HTTPException(403, "课程密码错误")
    student = (await db.execute(select(Student).where(Student.student_no == body.student_no.strip()))).scalar_one_or_none()
    if not student or student.status != "active" or student.name.strip() != body.name.strip():
        raise HTTPException(403, "姓名或学号不匹配")
    raw, digest, expires = issue_token()
    ip = request.client.host if request.client else None
    db.add(Device(student_id=student.student_id, token_hash=digest, expires_at=expires,
                  user_agent=request.headers.get("user-agent"), platform=body.platform,
                  language=body.language, timezone=body.timezone, first_ip=ip, last_ip=ip))
    await db.commit()
    return {"device_token": raw, "expires_at": expires, "student": {"name": student.name, "student_no": student.student_no}}


@app.get("/api/auth/me")
async def me(student: Student = Depends(current_student)):
    return {"name": student.name, "student_no": student.student_no}


@app.post("/api/auth/logout")
async def logout(request: Request, student: Student = Depends(current_student), db: AsyncSession = Depends(get_db)):
    auth = request.headers.get("authorization", "")[7:]
    device = (await db.execute(select(Device).where(Device.token_hash == token_hash(auth), Device.student_id == student.student_id))).scalar_one()
    device.revoked_at = datetime.now(timezone.utc)
    await db.commit()
    return {"ok": True}


@app.post("/api/chat/stream")
async def chat_stream(body: ChatBody, student: Student = Depends(current_student), db: AsyncSession = Depends(get_db)):
    lock = student_locks[str(student.student_id)]
    if lock.locked():
        raise HTTPException(409, "你已有一个回答正在生成")
    evidence, retrieval_ms = await retrieve(db, body.question)

    async def events():
        async with lock:
            try:
                yield f"event: meta\ndata: {json.dumps({'retrieval_ms': round(retrieval_ms), 'sources': [{'title': e.title, 'locator': e.locator} for e in evidence]}, ensure_ascii=False)}\n\n"
                async for token in stream_answer(body.question, body.skill, evidence):
                    yield f"event: token\ndata: {json.dumps({'text': token}, ensure_ascii=False)}\n\n"
                yield "event: done\ndata: {}\n\n"
            except Exception:
                yield f"event: error\ndata: {json.dumps({'message': '回答服务暂时不可用，请稍后重试'}, ensure_ascii=False)}\n\n"
    return StreamingResponse(events(), media_type="text/event-stream", headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})


@app.post("/api/chat")
async def chat(body: ChatBody, student: Student = Depends(current_student), db: AsyncSession = Depends(get_db)):
    lock = student_locks[str(student.student_id)]
    if lock.locked():
        raise HTTPException(409, "你已有一个回答正在生成")
    evidence, retrieval_ms = await retrieve(db, body.question)
    async with lock:
        try:
            answer = "".join([part async for part in stream_answer(body.question, body.skill, evidence)])
        except Exception as exc:
            raise HTTPException(503, "回答服务暂时不可用，请稍后重试") from exc
    return {"answer": answer, "retrieval_ms": round(retrieval_ms),
            "sources": [{"title": item.title, "locator": item.locator} for item in evidence]}
