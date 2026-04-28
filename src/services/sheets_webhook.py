import requests
import os

WEBHOOK_URL = os.getenv("GOOGLE_SHEET_WEBHOOK_URL")


def send_to_sheet(lead: dict):
    """
    Send lead data to Google Sheet via Apps Script webhook
    """
    if not WEBHOOK_URL:
        print("⚠️ GOOGLE_SHEET_WEBHOOK_URL not set")
        return

    payload = {
        "id": lead.get("id"),
        "title": lead.get("title"),
        "company": lead.get("company", ""),
        "value": lead.get("value", ""),
        "location": lead.get("location", ""),
        "phone": lead.get("phone", ""),
        "email": lead.get("email", ""),
        "score": lead.get("score", 0),
    }

    try:
        requests.post(WEBHOOK_URL, json=payload, timeout=10)
    except Exception as e:
        print(f"Sheet webhook error: {e}")
