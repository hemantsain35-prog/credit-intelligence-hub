"""Company enrichment utilities."""

import logging
import re
from typing import Dict, Any
from src.utils.justdial_lookup import JustDialLookup

logger = logging.getLogger(__name__)


class CompanyEnricher:
    """Enriches leads with company information."""
    
    # Common business types
    BUSINESS_TYPES = {
        "construction": ["construction", "building", "contractor", "civil", "architect"],
        "manufacturing": ["manufacturing", "factory", "production", "industrial", "mill"],
        "trading": ["trading", "exporter", "importer", "distributor", "wholesale"],
        "services": ["services", "consulting", "solutions", "provider", "agency"],
        "logistics": ["logistics", "transport", "shipping", "delivery", "courier"],
        "it": ["software", "it", "digital", "technology", "app", "development"],
        "retail": ["retail", "e-commerce", "online", "store", "shop"],
        "machinery": ["machinery", "equipment", "machine", "industrial"],
        "chemicals": ["chemicals", "pharmaceutical", "chemical"],
        "textiles": ["textiles", "fabric", "garment", "textile"],
    }
    
    # GST registration keywords
    GST_KEYWORDS = {
        "gst registered", "gst no", "gst number", "gst number:",
        "gst ain", "registered under gst", "gst compliant"
    }
    
    # MSME signals
    MSME_KEYWORDS = {
        "msme", "micro enterprise", "small enterprise", "medium enterprise",
        "startup", "sme", "ugam", "msme registered"
    }
    
    def __init__(self):
        """Initialize enricher."""
        self.justdial = JustDialLookup()
    
    def enrich(self, item: Dict[str, Any]) -> Dict[str, Any]:
        """Enrich item with company information."""
        title = item.get("title", "")
        description = item.get("description", "")
        combined_text = f"{title} {description}".lower()
        
        company_name = self._extract_company_name(title)
        business_type = self._detect_business_type(combined_text)
        gst_active = self._check_gst_signal(combined_text)
        msme_signal = self._check_msme_signal(combined_text)
        risk = self._assess_risk(item)
        
        enrichment = {
            "company": company_name,
            "business_type": business_type,
            "gst_active": gst_active,
            "msme_signal": msme_signal,
            "risk": risk,
        }
        
        # Optional: JustDial lookup (may be slow)
        # Uncomment to enable:
        # if company_name and company_name != "Not specified":
        #     justdial_data = self.justdial.lookup(company_name)
        #     enrichment.update(justdial_data)
        # else:
        enrichment["phone_justdial"] = ""
        enrichment["address_justdial"] = ""
        enrichment["business_category_justdial"] = ""
        
        return enrichment
    
    def _extract_company_name(self, title: str) -> str:
        """Extract company name from title (best effort)."""
        if not title:
            return "Not specified"
        
        # Try to extract company name from title
        # Remove common prefixes
        cleaned = title
        prefixes = ["need", "wanted", "requirement", "supplier", "vendor", "urgent"]
        
        for prefix in prefixes:
            if cleaned.lower().startswith(prefix):
                cleaned = cleaned[len(prefix):].strip()
                break
        
        # Extract capitalized words
        words = cleaned.split()
        capitalized = [w.strip(":-") for w in words if w and w[0].isupper() and len(w) > 2]
        
        if capitalized:
            # Return first 2-3 capitalized words as company name
            return " ".join(capitalized[:3])
        
        # Fallback: return first part of title
        parts = title.split("-")
        if parts:
            return parts[0].strip()[:50]  # Limit to 50 chars
        
        return "Not specified"
    
    def _detect_business_type(self, text: str) -> str:
        """Detect business type from text."""
        for btype, keywords in self.BUSINESS_TYPES.items():
            for keyword in keywords:
                if keyword in text:
                    return btype.capitalize()
        
        return "Other"
    
    def _check_gst_signal(self, text: str) -> bool:
        """Check for GST registration signal."""
        for keyword in self.GST_KEYWORDS:
            if keyword in text:
                return True
        return False
    
    def _check_msme_signal(self, text: str) -> bool:
        """Check for MSME signal."""
        for keyword in self.MSME_KEYWORDS:
            if keyword in text:
                return True
        return False
    
    def _assess_risk(self, item: Dict[str, Any]) -> str:
        """Assess lead risk level (Low/Medium/High)."""
        score = item.get("score", 0)
        has_contact = bool(item.get("phone") or item.get("email"))
        gst_active = item.get("gst_active", False)
        
        # Higher score + contact info + GST = Lower risk
        if score >= 18 and has_contact and gst_active:
            return "Low"
        elif score >= 15 and has_contact:
            return "Low"
        elif score >= 12:
            return "Medium"
        else:
            return "High"
