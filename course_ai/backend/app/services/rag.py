import re
import time
from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..models import SourceChunk


@dataclass
class Evidence:
    chunk_id: str
    title: str
    locator: str | None
    text: str


def terms(query: str) -> set[str]:
    return set(re.findall(r"[\u4e00-\u9fff]{2,}|[A-Za-z0-9_]{2,}", query.lower()))


async def retrieve(db: AsyncSession, query: str, limit: int = 8) -> tuple[list[Evidence], float]:
    started = time.perf_counter()
    # Permission filtering deliberately happens here, before ranking or model context creation.
    rows = (await db.execute(select(SourceChunk).where(
        SourceChunk.visibility == "student", SourceChunk.status == "active"
    ))).scalars().all()
    needles = terms(query)
    scored = []
    for row in rows:
        haystack = (row.title + " " + row.text).lower()
        score = sum(haystack.count(term) for term in needles) + row.authority_level / 1000
        if score > row.authority_level / 1000:
            scored.append((score, row))
    scored.sort(key=lambda item: item[0], reverse=True)
    evidence = [Evidence(r.chunk_id, r.title, r.locator, r.text) for _, r in scored[:limit]]
    return evidence, (time.perf_counter() - started) * 1000

