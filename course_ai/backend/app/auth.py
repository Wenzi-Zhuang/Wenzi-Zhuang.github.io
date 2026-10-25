import hashlib
import hmac
import secrets
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError
from fastapi import Depends, Header, HTTPException, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from .config import get_settings
from .database import get_db
from .models import CourseDevice, Student

ph = PasswordHasher()


def token_hash(token: str) -> str:
    return hmac.new(get_settings().device_token_secret.encode(), token.encode(), hashlib.sha256).hexdigest()


def verify_password(password_hash: str, password: str) -> bool:
    try:
        return ph.verify(password_hash, password)
    except (VerifyMismatchError, TypeError):
        return False


@dataclass
class CourseSession:
    student: Student
    device: CourseDevice
    assistant_id: str

    def student_for(self, assistant_id: str) -> Student:
        if self.assistant_id != assistant_id:
            raise HTTPException(403, "请先在本课程注册并登录")
        return self.student


async def current_session(
    authorization: str | None = Header(default=None), db: AsyncSession = Depends(get_db)
) -> CourseSession:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(401, "需要设备验证")
    digest = token_hash(authorization[7:])
    now = datetime.now(timezone.utc)
    result = await db.execute(
        select(CourseDevice, Student).join(Student).where(
            CourseDevice.token_hash == digest,
            CourseDevice.revoked_at.is_(None),
            CourseDevice.expires_at > now,
            Student.status == "active",
        )
    )
    row = result.first()
    if not row:
        raise HTTPException(401, "设备凭证无效或已过期")
    device, student = row
    device.last_seen_at = now
    await db.commit()
    return CourseSession(student=student, device=device, assistant_id=device.assistant_id)


def issue_token() -> tuple[str, str, datetime]:
    raw = secrets.token_urlsafe(48)
    expires = datetime.now(timezone.utc) + timedelta(days=get_settings().device_token_days)
    return raw, token_hash(raw), expires

