from __future__ import annotations

import os
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
ENV_PATH = ROOT / ".env"


def load_env_file(env_path: Path = ENV_PATH) -> None:
    if not env_path.exists():
        return

    for raw_line in env_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key and key not in os.environ:
            os.environ[key] = value


def read_env_values(env_path: Path = ENV_PATH) -> dict[str, str]:
    values: dict[str, str] = {}
    if not env_path.exists():
        return values

    for raw_line in env_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        values[key.strip()] = value.strip().strip('"').strip("'")
    return values


def write_env_values(updates: dict[str, str], env_path: Path = ENV_PATH) -> None:
    current = read_env_values(env_path)
    current.update(updates)

    ordered_keys = [
        "OPENAI_API_KEY",
        "OPENAI_MODEL",
        "META_ACCESS_TOKEN",
        "META_AD_ACCOUNT_ID",
        "GOOGLE_ADS_DEVELOPER_TOKEN",
        "GOOGLE_ADS_CLIENT_ID",
        "GOOGLE_ADS_CLIENT_SECRET",
        "GOOGLE_ADS_REFRESH_TOKEN",
        "GOOGLE_ADS_LOGIN_CUSTOMER_ID",
        "GOOGLE_ADS_CUSTOMER_ID",
    ]

    sections = [
        ("# OpenAI", ["OPENAI_API_KEY", "OPENAI_MODEL"]),
        ("# Meta Marketing API", ["META_ACCESS_TOKEN", "META_AD_ACCOUNT_ID"]),
        (
            "# Google Ads API",
            [
                "GOOGLE_ADS_DEVELOPER_TOKEN",
                "GOOGLE_ADS_CLIENT_ID",
                "GOOGLE_ADS_CLIENT_SECRET",
                "GOOGLE_ADS_REFRESH_TOKEN",
                "GOOGLE_ADS_LOGIN_CUSTOMER_ID",
                "GOOGLE_ADS_CUSTOMER_ID",
            ],
        ),
    ]

    lines: list[str] = []
    for title, keys in sections:
        lines.append(title)
        for key in keys:
            value = current.get(key, "")
            lines.append(f"{key}={value}")
            if value:
                os.environ[key] = value
        lines.append("")

    remaining_keys = [key for key in current if key not in ordered_keys]
    if remaining_keys:
        lines.append("# Outros")
        for key in sorted(remaining_keys):
            value = current.get(key, "")
            lines.append(f"{key}={value}")
            if value:
                os.environ[key] = value
        lines.append("")

    env_path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")
