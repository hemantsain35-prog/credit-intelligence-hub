"""Location filtering utilities."""

import logging

logger = logging.getLogger(__name__)


class LocationFilter:
    """Filters leads by location."""
    
    GURGAON_VARIANTS = {
        "gurgaon",
        "gurugram",
        "gurgaon, haryana",
        "gurugram, haryana",
        "ncr gurgaon",
        "gurgaon ncr",
        "gurgaon, ncr",
        "gurgaon (haryana)",
        "gurugram (haryana)",
    }
    
    @staticmethod
    def is_gurgaon(text: str) -> bool:
        """Check if text references Gurgaon/Gurugram location (STRICT)."""
        if not text:
            return False
        
        text_lower = text.lower().strip()
        
        # Direct matching
        return "gurgaon" in text_lower or "gurugram" in text_lower
