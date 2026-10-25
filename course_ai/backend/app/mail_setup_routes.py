"""Private, one-time DUFE IMAP setup page for the NAS worker."""

import asyncio
import secrets
import time
from collections import deque
from html import escape

from fastapi import APIRouter, Form, HTTPException
from fastapi.responses import HTMLResponse

from .config import get_settings
from .services.case_worker import retry_mail_after_configuration, wake_case_worker
from .services.mail_drafts import MailConfig, discover_drafts, save_mail_config, validate_mail_settings

router = APIRouter()
_attempts: deque[float] = deque()

PAGE = """<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="referrer" content="no-referrer"><title>DUFE 邮箱草稿配置</title><style>body{margin:0;background:#f3f7f4;color:#17211d;font:15px/1.7 system-ui,-apple-system,'PingFang SC',sans-serif}.box{box-sizing:border-box;width:min(500px,calc(100% - 32px));margin:7vh auto;padding:30px;background:#fff;border:1px solid #dfe7e2;border-radius:15px}h1{margin:0;font-size:24px}p{color:#65716b;font-size:13px}label{display:grid;gap:5px;margin:16px 0;color:#45564c;font-size:13px}input{box-sizing:border-box;width:100%;min-height:43px;padding:9px 11px;border:1px solid #cbd8d1;border-radius:7px;font:inherit}button{width:100%;min-height:44px;margin-top:10px;color:#fff;font-weight:700;background:#176b52;border:0;border-radius:7px}.error{color:#a43a36}.ok{color:#176b52}</style></head><body><main class="box"><h1>DUFE 邮箱草稿配置</h1><p>学生论文由 NAS 后端处理，初审意见只保存到你的 DUFE 草稿箱，绝不自动发送。请使用邮箱“客户端专用密码”，不要使用网页登录密码；凭据仅保存在 NAS 私有配置目录。</p><p class="error" role="alert">{{message}}</p><form method="post" action="/setup/mail" autocomplete="off"><label>NAS 设置码<input name="setup_code" type="password" required autocomplete="off"></label><label>你的 DUFE 邮箱地址<input name="address" type="email" required autocomplete="off" placeholder="name@dufe.edu.cn"></label><label>IMAP 主机<input name="host" required value="mail.dufe.edu.cn"></label><label>客户端专用密码<input name="app_password" type="password" required autocomplete="off"></label><button type="submit">验证连接并保存</button></form><p>NAS 会先验证加密 IMAP 连接并识别草稿箱，不会创建测试邮件。成功后自动处理等待中的初审草稿。配置不需要你的电脑持续开机。</p></main></body></html>"""


def _page(message: str = "", status_code: int = 200) -> HTMLResponse:
    response = HTMLResponse(PAGE.replace("{{message}}", escape(message)), status_code=status_code)
    response.headers["Cache-Control"] = "no-store"
    response.headers["Referrer-Policy"] = "no-referrer"
    response.headers["X-Frame-Options"] = "DENY"
    return response


@router.get("/setup/mail", response_class=HTMLResponse)
async def mail_setup_page():
    return _page()


@router.post("/setup/mail", response_class=HTMLResponse)
async def mail_setup_save(setup_code: str = Form(...), address: str = Form(...),
                          host: str = Form("mail.dufe.edu.cn"), app_password: str = Form(...)):
    now = time.monotonic()
    while _attempts and _attempts[0] <= now - 3600:
        _attempts.popleft()
    if len(_attempts) >= 8:
        raise HTTPException(429, "设置尝试过多，请一小时后重试")
    _attempts.append(now)
    cfg = get_settings()
    if cfg.setup_code == "CHANGE_ME" or not secrets.compare_digest(setup_code, cfg.setup_code):
        return _page("NAS 设置码不正确。", 403)
    address, host = address.strip().lower(), host.strip().lower()
    try:
        validate_mail_settings(address, host, app_password)
        folder = await asyncio.to_thread(discover_drafts, address, host, app_password)
        save_mail_config(MailConfig(address, host, app_password, folder))
    except ValueError as exc:
        return _page(str(exc), 400)
    except Exception:
        return _page("无法连接学校邮箱或识别草稿箱；请核对 IMAP 主机及客户端专用密码。", 503)
    retry_mail_after_configuration()
    wake_case_worker()
    response = HTMLResponse("<meta charset='utf-8'><main style='font:16px/1.8 system-ui;max-width:500px;margin:8vh auto'><h1>DUFE 草稿连接已保存</h1><p>NAS 将独立处理已提交论文与待同步草稿；不会自动发送邮件。</p></main>")
    response.headers["Cache-Control"] = "no-store"
    return response
