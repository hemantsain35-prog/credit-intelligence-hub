"""Company enrichment utilities."""

import logging
import re
from typing import Dict, Any

logger = logging.getLogger(__name__)


class CompanyEnricher:
    """Enriches leads with company information."""
    
    # Common business types
    BUSINESS_TYPES = {
        "construction": ["construction", "building", "contractor", "civil"],
        "manufacturing": ["manufacturing", "factory", "production", "industrial"],
        "trading": ["trading", "exporter", "importer", "distributor"],
        "services": ["services", "consulting", "solutions", "provider"],
        "logistics": ["logistics", "transport", "shipping", "delivery"],
        "it": ["software", "it", "digital", "technology", "app"],
        "retail": ["retail", "e-commerce", "online", "store"],
    }
    
    def enrich(self, item: Dict[str, Any]) -> Dict[str, Any]:
        """Enrich item with company information."""
        title = item.get("title", "")
        description = item.get("description", "")
        combined_text = f"{title} {description}".lower()
        
        company_name = self._extract_company_name(title)
        business_type = self._detect_business_type(combined_text)
        turnover = self._estimate_turnover(item.get("numeric_value", 0))
        risk = self._assess_risk(item)
        
        return {
            "company": company_name,
            "business_type": business_type,
            "turnover": turnover,
            "risk": risk,
        }
    
    def _extract_company_name(self, title: str) -> str:
        """Extract company name from title (best effort)."""
        # Try to extract a company name from the title
        # This is a simple heuristic - look for capitalized words
        words = title.split()
        capitalized = [w for w in words if w and w[0].isupper() and len(w) > 2]
        
        if capitalized:
            # Return first 2-3 capitalized words as company name
            return " ".join(capitalized[:3])
        
        return "Not specified"
    
    def _detect_business_type(self, text: str) -> str:
        """Detect business type from text."""
        for btype, keywords in self.BUSINESS_TYPES.items():
            for keyword in keywords:
                if keyword in text:
                    return btype.capitalize()
        
        return "Other"
    
    def _estimate_turnover(self, deal_value: int) -> str:
        """Estimate turnover based on deal value."""
        if deal_value == 0:
            return "Unknown"
        
        # Simple heuristic: assume deal is 5-20% of annual turnover
        # Take middle estimate
        estimated_turnover = deal_value * 10  # Rough estimate in lakhs
        
        if estimated_turnover >= 1000:
            return f"₹{estimated_turnover / 100:.0f} Cr+"
        else:
            return f"₹{estimated_turnover:.0f} L+"
    
    def _assess_risk(self, item: Dict[str, Any]) -> str:
        """Assess lead risk level."""
        score = item.get("score", 0)
        
        # Higher score = lower risk
        if score >= 15:
            return "Low"
        elif score >= 10:
            return "Medium"
        else:
            return "High"
