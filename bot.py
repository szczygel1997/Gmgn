import os
import time
import requests

GMGN_API_KEY = os.environ["GMGN_API_KEY"]
TELEGRAM_BOT_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
TELEGRAM_CHAT_ID = os.environ["TELEGRAM_CHAT_ID"]

CHAIN = "robinhood"

LIQUIDITY_MIN = 25_000
VOLUME_MIN = 100_000
HOLDERS_MIN = 200
TOP_HOLDERS_MAX = 0.30

seen = set()

BASE_URL = "https://gmgn.ai/api/v1"

HEADERS = {
    "Authorization": f"Bearer {GMGN_API_KEY}",
    "Content-Type": "application/json",
}


def gmgn_get(endpoint, params):
    response = requests.get(
        BASE_URL + endpoint,
        headers=HEADERS,
        params=params,
        timeout=20
    )
    response.raise_for_status()
    return response.json()


def get_tokens():
    data = gmgn_get(
        "/market/rank",
        {
            "chain": CHAIN,
            "orderby": "volume",
            "direction": "desc",
            "limit": 100,
        }
    )

    return data.get("data", {}).get("rank", [])


def get_top_holders_percentage(address):
    data = gmgn_get(
        "/market/token_top_holders",
        {
            "chain": CHAIN,
            "address": address,
            "limit": 10,
            "order_by": "amount_percentage",
            "direction": "desc",
        }
    )

    holders = data.get("data", {}).get("list", [])

    total = 0

    for holder in holders:
        percentage = float(holder.get("amount_percentage", 0) or 0)
        total += percentage

    return total


def send_telegram(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"

    response = requests.post(
        url,
        json={
            "chat_id": TELEGRAM_CHAT_ID,
            "text": message,
            "disable_web_page_preview": True,
        },
        timeout=20,
    )

    response.raise_for_status()


def check_token(token):
    liquidity = float(token.get("liquidity", 0) or 0)
    volume = float(token.get("volume", 0) or 0)
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
        tokens = get_tokens()

        print(f"Sprawdzam {len(tokens)} tokenów...")

        for token in tokens:
            address = token.get("address")

            if not address or address in seen:
                continue

            if not check_token(token):
                continue

            top_holders = get_top_holders_percentage(address)

            print(
                f"{token.get('symbol', 'UNKNOWN')} "
                f"| Top holders: {top_holders * 100:.1f}%"
            )

            if top_holders > TOP_HOLDERS_MAX:
                continue

            symbol = token.get("symbol", "UNKNOWN")
            liquidity = float(token.get("liquidity", 0) or 0)
            volume = float(token.get("volume", 0) or 0)
            holders = int(token.get("holder_count", 0) or 0)

            message = (
                "🚨 GMGN ROBINHOOD ALERT\n\n"
                f"🪙 {symbol}\n"
                f"💧 Liquidity: ${liquidity:,.0f}\n"
                f"📊 Volume: ${volume:,.0f}\n"
                f"👥 Holders: {holders}\n"
                f"🐋 Top 10 holders: {top_holders * 100:.1f}%\n\n"
                f"CA:\n{address}"
            )

            send_telegram(message)

            seen.add(address)

            print(f"✅ ALERT WYSŁANY: {symbol}")

        time.sleep(60)

    except Exception as e:
        print("ERROR:", e)
        time.sleep(60)
