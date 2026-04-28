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
                "Set TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID environment variables."
            )
    
    def send_leads(self, leads: List[Dict[str, Any]]) -> bool:
        """Send leads to Telegram."""
        if not leads:
            logger.info("No leads to send.")
            return True
        
        if not self.enabled:
            logger.info(f"Telegram disabled. Would send {len(leads)} leads:")
            for i, lead in enumerate(leads, 1):
                logger.info(f"  {i}. {lead.get('title', 'N/A')} (Score: {lead.get('score', 0)})")
            return False
        
        try:
            messages = self._format_messages(leads)
            
            for msg_index, message in enumerate(messages, 1):
                logger.debug(f"Sending message {msg_index}/{len(messages)} to Telegram...")
                success = self._send_message(message)
                if not success:
                    logger.error(f"Failed to send message {msg_index}")
                    return False
            
            return True
        
        except Exception as e:
            logger.error(f"Error sending leads to Telegram: {str(e)}")
            return False
    
    def _format_messages(self, leads: List[Dict[str, Any]]) -> List[str]:
        """Format leads into Telegram messages."""
        messages = []
        current_message = "🔥 *GURGAON HIGH-VALUE LEADS*\n\n"
        lead_counter = 1
        
        for lead in leads:
            formatted_lead = self._format_lead(lead, lead_counter)
            
            # Check if adding this lead would exceed message limit
            if len(current_message) + len(formatted_lead) > self.MAX_MESSAGE_LENGTH:
                # Save current message and start new one
                messages.append(current_message)
                current_message = f"🔥 *GURGAON HIGH-VALUE LEADS (continued)*\n\n{formatted_lead}"
            else:
                current_message += formatted_lead
            
            lead_counter += 1
        
        # Add final message
        if current_message.strip() != "🔥 *GURGAON HIGH-VALUE LEADS*":
            current_message += "\n👉 *Action:* Call immediately\n"
            messages.append(current_message)
        
        return messages
    
    def _format_lead(self, lead: Dict[str, Any], number: int) -> str:
        """Format individual lead for display."""
        title = lead.get("title", "N/A")
        company = lead.get("company", "Not specified")
        value = lead.get("numeric_value", 0)
        turnover = lead.get("turnover", "Unknown")
        risk = lead.get("risk", "Unknown")
        url = lead.get("url", "#")
        score = lead.get("score", 0)
        source = lead.get("source", "Unknown")
        
        # Format value nicely
        if value >= 100:
            value_str = f"₹{value/100:.1f} Cr"
        else:
            value_str = f"₹{value} L"
        
        # Contact information
        contact_info = ""
        if lead.get("contact_name") or lead.get("phone") or lead.get("email"):
            contact_info = "\n👤 *Contact:*\n"
            if lead.get("contact_name"):
                contact_info += f"    {lead.get('contact_name')}\n"
            if lead.get("phone"):
                contact_info += f"    📞 {lead.get('phone')}\n"
            if lead.get("email"):
                contact_info += f"    ✉️  {lead.get('email')}\n"
        
        # Business signals
        signals = ""
        if lead.get("gst_active") or lead.get("msme_signal"):
            signals = "\n🔍 "
            if lead.get("gst_active"):
                signals += "✓ GST Registered | "
            if lead.get("msme_signal"):
                signals += "✓ MSME Signal | "
            signals += f"Risk: {risk}"
        else:
            signals = f"\n🔍 Risk: {risk}"
        
        formatted = f"""{number}. {title}
📍 Gurgaon
💰 {value_str}
🏢 {company}
📊 Source: {source}
⭐ Score: {score}/25{contact_info}{signals}
🔗 [View Details]({url})
\n"""
        
        return formatted
    
    def _send_message(self, message: str) -> bool:
        """Send message via Telegram API."""
        if not self.enabled:
            logger.info("Telegram not configured. Skipping send.")
            return False
        
        try:
            import requests
            
            url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"
            payload = {
                "chat_id": self.chat_id,
                "text": message,
                "parse_mode": "Markdown",
            }
            
            response = requests.post(url, json=payload, timeout=10)
            
            if response.status_code == 200:
                logger.debug("Message sent successfully to Telegram")
                return True
            else:
                logger.error(
                    f"Telegram API error: {response.status_code} - {response.text}"
                )
                return False
        
        except Exception as e:
            logger.error(f"Error sending message to Telegram: {str(e)}")
            return False
