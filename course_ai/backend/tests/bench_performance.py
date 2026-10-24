"""Bounded synthetic benchmark for local knowledge retrieval; no NAS writes."""

import os
import statistics
import tempfile
import time
from pathlib import Path


def benchmark(count: int, library: Path) -> tuple[float, float]:
    folder = library / "financial_accounting" / "20_knowledge_system"
    folder.mkdir(parents=True, exist_ok=True)
    for index in range(count):
        (folder / f"note-{index:04d}.md").write_text("会计基础与财务报表分析。\n" * 100, encoding="utf-8")
    from course_ai.backend.app.services.assistant_context import load_assistant_context
    elapsed = []
    for _ in range(20):
        start = time.perf_counter()
        load_assistant_context("financial_accounting", "会计基础")
        elapsed.append((time.perf_counter() - start) * 1000)
    for path in folder.glob("*.md"):
        path.unlink()
    return round(statistics.median(elapsed), 1), round(sorted(elapsed)[18], 1)


if __name__ == "__main__":
    with tempfile.TemporaryDirectory(prefix="course-ai-bench-") as temp:
        library = Path(temp) / "library"
        os.environ.update({
            "DATABASE_URL": "sqlite+aiosqlite:///" + str(Path(temp) / "unused.db"),
            "DEEPSEEK_API_KEY": "CHANGE_ME", "DEVICE_TOKEN_SECRET": "benchmark-only",
            "FRONTEND_ORIGIN": "https://wenzi-zhuang.github.io", "PUBLIC_API_BASE": "https://example.invalid",
            "ASSISTANT_LIBRARY_ROOT": str(library), "RUNTIME_CONFIG_ROOT": str(Path(temp) / "config"),
        })
        for count in (0, 200, 800):
            p50, p95 = benchmark(count, library)
            print(f"{count} small Markdown files: p50={p50} ms, p95={p95} ms (20 runs)")
