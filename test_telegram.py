import requests


CHAT_ID = "8622521669"


def send_test_notification() -> None:
    bot_token = input("Enter your Telegram bot token: ").strip()

    if not bot_token:
        print("ERROR: No bot token was entered.")
        return

    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"

    message = (
        "✅ TSX MOMENTUM SYSTEM\n\n"
        "Telegram notifications are connected successfully.\n\n"
        "This is a test message from the trading workstation."
    )

    payload = {
        "chat_id": CHAT_ID,
        "text": message,
    }

    try:
        response = requests.post(url, json=payload, timeout=15)
        response.raise_for_status()

        data = response.json()

        if data.get("ok"):
            print("SUCCESS: Test notification sent.")
        else:
            print("ERROR: Telegram rejected the message.")
            print(data)

    except requests.RequestException as error:
        print(f"CONNECTION ERROR: {error}")
    except ValueError as error:
        print(f"INVALID RESPONSE: {error}")


if __name__ == "__main__":
    send_test_notification()