"""Append review messages to the teacher's DUFE IMAP Drafts, never send them."""

import imaplib
import json
import os
import re
import ssl
import uuid
from dataclasses import dataclass
from email.message import EmailMessage
from email.policy import SMTP
from pathlib import Path

from ..config import get_settings


@dataclass
class MailConfig:
    address: str
    host: str
    app_password: str
    draft_folder: str


def _config_path() -> Path:
    return get_settings().runtime_config_root / "dufe_mail.json"


def load_mail_config() -> MailConfig | None:
    path = _config_path()
    if not path.is_file() or path.is_symlink():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return MailConfig(data["address"], data["host"], data["app_password"], data["draft_folder"])
    except (OSError, KeyError, ValueError, TypeError):
        return None


def validate_mail_settings(address: str, host: str, app_password: str) -> None:
    if not re.fullmatch(r"[A-Za-z0-9_.+\-]+@(?:[A-Za-z0-9\-]+\.)?dufe\.edu\.cn", address):
        raise ValueError("邮箱地址须为 DUFE 学校邮箱")
    if host != "mail.dufe.edu.cn" and not re.fullmatch(r"[A-Za-z0-9-]+\.dufe\.edu\.cn", host):
        raise ValueError("IMAP 主机须为 DUFE 学校域名")
    if not app_password or len(app_password) > 256:
        raise ValueError("请输入有效的客户端专用密码")


def _folder_name(raw: bytes) -> tuple[str, str]:
    line = raw.decode("ascii", errors="replace")
    flags = line.split(")", 1)[0].lower()
    match = re.search(r'"([^"]+)"\s*$|\s([^\s]+)\s*$', line)
    if not match:
        return flags, ""
    return flags, match.group(1) or match.group(2)


def _connect(config: MailConfig):
    client = imaplib.IMAP4_SSL(config.host, 993, ssl_context=ssl.create_default_context(), timeout=15)
    try:
        client.login(config.address, config.app_password)
        return client
    except Exception:
        client.logout()
        raise


def discover_drafts(address: str, host: str, app_password: str) -> str:
    validate_mail_settings(address, host, app_password)
    client = _connect(MailConfig(address, host, app_password, ""))
    try:
        status, rows = client.list()
        if status != "OK" or not rows:
            raise RuntimeError("无法读取邮箱文件夹")
        names = [_folder_name(row) for row in rows if row]
        candidates = [name for flags, name in names if r"\drafts" in flags]
        candidates += [name for _, name in names if name.lower().strip('"') in {"draft", "drafts"}]
        if not candidates:
            raise RuntimeError("未能识别草稿箱，请检查邮箱 IMAP 设置")
        return candidates[0]
    finally:
        try:
            client.logout()
        except Exception:
            pass


def save_mail_config(config: MailConfig) -> None:
    validate_mail_settings(config.address, config.host, config.app_password)
    root = get_settings().runtime_config_root
    root.mkdir(mode=0o700, parents=True, exist_ok=True)
    if root.is_symlink():
        raise ValueError("私有配置目录不能是符号链接")
    root.chmod(0o700)
    target = _config_path()
    if target.is_symlink():
        raise ValueError("邮箱配置文件不能是符号链接")
    temporary = root / (".dufe_mail_" + uuid.uuid4().hex + ".tmp")
    try:
        with temporary.open("x", encoding="utf-8") as handle:
            json.dump(config.__dict__, handle, ensure_ascii=False)
        temporary.chmod(0o600)
        os.replace(temporary, target)
    finally:
        temporary.unlink(missing_ok=True)


def append_review_draft(config: MailConfig, submission_id: str, subject: str,
                        recipient: str | None, body: str) -> None:
    """Use a deterministic Message-ID so restart/retry does not duplicate a draft."""
    if not re.fullmatch(r"[a-f0-9]{32}", submission_id):
        raise ValueError("提交编号无效")
    message_id = f"<course-ai-{submission_id}@dufe.edu.cn>"
    message = EmailMessage(policy=SMTP)
    message["Message-ID"] = message_id
    message["From"] = config.address
    if recipient:
        message["To"] = recipient
    message["Subject"] = subject
    message.set_content(body)
    client = _connect(config)
    try:
        status, _ = client.select(config.draft_folder, readonly=True)
        if status != "OK":
            raise RuntimeError("无法打开邮箱草稿箱")
        status, existing = client.search(None, "HEADER", "Message-ID", f'"{message_id}"')
        if status != "OK":
            raise RuntimeError("无法核查邮箱草稿，已停止以避免重复")
        if existing and existing[0].strip():
            return
        status, _ = client.append(config.draft_folder, "(\\Draft)", None, message.as_bytes())
        if status != "OK":
            raise RuntimeError("保存到邮箱草稿箱失败")
    finally:
        try:
            client.logout()
        except Exception:
            pass
