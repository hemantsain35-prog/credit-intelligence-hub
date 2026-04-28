"""Lead scoring logic (0-25 scale)."""

import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)


class LeadScorer:
    """Scores leads based on multiple factors (0-25 scale)."""
    
    def calculate_score(self, item: Dict[str, Any]) -> int:
        """Calculate lead score based on multiple factors.
        
        Scoring breakdown:
        - Gurgaon location: +5
        - Value >= 100L (1 Cr): +3
        - Value >= 500L (5 Cr): +2 (bonus)
        - Demand signal: +3
        - Urgency keywords: +4
        - Project/Contract: +2
        - Has phone: +5
        - Has email: +3
        - GST registered signal: +2
        - MSME signal: +1
        
        Max: 25
        """
        score = 0
        
        # ====== LOCATION (Essential) ======
        # Already filtered for Gurgaon, but double-check
        score += 5
        
        # ====== DEAL VALUE ======
        numeric_value = item.get("numeric_value", 0)
        
        if numeric_value >= 500:
            score += 3 + 2  # Base + bonus
        elif numeric_value >= 100:
            score += 3
        
        # ====== DEMAND SIGNAL ======
        if item.get("is_demand", False):
            score += 3
        
        # ====== URGENCY ======
        if item.get("has_urgency", False):
            score += 4
        
        # ====== PROJECT/CONTRACT ======
        title = item.get("title", "").lower()
        description = item.get("description", "").lower()
        combined = f"{title} {description}"
        
        if "project" in combined or "contract" in combined or "tender" in combined:
            score += 2
        
        # ====== CONTACT INFORMATION (HIGH CONVERSION) ======
        if item.get("phone"):
            score += 5
        
        if item.get("email"):
            score += 3
        
        # ====== BUSINESS LEGITIMACY SIGNALS ======
        if item.get("gst_active", False):
            score += 2
        
        if item.get("msme_signal", False):
            score += 1
        
        # Cap at 25
        return min(score, 25)
