"""Company enrichment utilities."""

import logging
import re
from typing import Dict, Any
from src.utils.justdial_lookup import JustDialLookup

logger = logging.getLogger(__name__)


class CompanyEnricher:
    """Enriches leads with company information and signals."""
    
    # Common business types
    BUSINESS_TYPES = {
        "construction": ["construction", "building", "contractor", "civil", "infrastructure"],
        "manufacturing": ["manufacturing", "factory", "production", "industrial", "units"],
        "trading": ["trading", "exporter", "importer", "distributor", "wholesale"],
        "services": ["services", "consulting", "solutions", "provider", "agency"],
        "logistics": ["logistics", "transport", "shipping", "delivery", "courier"],
        "it": ["software", "it", "digital", "technology", "app", "web"],
        "retail": ["retail", "e-commerce", "online", "store", "shopping"],
    }
    
    def __init__(self):
        """Initialize enricher with JustDial lookup."""
        self.justdial = JustDialLookup()
    
    def enrich(self, item: Dict[str, Any]) -> Dict[str, Any]:
        """Enrich item with company information."""
        title = item.get("title", "")
        description = item.get("description", "")
        combined_text = f"{title} {description}".lower()
        
        company_name = item.get("company") or self._extract_company_name(title)
        business_type = self._detect_business_type(combined_text)
        gst_active = self._detect_gst_signal(combined_text)
        msme_signal = self._detect_msme_signal(combined_text)
        risk = self._assess_risk(item)
        
        enrichment = {
            "company": company_name,
            "business_type": business_type,
            "gst_active": gst_active,
            "msme_signal": msme_signal,
            "risk": risk,
        }
        
        # Optional: Try JustDial lookup if company name exists
        if company_name and company_name != "Not specified":
            try:
                justdial_data = self.justdial.lookup(company_name)
                if justdial_data.get("phone") and not item.get("phone"):
                    enrichment["phone_justdial"] = justdial_data.get("phone")
                if justdial_data.get("address"):
                    enrichment["address_justdial"] = justdial_data.get("address")
            except Exception as e:
                logger.debug(f"JustDial lookup failed for {company_name}: {str(e)}")
        
        return enrichment
    
    def _extract_company_name(self, title: str) -> str:
        """Extract company name from title."""
        if not title:
            return "Not specified"
        
        # Remove common prefixes/suffixes
        cleaned = re.sub(r'(^(need|urgent|looking|requirement|wanted|supplier)\s+|\s+(supplier|contractor|vendor|service|needed)$)', '', title, flags=re.IGNORECASE).strip()
        
        # Get first 2-3 capitalized words
        words = cleaned.split()
        capitalized = [w for w in words if w and w[0].isupper() and len(w) > 2]
        
        if capitalized:
            return " ".join(capitalized[:3])
        
        if len(words) > 0:
            return words[0][:30]  # First word up to 30 chars
        
        return "Not specified"
    
    def _detect_business_type(self, text: str) -> str:
        """Detect business type from text."""
        for btype, keywords in self.BUSINESS_TYPES.items():
            for keyword in keywords:
                if keyword in text:
                    return btype.capitalize()
        
        return "Other"
    
    def _detect_gst_signal(self, text: str) -> bool:
        """Detect GST active signal from text."""
        gst_keywords = [
            "gst", "gst registered", "gst number", "gstin",
            "tax compliant", "registered business"
        ]
        
        for keyword in gst_keywords:
            if keyword in text:
                return True
        
        return False
    
    def _detect_msme_signal(self, text: str) -> bool:
        """Detect MSME signal from text."""
        msme_keywords = [
            "msme", "micro enterprise", "small enterprise", "medium enterprise",
            "startup", "sme", "udyam", "msme registered"
        ]
        
        for keyword in msme_keywords:
            if keyword in text:
                return True
        
        return False
    
    def _assess_risk(self, item: Dict[str, Any]) -> str:
        """Assess lead risk level."""
        score = item.get("score", 0)
        has_contact = item.get("phone") or item.get("email")
        gst_active = item.get("gst_active", False)
        
        # Higher score + contact info + GST = lower risk
        if score >= 15 and has_contact and gst_active:
            return "Low"
        elif score >= 12 and has_contact:
            return "Low"
        elif score >= 10 and has_contact:
            return "Medium"
        elif score >= 8:
            return "Medium"
        else:
            return "High"
