import asyncio
import json
from collections.abc import AsyncIterator

import httpx

from .rag import Evidence
from .runtime_config import load_deepseek_config

SYSTEM_PROMPT = """你是会计学课程AI助教。优先依据提供的课程证据回答；不得编造课程来源。回答应教学化、准确、简洁，必要时依次说明概念、原理、确认、计量、分录、报表影响、案例和易错点。不要复述或猜测学生身份。证据不足时明确说明内容依据一般会计知识。"""


def messages(question: str, skill: str, evidence: list[Evidence], system_prompt: str = SYSTEM_PROMPT) -> list[dict]:
    context = "\n\n".join(
        f"[来源 {i}: {e.title}{'，' + e.locator if e.locator else ''}]\n{e.text}"
        for i, e in enumerate(evidence, 1)
    ) or "没有检索到可靠课程证据。"
    return [
        {"role": "system", "content": system_prompt},
        {"role": "system", "content": f"当前教学模式：{skill}\n课程证据：\n{context}"},
        {"role": "user", "content": question},
    ]


async def stream_answer(question: str, skill: str, evidence: list[Evidence], system_prompt: str = SYSTEM_PROMPT) -> AsyncIterator[str]:
    async for token in stream_messages(messages(question, skill, evidence, system_prompt)):
        yield token


async def stream_messages(message_list: list[dict]) -> AsyncIterator[str]:
    cfg = load_deepseek_config()
    headers = {"Authorization": f"Bearer {cfg.api_key}", "Content-Type": "application/json"}
    payload = {"model": cfg.model, "messages": message_list, "stream": True}
    last_error = None
    for attempt in range(3):
        try:
            async with httpx.AsyncClient(timeout=httpx.Timeout(90, connect=10)) as client:
                async with client.stream("POST", f"{cfg.base_url.rstrip('/')}/chat/completions", headers=headers, json=payload) as response:
                    if response.status_code == 429:
                        raise httpx.HTTPStatusError("rate limited", request=response.request, response=response)
                    response.raise_for_status()
                    async for line in response.aiter_lines():
                        if not line.startswith("data: ") or line == "data: [DONE]":
                            continue
                        data = json.loads(line[6:])
                        content = data["choices"][0]["delta"].get("content")
                        if content:
                            yield content
                    return
        except (httpx.HTTPError, KeyError, json.JSONDecodeError) as exc:
            last_error = exc
            if attempt < 2:
                await asyncio.sleep(2 ** attempt)
    raise RuntimeError("DeepSeek 暂时不可用") from last_error

