"""Telegram notification service (FINAL STABLE VERSION)."""

import logging
import os
from typing import List, Dict, Any
import requests

logger = logging.getLogger(__name__)


class TelegramService:
    """Sends alerts and lead notifications to Telegram."""

    MAX_MESSAGE_LENGTH = 3500

    def __init__(self):
        self.bot_token = os.getenv("TELEGRAM_BOT_TOKEN", "")
        self.chat_id = os.getenv("TELEGRAM_CHAT_ID", "")
        self.enabled = bool(self.bot_token and self.chat_id)

        if self.enabled:
            logger.info("✅ Telegram service initialized")
        else:
            logger.warning(
                "❌ Telegram disabled. Missing TELEGRAM_BOT_TOKEN or TELEGRAM_CHAT_ID"
            )

    # ============================================================
    # SIMPLE MESSAGE (FOR DEBUG / TEST)
    # ============================================================
    def send_message(self, text: str) -> bool:
        return self._send_message(text)

    # ============================================================
    # SEND LEADS
    # ============================================================
    def send_leads(self, leads: List[Dict[str, Any]]) -> bool:
        if not leads:
            logger.warning("⚠ No leads to send")
            return False

        if not self.enabled:
            logger.warning("❌ Telegram disabled — skipping send")
            return False

        try:
            messages = self._format_messages(leads)

            for msg in messages:
                if not self._send_message(msg):
                    return False

            return True

        except Exception as e:
            logger.error(f"❌ Error sending leads: {str(e)}")
            return False

    # ============================================================
    # FORMAT MESSAGES
    # ============================================================
    def _format_messages(self, leads: List[Dict[str, Any]]) -> List[str]:
        messages = []
        current = "🔥 <b>GURGAON HIGH-VALUE LEADS</b>\n\n"

        for i, lead in enumerate(leads, start=1):
            block = self._format_lead(lead, i)

            if len(current) + len(block) > self.MAX_MESSAGE_LENGTH:
                messages.append(current)
                current = "🔥 <b>CONTINUED</b>\n\n" + block
            else:
                current += block

        current += "\n👉 <b>Action:</b> Call immediately"
        messages.append(current)

        return messages

    # ============================================================
    # FORMAT SINGLE LEAD
    # ============================================================
    def _format_lead(self, lead: Dict[str, Any], number: int) -> str:
        title = lead.get("title", "N/A")
        company = lead.get("company", "Not specified")
        value = lead.get("numeric_value", 0)
        url = lead.get("url", "")
        score = lead.get("score", 0)

        # Value formatting
        if value >= 100:
            value_str = f"₹{value/100:.1f} Cr"
        else:
            value_str = f"₹{value} L"

        phone = lead.get("phone", "")
        email = lead.get("email", "")

        contact = ""
        if phone:
            contact += f"📞 {phone}\n"
        if email:
            contact += f"✉️ {email}\n"

        return (
            f"<b>{number}. {title}</b>\n"
            f"💰 {value_str}\n"
            f"📍 Gurgaon\n"
            f"🏢 {company}\n"
            f"⭐ Score: {score}\n"
            f"{contact}"
            f"🔗 {url}\n\n"
        )

    # ============================================================
    # CORE SEND FUNCTION (FINAL)
    # ============================================================
    def _send_message(self, message: str) -> bool:
        if not self.enabled:
            logger.error("❌ Telegram not enabled")
            return False

        try:
            url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"

            payload = {
                "chat_id": self.chat_id,
                "text": message,
                "parse_mode": "HTML",
                "disable_web_page_preview": True
            }

            response = requests.post(url, json=payload, timeout=10)

            logger.info(f"📡 Telegram status: {response.status_code}")
            logger.info(f"📨 Response: {response.text}")

            if response.status_code == 200:
                logger.info("✅ Message sent to Telegram")
                return True
            else:
                logger.error("❌ Telegram API failed")
                return False

        except Exception as e:
            logger.error(f"❌ Telegram exception: {str(e)}")
            return False
