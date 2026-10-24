"""Private course rosters, device summaries and chat threads on the NAS."""

import json
import os
import re
import uuid
from datetime import datetime, timezone
from pathlib import Path

from ..config import get_settings
from .assistant_context import ASSISTANT_FOLDERS, ASSISTANTS

MAX_SAVED_FILE = 200 * 1024
SEED_STUDENTS = (
    {"student_no": "2011310411", "name": "邓伦", "class_name": "待填写"},
    {"student_no": "2013420430", "name": "于洋", "class_name": "待填写"},
)


def private_root(assistant_id: str) -> Path:
    if assistant_id not in ASSISTANTS:
        raise ValueError("AI 助手不存在")
    root = get_settings().assistant_library_root / ASSISTANT_FOLDERS[assistant_id] / "access"
    root.mkdir(mode=0o700, parents=True, exist_ok=True)
    if root.is_symlink():
        raise ValueError("课程私有目录不能是符号链接")
    root.chmod(0o700)
    return root


def _write_json(path: Path, data: object) -> None:
    if path.is_symlink():
        raise ValueError("不能写入符号链接")
    raw = json.dumps(data, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    if len(raw) > MAX_SAVED_FILE:
        raise ValueError("保存内容超过 200 KB，无法处理")
    temporary = path.with_name(path.name + "." + uuid.uuid4().hex + ".tmp")
    try:
        with temporary.open("xb") as handle:
            handle.write(raw)
        temporary.chmod(0o600)
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


def ensure_rosters() -> None:
    for assistant_id in ASSISTANTS:
        path = private_root(assistant_id) / "roster.json"
        if not path.exists():
            _write_json(path, list(SEED_STUDENTS))


def roster_entry(assistant_id: str, student_no: str) -> dict | None:
    path = private_root(assistant_id) / "roster.json"
    if path.is_symlink() or (path.exists() and path.stat().st_size > MAX_SAVED_FILE):
        raise ValueError("学生名单文件不安全或过大")
    try:
        rows = json.loads(path.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError):
        return None
    return next((row for row in rows if row.get("student_no") == student_no), None)


def roster_rows(assistant_id: str) -> list[dict]:
    path = private_root(assistant_id) / "roster.json"
    if path.is_symlink() or (path.exists() and path.stat().st_size > MAX_SAVED_FILE):
        raise ValueError("学生名单文件不安全或过大")
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError):
        return []


def upsert_roster(assistant_id: str, student_no: str, name: str, class_name: str) -> None:
    rows = roster_rows(assistant_id)
    record = {"student_no": student_no, "name": name, "class_name": class_name}
    for index, row in enumerate(rows):
        if row.get("student_no") == student_no:
            rows[index] = record
            break
    else:
        rows.append(record)
    _write_json(private_root(assistant_id) / "roster.json", rows)


def student_dir(assistant_id: str, student_no: str) -> Path:
    if not re.fullmatch(r"(?:\d{5,20}|admin)", student_no):
        raise ValueError("学号格式无效")
    base = private_root(assistant_id) / "students"
    base.mkdir(mode=0o700, exist_ok=True)
    if base.is_symlink():
        raise ValueError("学生目录不能是符号链接")
    base.chmod(0o700)
    folder = base / student_no
    folder.mkdir(mode=0o700, exist_ok=True)
    if folder.is_symlink():
        raise ValueError("学生目录不能是符号链接")
    folder.chmod(0o700)
    return folder


def save_devices(assistant_id: str, student_no: str, rows: list[dict]) -> None:
    _write_json(student_dir(assistant_id, student_no) / "devices.json", rows)


def _thread_path(assistant_id: str, student_no: str, thread_id: str) -> Path:
    if not re.fullmatch(r"[a-f0-9]{32}", thread_id):
        raise ValueError("对话编号无效")
    folder = student_dir(assistant_id, student_no) / "threads"
    folder.mkdir(mode=0o700, exist_ok=True)
    if folder.is_symlink():
        raise ValueError("对话目录不能是符号链接")
    folder.chmod(0o700)
    return folder / f"{thread_id}.json"


def list_threads(assistant_id: str, student_no: str) -> list[dict]:
    folder = student_dir(assistant_id, student_no) / "threads"
    if not folder.is_dir():
        return []
    rows = []
    for path in folder.glob("*.json"):
        if path.is_symlink() or path.stat().st_size > MAX_SAVED_FILE:
            continue
        try:
            item = json.loads(path.read_text(encoding="utf-8"))
            rows.append({key: item[key] for key in ("id", "title", "updated_at")})
        except (KeyError, json.JSONDecodeError, OSError):
            continue
    return sorted(rows, key=lambda item: item["updated_at"], reverse=True)[:50]


def read_thread(assistant_id: str, student_no: str, thread_id: str) -> dict | None:
    path = _thread_path(assistant_id, student_no, thread_id)
    if path.is_symlink() or not path.is_file() or path.stat().st_size > MAX_SAVED_FILE:
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return None


def save_thread(assistant_id: str, student_no: str, thread_id: str, title: str, messages: list[dict]) -> dict:
    path = _thread_path(assistant_id, student_no, thread_id)
    old = read_thread(assistant_id, student_no, thread_id)
    now = datetime.now(timezone.utc).isoformat()
    data = {"id": thread_id, "title": title[:80], "created_at": old["created_at"] if old else now,
            "updated_at": now, "messages": messages}
    _write_json(path, data)
    return data
