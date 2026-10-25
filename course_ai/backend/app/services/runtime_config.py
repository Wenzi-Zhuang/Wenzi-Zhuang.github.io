import json
import os
from dataclasses import dataclass
from pathlib import Path

from ..config import get_settings


@dataclass
class DeepSeekRuntimeConfig:
    api_key: str
    base_url: str
    model: str


def load_deepseek_config() -> DeepSeekRuntimeConfig:
    settings = get_settings()
    path = settings.runtime_config_root / "deepseek.json"
    if path.is_file():
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            if data.get("api_key"):
                model = data.get("model") or settings.deepseek_model
                if model == "deepseek-chat":
                    model = "deepseek-flash"
                return DeepSeekRuntimeConfig(
                    api_key=data["api_key"],
                    base_url=data.get("base_url") or settings.deepseek_base_url,
                    model=model,
                )
        except (OSError, ValueError, TypeError):
            pass
    model = "deepseek-flash" if settings.deepseek_model == "deepseek-chat" else settings.deepseek_model
    return DeepSeekRuntimeConfig(settings.deepseek_api_key, settings.deepseek_base_url, model)


def save_deepseek_config(api_key: str, base_url: str, model: str) -> None:
    root = get_settings().runtime_config_root
    root.mkdir(parents=True, exist_ok=True)
    destination = root / "deepseek.json"
    temporary = root / ".deepseek.json.tmp"
    temporary.write_text(json.dumps({"api_key": api_key, "base_url": base_url, "model": model}, ensure_ascii=False), encoding="utf-8")
    os.chmod(temporary, 0o600)
    temporary.replace(destination)

