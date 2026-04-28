"""Contact information extraction utilities."""

import logging
import re
from typing import Dict, Any

logger = logging.getLogger(__name__)


class ContactExtractor:
    """Extracts phone, email, and name from text."""
    
    # Phone patterns (India-focused)
    PHONE_PATTERNS = [
        r'\+91[\-\s]?[6-9]\d{9}',          # +91-9876543210
        r'[6-9]\d{9}',                       # 9876543210
        r'[6-9]\d{4}\s?[\-\s]?\d{6}',      # 9876 432101
        r'\([6-9]\d{4}\)\s?\d{6}',        # (9876) 432101
        r'0\d{2,4}\s?[\-\s]?\d{3,4}\s?[\-\s]?\d{4}',  # 011-2345-6789
    ]
    
    # Email pattern
    EMAIL_PATTERN = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    
    # Name patterns (capitalized words)
    NAME_PATTERN = r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b'
    
    def extract(self, text: str) -> Dict[str, Any]:
        """Extract contact information from text."""
        if not text:
            return {
                "contact_name": "",
                "phone": "",
                "email": "",
            }
        
        phone = self._extract_phone(text)
        email = self._extract_email(text)
        contact_name = self._extract_name(text)
        
        return {
            "contact_name": contact_name,
            "phone": phone,
            "email": email,
        }
    
    def _extract_phone(self, text: str) -> str:
        """Extract phone number from text."""
        for pattern in self.PHONE_PATTERNS:
            match = re.search(pattern, text)
            if match:
                phone = match.group(0)
                # Normalize phone (remove spaces and dashes)
                phone = re.sub(r'[\-\s()]', '', phone)
                # Ensure it's a valid length
                if len(phone) >= 10:
                    return phone
        
        return ""
    
    def _extract_email(self, text: str) -> str:
        """Extract email from text."""
        match = re.search(self.EMAIL_PATTERN, text)
        if match:
            return match.group(0)
        return ""
    
    def _extract_name(self, text: str) -> str:
        """Extract name from text."""
        # Look for "Contact:" or "Name:" patterns
        contact_patterns = [
            r'(?:Contact|Name|Contact Name|Mr\.|Ms\.|Mrs\.)[:\s]+([A-Z][a-zA-Z\s]+)',
            r'(?:By|From)[:\s]+([A-Z][a-zA-Z\s]+)',
        ]
        
        for pattern in contact_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                name = match.group(1).strip()
                if name and len(name) > 2:
                    return name
        
        # Fallback: extract first capitalized word sequence
        matches = re.findall(self.NAME_PATTERN, text)
        if matches:
            # Return first meaningful name (not in common words)
            common_words = {'and', 'the', 'for', 'with', 'from', 'to', 'at', 'by', 'on', 'in'}
            for match in matches:
                if match.lower() not in common_words and len(match) > 2:
                    return match
        
        return ""
