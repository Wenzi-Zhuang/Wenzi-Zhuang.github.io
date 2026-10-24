"""Local end-to-end preview API; isolated DB and fake AI answers."""

import os
from pathlib import Path

root = Path("/private/tmp/course-ai-browser-test-20261025")
root.mkdir(exist_ok=True)
os.environ.update({
    "DATABASE_URL": "sqlite+aiosqlite:///" + str(root / "test.db"),
    "DEEPSEEK_API_KEY": "CHANGE_ME", "DEVICE_TOKEN_SECRET": "local-browser-test-only",
    "FRONTEND_ORIGIN": "http://127.0.0.1:8765", "PUBLIC_API_BASE": "http://127.0.0.1:8766",
    "ASSISTANT_LIBRARY_ROOT": str(root / "library"), "RUNTIME_CONFIG_ROOT": str(root / "config"),
    "SETUP_CODE": "local-browser-test-setup-code",
})

from course_ai.backend.app import main  # noqa: E402


async def fake_stream(_messages):
    yield "本地模拟回答：对话连接正常。"


main.stream_messages = fake_stream

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(main.app, host="127.0.0.1", port=8766)
