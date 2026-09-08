import hashlib
import hmac
import secrets
from datetime import datetime, timedelta, timezone

from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError
from fastapi import Depends, Header, HTTPException, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from .config import get_settings
from .database import get_db
from .models import Device, Student

ph = PasswordHasher()


def token_hash(token: str) -> str:
    return hmac.new(get_settings().device_token_secret.encode(), token.encode(), hashlib.sha256).hexdigest()


def verify_course_password(password: str) -> bool:
    try:
        return ph.verify(get_settings().course_access_password_hash, password)
    except VerifyMismatchError:
        return False


async def current_student(
    authorization: str | None = Header(default=None), db: AsyncSession = Depends(get_db)
) -> Student:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(401, "需要设备验证")
    digest = token_hash(authorization[7:])
    now = datetime.now(timezone.utc)
    result = await db.execute(
        select(Device, Student).join(Student).where(
            Device.token_hash == digest,
            Device.revoked_at.is_(None),
            Device.expires_at > now,
            Student.status == "active",
        )
    )
    row = result.first()
    if not row:
        raise HTTPException(401, "设备凭证无效或已过期")
    device, student = row
    device.last_seen_at = now
    await db.commit()
    return student


def issue_token() -> tuple[str, str, datetime]:
    raw = secrets.token_urlsafe(48)
    expires = datetime.now(timezone.utc) + timedelta(days=get_settings().device_token_days)
    return raw, token_hash(raw), expires

