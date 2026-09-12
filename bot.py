import os
import time
import requests

GMGN_API_KEY = os.environ["GMGN_API_KEY"]
TELEGRAM_BOT_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
TELEGRAM_CHAT_ID = os.environ["TELEGRAM_CHAT_ID"]

LIQUIDITY_MIN = 25_000
VOLUME_MIN = 100_000
HOLDERS_MIN = 200
TOP_HOLDERS_MAX = 30

seen = set()


def get_tokens():
    url = "https://gmgn.ai/api/v1/market/rank"
    headers = {
        "Authorization": f"Bearer {GMGN_API_KEY}"
    }

    params = {
        "chain": "sol",
        "orderby": "volume_24h",
        "direction": "desc",
        "limit": 100
    }

    r = requests.get(url, headers=headers, params=params, timeout=20)
    r.raise_for_status()
    return r.json()


def send_telegram(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"

    requests.post(
        url,
        json={
            "chat_id": TELEGRAM_CHAT_ID,
            "text": message,
            "disable_web_page_preview": True
        },
        timeout=20
    )


def check_token(token):
    liquidity = float(token.get("liquidity", 0) or 0)
    volume = float(token.get("volume_24h", 0) or 0)
    holders = int(token.get("holder_count", 0) or 0)

    if liquidity < LIQUIDITY_MIN:
        return False

    if volume < VOLUME_MIN:
        return False

    if holders < HOLDERS_MIN:
        return False

    return True


while True:
    try:
        data = get_tokens()

        tokens = data.get("data", [])

        for token in tokens:
            address = token.get("address")

            if not address or address in seen:
                continue

            if check_token(token):
                name = token.get("symbol", "UNKNOWN")
                liquidity = token.get("liquidity", 0)
                volume = token.get("volume_24h", 0)
                holders = token.get("holder_count", 0)

                message = (
                    f"🚨 GMGN ALERT\n\n"
                    f"🪙 {name}\n"
                    f"💧 Liquidity: ${liquidity:,.0f}\n"
                    f"📊 Volume 24h: ${volume:,.0f}\n"
                    f"👥 Holders: {holders}\n\n"
                    f"CA:\n{address}"
                )

                send_telegram
