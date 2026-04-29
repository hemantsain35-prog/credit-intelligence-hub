import requests
import os

WEBHOOK_URL = os.getenv("GOOGLE_SHEET_WEBHOOK_URL")


def send_to_sheet(lead: dict):
    if not WEBHOOK_URL:
        return

    payload = {
        "id": lead.get("id"),
        "title": lead.get("title"),
        "company": lead.get("company", lead.get("title")),
        "location": lead.get("location", ""),
        "phone": lead.get("phone", ""),
        "email": lead.get("email", "")
    }

    try:
        requests.post(WEBHOOK_URL, json=payload, timeout=10)
    except Exception as e:
        print("Sheet error:", e)
