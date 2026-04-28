import requests
import os
import logging

logger = logging.getLogger(__name__)

WEBHOOK_URL = os.getenv("GOOGLE_SHEET_WEBHOOK_URL")


def send_to_sheet(lead: dict):
    """Send lead data to Google Sheet via webhook"""

    if not WEBHOOK_URL:
        logger.warning("⚠️ GOOGLE_SHEET_WEBHOOK_URL not set")
        return

    payload = {
        "id": lead.get("id"),
        "title": lead.get("title"),
        "company": lead.get("company", ""),
        "numeric_value": lead.get("numeric_value", ""),  # ✅ fixed
        "location": lead.get("location", ""),
        "score": lead.get("score", 0),
        "lead_type": lead.get("lead_type", ""),          # ✅ NEW
        "phone": lead.get("phone", ""),
        "email": lead.get("email", ""),
        "url": lead.get("url", "")                       # ✅ NEW
    }

    try:
        response = requests.post(WEBHOOK_URL, json=payload, timeout=10)

        if response.status_code == 200:
            logger.info("✅ Sent to Google Sheet")
        else:
            logger.error(f"❌ Sheet error: {response.text}")

    except Exception as e:
        logger.error(f"❌ Webhook error: {e}")
