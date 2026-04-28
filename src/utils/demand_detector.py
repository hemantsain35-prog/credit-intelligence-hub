"""Demand detection and value extraction."""

import logging
import re
from typing import Dict, Any

logger = logging.getLogger(__name__)


class DemandDetector:
    """Detects demand signals and extracts monetary values."""
    
    # Keywords indicating demand/need
    DEMAND_KEYWORDS = {
        "need", "require", "requirement", "supplier", "vendor",
        "wanted", "seek", "looking", "search", "purchase",
        "procurement", "tender", "bid", "request", "inquiry",
        "demand", "buyer", "looking for", "in need", "urgent need",
        "bulk order", "contract", "buyer requirement", "vendor requirement",
        "buying", "sourcing", "interested", "required", "requirement",
    }
    
    # Keywords indicating urgency
    URGENCY_KEYWORDS = {
        "urgent", "immediate", "asap", "quickly", "rush",
        "priority", "fast", "time-sensitive", "bulk", "project",
        "time bound", "on urgent basis", "immediately required",
    }
    
    def analyze(self, item: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze item for demand and extract value."""
        title = item.get("title", "").lower()
        description = item.get("description", "").lower()
        combined_text = f"{title} {description}"
        
        # Check for demand keywords
        has_demand = self._has_demand_keywords(combined_text)
        
        # Check for urgency
        has_urgency = self._has_urgency_keywords(combined_text)
        
        # Extract monetary value
        numeric_value = self._extract_value(combined_text)
        
        return {
            "is_demand": has_demand,
            "has_urgency": has_urgency,
            "numeric_value": numeric_value,
            "raw_value": self._extract_raw_value(combined_text),
        }
    
    def _has_demand_keywords(self, text: str) -> bool:
        """Check if text contains demand keywords."""
        for keyword in self.DEMAND_KEYWORDS:
            if keyword in text:
                return True
        return False
    
    def _has_urgency_keywords(self, text: str) -> bool:
        """Check if text contains urgency keywords."""
        for keyword in self.URGENCY_KEYWORDS:
            if keyword in text:
                return True
        return False
    
    def _extract_raw_value(self, text: str) -> str:
        """Extract raw value string from text."""
        # Match patterns like "50 lakh", "3 crore", "₹100L", etc.
        patterns = [
            r'₹\s*([0-9.]+)\s*(cr|crore|l|lakh)?',
            r'([0-9.]+)\s*(crore|cr|lakh|l)\b',
            r'rupees?\s*([0-9.]+)\s*(cr|crore|l|lakh)?',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(0)
        
        return ""
    
    def _extract_value(self, text: str) -> int:
        """Extract numeric value in lakhs from text."""
        raw_value = self._extract_raw_value(text)
        
        if not raw_value:
            return 0
        
        try:
            # Remove special characters
            cleaned = raw_value.replace("₹", "").replace(",", "").strip()
            cleaned = re.sub(r'[a-zA-Z\s]+', '', cleaned)  # Remove letters
            
            if not cleaned:
                return 0
            
            # Extract number
            number = float(cleaned)
            
            # Check unit (crore or lakh)
            if "cr" in raw_value.lower() or "crore" in raw_value.lower():
                # Convert crore to lakh (1 Cr = 100 Lakh)
                return int(number * 100)
            else:
                # Already in lakh
                return int(number)
        
        except Exception as e:
            logger.debug(f"Error extracting value from '{raw_value}': {str(e)}")
            return 0
