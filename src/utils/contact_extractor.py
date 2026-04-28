"""Extract contact information from lead text."""

import logging
import re
from typing import Dict, Any

logger = logging.getLogger(__name__)


class ContactExtractor:
    """Extracts phone, email, and contact name from text."""
    
    # Indian phone number patterns
    PHONE_PATTERNS = [
        r'(?:\+91[\-\s]?)?[6-9]\d{9}',  # 10-digit mobile
        r'(?:\+91[\-\s]?)?[2-9]\d{9}(?:\-\d{4})?',  # Landline with optional extension
    ]
    
    # Email patterns
    EMAIL_PATTERN = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    
    # Name patterns (capitalized words)
    NAME_PATTERN = r'(?:Contact|Name|M/s|Mr|Ms|Mrs)\s*[:\.\s]+([A-Z][A-Za-z\s]+)'
    
    def extract(self, item: Dict[str, Any]) -> Dict[str, str]:
        """Extract contact details from item."""
        title = item.get("title", "")
        description = item.get("description", "")
        combined = f"{title} {description}"
        
        phone = self._extract_phone(combined)
        email = self._extract_email(combined)
        contact_name = self._extract_name(combined)
        
        return {
            "phone": phone,
            "email": email,
            "contact_name": contact_name,
        }
    
    def _extract_phone(self, text: str) -> str:
        """Extract phone number from text."""
        if not text:
            return ""
        
        for pattern in self.PHONE_PATTERNS:
            match = re.search(pattern, text)
            if match:
                phone = match.group(0)
                # Normalize: remove spaces and hyphens
                phone = re.sub(r'[\s\-]', '', phone)
                # Ensure it starts with country code or digits
                if len(phone) >= 10:
                    return phone
        
        return ""
    
    def _extract_email(self, text: str) -> str:
        """Extract email address from text."""
        if not text:
            return ""
        
        match = re.search(self.EMAIL_PATTERN, text)
        if match:
            return match.group(0).lower()
        
        return ""
    
    def _extract_name(self, text: str) -> str:
        """Extract contact name from text."""
        if not text:
            return ""
        
        # Try pattern matching first
        match = re.search(self.NAME_PATTERN, text, re.IGNORECASE)
        if match:
            return match.group(1).strip()
        
        # Fallback: get first capitalized phrase
        words = text.split()
        for i, word in enumerate(words):
            if word and word[0].isupper() and len(word) > 2:
                # Collect capitalized sequence
                name_parts = [word]
                for j in range(i + 1, min(i + 3, len(words))):
                    if words[j] and words[j][0].isupper():
                        name_parts.append(words[j])
                    else:
                        break
                return " ".join(name_parts)
        
        return ""
