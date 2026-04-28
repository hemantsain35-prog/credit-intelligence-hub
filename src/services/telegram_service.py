"""Telegram notification service."""

import logging
import os
from typing import List, Dict, Any

logger = logging.getLogger(__name__)


class TelegramService:
    """Sends lead alerts to Telegram."""
    
    MAX_MESSAGE_LENGTH = 3500
    
    def __init__(self):
        """Initialize Telegram service."""
        self.bot_token = os.getenv("TELEGRAM_BOT_TOKEN", "")
        self.chat_id = os.getenv("TELEGRAM_CHAT_ID", "")
        self.enabled = bool(self.bot_token and self.chat_id)
        
        if not self.enabled:
            logger.warning(
                "Telegram credentials not configured. "
                "Set TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID."
            )
    
    def send_leads(self, leads: List[Dict[str, Any]]) -> bool:
        """Send leads to Telegram."""
        if not leads:
            logger.info("No leads to send.")
            return True
        
        if not self.enabled:
            logger.info(f"Telegram disabled. Would send {len(leads)} leads.")
            return False
        
        try:
            messages = self._format_messages(leads)
            
            for message in messages:
                success = self._send_message(message)
                if not success:
                    return False
            
            return True
        
        except Exception as e:
            logger.error(f"Error sending leads to Telegram: {str(e)}")
            return False
    
    def _format_messages(self, leads: List[Dict[str, Any]]) -> List[str]:
        """Format leads into Telegram messages."""
        messages = []
        current_message = "🔥 GURGAON HIGH-VALUE LEADS\n\n"
        lead_counter = 1
        
        for lead in leads:
            formatted_lead = self._format_lead(lead, lead_counter)
            
            if len(current_message) + len(formatted_lead) > self.MAX_MESSAGE_LENGTH:
                messages.append(current_message)
                current_message = "🔥 GURGAON HIGH-VALUE LEADS (continued)\n\n" + formatted_lead
            else:
                current_message += formatted_lead
            
            lead_counter += 1
        
        if current_message.strip():
            current_message += "\n👉 Action: Call immediately\n"
            messages.append(current_message)
        
        return messages
    
    def _format_lead(self, lead: Dict[str, Any], number: int) -> str:
        """Format individual lead."""
        title = lead.get("title", "N/A")
        company = lead.get("company", "Not specified")
        value = lead.get("numeric_value", 0)
        url = lead.get("url", "")
        score = lead.get("score", 0)
        
        # Value format
        if value >= 100:
            value_str = f"₹{value/100:.1f} Cr"
        else:
            value_str = f"₹{value} L"
        
        phone = lead.get("phone", "")
        email = lead.get("email", "")
        
        contact = ""
        if phone or email:
            contact = "\n"
            if phone:
                contact += f"📞 {phone}\n"
            if email:
                contact += f"✉️ {email}\n"
        
        return (
            f"{number}. {title}\n"
            f"💰 {value_str}\n"
            f"📍 Gurgaon\n"
            f"🏢 {company}\n"
            f"⭐ Score: {score}\n"
            f"{contact}"
            f"🔗 {url}\n\n"
        )
    
    def _send_message(self, message: str) -> bool:
        """Send message via Telegram API."""
        if not self.enabled:
            return False
        
        try:
            import requests
            
            url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"
            
            payload = {
                "chat_id": self.chat_id,
                "text": message
            }
            
            # ✅ FIXED: using data instead of json
            response = requests.post(url, data=payload, timeout=10)
            
            if response.status_code == 200:
                logger.info("✅ Telegram message sent")
                return True
            else:
                logger.error(f"Telegram API error: {response.text}")
                return False
        
        except Exception as e:
            logger.error(f"Telegram send error: {str(e)}")
            return False
