import argparse
import getpass
import os
from pathlib import Path


def update_env(path: Path, values: dict[str, str]) -> None:
    lines = path.read_text(encoding="utf-8").splitlines() if path.exists() else []
    output = []
    remaining = dict(values)
    for line in lines:
        key = line.split("=", 1)[0].strip() if "=" in line and not line.lstrip().startswith("#") else None
        if key in remaining:
            output.append(f"{key}={remaining.pop(key)}")
        else:
            output.append(line)
    output.extend(f"{key}={value}" for key, value in remaining.items())
    path.write_text("\n".join(output) + "\n", encoding="utf-8")
    os.chmod(path, 0o600)


def main() -> None:
    parser = argparse.ArgumentParser(description="在 NAS 本地安全配置 DeepSeek API")
    parser.add_argument("--env", default=".env", help=".env 路径，默认当前目录/.env")
    args = parser.parse_args()
    key = getpass.getpass("请输入 DeepSeek API Key（输入不会显示）: ").strip()
    if not key or key == "CHANGE_ME":
        raise SystemExit("未输入有效 API Key，配置未更改。")
    base_url = input("DeepSeek Base URL [https://api.deepseek.com]: ").strip() or "https://api.deepseek.com"
    model = input("模型 [deepseek-chat]: ").strip() or "deepseek-chat"
    update_env(Path(args.env), {
        "DEEPSEEK_API_KEY": key,
        "DEEPSEEK_BASE_URL": base_url,
        "DEEPSEEK_MODEL": model,
    })
    print(f"配置已安全写入 {args.env}。请运行：docker compose up -d --build")


if __name__ == "__main__":
    main()
