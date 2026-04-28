"""Lead scoring logic."""

import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)


class LeadScorer:
    """Scores leads based on multiple factors."""
    
    def calculate_score(self, item: Dict[str, Any]) -> int:
        """Calculate lead score based on multiple factors."""
        score = 0
        
        # Base score for being from Gurgaon
        score += 5
        
        # Bonus for high-value deals (>= 1 Cr = 100L)
        if item.get("numeric_value", 0) >= 100:
            score += 3
        
        # Bonus for clear demand signal
        if item.get("is_demand", False):
            score += 3
        
        # Bonus for urgency
        if item.get("has_urgency", False):
            score += 4
        
        # Bonus for project/contract keywords
        title = item.get("title", "").lower()
        description = item.get("description", "").lower()
        combined = f"{title} {description}"
        
        if "project" in combined or "contract" in combined or "tender" in combined:
            score += 2
        
        return min(score, 20)  # Cap at 20
