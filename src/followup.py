import requests
import os


SHEET_URL = os.getenv("GOOGLE_SHEET_WEBHOOK_URL")
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")


def get_followups():
    try:
        res = requests.get(SHEET_URL)
        return res.json()
    except:
        return []


def send_message(text):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"

    payload = {
        "chat_id": CHAT_ID,
        "text": text,
        "parse_mode": "HTML"
    }

    requests.post(url, json=payload)


def run_followup():
    data = get_followups()

    if not data:
        return

    pending = [
        x for x in data
        if x.get("status") in ["NEW", "FOLLOW-UP"]
    ]

    if not pending:
        send_message("✅ No follow-ups pending")
        return

    msg = "📞 <b>FOLLOW-UP SHEET REMINDER</b>\n\n"

    for i, lead in enumerate(pending[:10], start=1):
        msg += (
            f"{i}. <b>{lead.get('title')}</b>\n"
            f"📞 {lead.get('phone')}\n"
            f"Status: {lead.get('status')}\n\n"
        )

    msg += "👉 Update Sheet 2"

    send_message(msg)


if __name__ == "__main__":
    run_followup()
