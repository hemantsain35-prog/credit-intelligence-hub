"""Lead scoring logic with high-conversion focus."""

import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)


class LeadScorer:
    """Scores leads based on multiple factors for high-conversion potential."""
    
    def calculate_score(self, item: Dict[str, Any]) -> int:
        """Calculate lead score based on multiple factors (0-25)."""
        score = 0
        
        # Base: Gurgaon location (essential)
        score += 5
        
        # Bonus: High-value deals (>= 1 Cr = 100L)
        if item.get("numeric_value", 0) >= 100:
            score += 3
        
        # Very high value (>= 5 Cr = 500L)
        if item.get("numeric_value", 0) >= 500:
            score += 2
        
        # Bonus: Clear demand signal
        if item.get("is_demand", False):
            score += 3
        
        # Bonus: Urgency keywords (immediate conversion signal)
        if item.get("has_urgency", False):
            score += 4
        
        # Bonus: Project/contract keywords (defined scope)
        title = item.get("title", "").lower()
        description = item.get("description", "").lower()
        combined = f"{title} {description}"
        
        if "project" in combined or "contract" in combined or "tender" in combined:
            score += 2
        
        # CRITICAL BONUS: Contact information available (conversion enabler)
        if item.get("phone"):
            score += 5
        if item.get("email"):
            score += 3
        
        # Bonus: GST signal (legitimate business)
        if item.get("gst_active", False):
            score += 2
        
        # Bonus: MSME signal (supportive ecosystem)
        if item.get("msme_signal", False):
            score += 1
        
        return min(score, 25)  # Cap at 25
