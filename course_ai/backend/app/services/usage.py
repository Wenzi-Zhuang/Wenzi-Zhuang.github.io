"""Persistent, per-student and per-assistant quotas."""

import asyncio
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

from fastapi import HTTPException
from sqlalchemy import func, select

from ..database import SessionLocal
from ..models import UsageEvent

MAX_FILE_BYTES = 500 * 1024
MAX_DAILY_FILE_BYTES = 1500 * 1024
CASE_FILE_BYTES = 1024 * 1024
CASE_DAILY_FILE_BYTES = 10 * 1024 * 1024
quota_lock = asyncio.Lock()


async def consume_quota(student_no: str, assistant_id: str, kind: str, byte_count: int = 0) -> None:
    now = datetime.now(timezone.utc)
    local_now = now.astimezone(ZoneInfo("Asia/Shanghai"))
    day_start = local_now.replace(hour=0, minute=0, second=0, microsecond=0).astimezone(timezone.utc)
    key = student_no
    async with quota_lock:
        async with SessionLocal() as db:
            base = (UsageEvent.client_id == key, UsageEvent.assistant_id == assistant_id,
                    UsageEvent.kind == kind)
            if kind == "question":
                hour_count = await db.scalar(select(func.count()).where(*base, UsageEvent.created_at >= now - timedelta(hours=1)))
                day_count = await db.scalar(select(func.count()).where(*base, UsageEvent.created_at >= day_start))
                if (hour_count or 0) >= 50 or (day_count or 0) >= 150:
                    raise HTTPException(429, "暂时无法回答：本平台每小时最多 50 个问题、每天最多 150 个问题，请稍后再试。")
            else:
                file_limit = CASE_FILE_BYTES if assistant_id == "case_study" else MAX_FILE_BYTES
                daily_limit = CASE_DAILY_FILE_BYTES if assistant_id == "case_study" else MAX_DAILY_FILE_BYTES
                if byte_count > file_limit:
                    size_label = "1 MB" if assistant_id == "case_study" else "500 KB"
                    raise HTTPException(413, f"文件过大，无法处理：单个文件不能超过 {size_label}。")
                count, total = (await db.execute(select(func.count(), func.coalesce(func.sum(UsageEvent.byte_count), 0))
                                                 .where(*base, UsageEvent.created_at >= day_start))).one()
                if count >= 10 or total + byte_count > daily_limit:
                    size_label = "10 MB" if assistant_id == "case_study" else "1500 KB"
                    raise HTTPException(429, f"文件过多，无法处理：本平台每天最多 10 个文件，累计不能超过 {size_label}。")
            db.add(UsageEvent(client_id=key, assistant_id=assistant_id, kind=kind, byte_count=byte_count,
                              created_at=now))
            await db.commit()
