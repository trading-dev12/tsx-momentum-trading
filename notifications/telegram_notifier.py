import os
from pathlib import Path

import requests


PROJECT_ROOT = Path(__file__).resolve().parent.parent
ENV_FILE = PROJECT_ROOT / ".env"


def _load_env_file() -> None:
    if not ENV_FILE.exists():
        return

    for line in ENV_FILE.read_text(encoding="utf-8").splitlines():
        line = line.strip()

        if not line or line.startswith("#") or "=" not in line:
            continue

        key, value = line.split("=", 1)

        key = key.strip()
        value = value.strip()

        if key and key not in os.environ:
            os.environ[key] = value


def send_telegram_message(message: str) -> dict:
    _load_env_file()

    bot_token = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
    chat_id = os.getenv("TELEGRAM_CHAT_ID", "").strip()

    if not bot_token:
        return {
            "success": False,
            "message": "TELEGRAM_BOT_TOKEN is missing.",
        }

    if not chat_id:
        return {
            "success": False,
            "message": "TELEGRAM_CHAT_ID is missing.",
        }

    if not message or not message.strip():
        return {
            "success": False,
            "message": "Notification message is empty.",
        }

    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"

    payload = {
        "chat_id": chat_id,
        "text": message.strip(),
    }

    try:
        response = requests.post(
            url,
            json=payload,
            timeout=15,
        )

        response.raise_for_status()
        data = response.json()

        if not data.get("ok"):
            return {
                "success": False,
                "message": "Telegram rejected the message.",
            }

        return {
            "success": True,
            "message": "Telegram notification sent.",
        }

    except requests.RequestException as error:
        return {
            "success": False,
            "message": f"Telegram connection error: {error}",
        }

    except ValueError as error:
        return {
            "success": False,
            "message": f"Invalid Telegram response: {error}",
        }