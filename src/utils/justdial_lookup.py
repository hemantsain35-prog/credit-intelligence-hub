"""JustDial company enrichment and lookup."""

import logging
import requests
from typing import Dict, Any, Optional
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)


class JustDialLookup:
    """Lookup company details on JustDial."""
    
    BASE_URL = "https://www.justdial.com"
    SEARCH_URL = "https://www.justdial.com/search"
    
    TIMEOUT = 10
    HEADERS = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }
    
    def lookup(self, company_name: str, location: str = "Gurgaon") -> Dict[str, Any]:
        """Look up company on JustDial."""
        result = {
            "phone": "",
            "address": "",
            "category": "",
        }
        
        if not company_name:
            return result
        
        try:
            details = self._search_company(company_name, location)
            if details:
                result.update(details)
        except Exception as e:
            logger.debug(f"JustDial lookup error for '{company_name}': {str(e)}")
        
        return result
    
    def _search_company(self, name: str, location: str) -> Optional[Dict[str, str]]:
        """Search for company on JustDial."""
        try:
            params = {
                "keyword": name,
                "ctg": "All",
                "lbzt_lt": location,
            }
            
            response = requests.get(
                self.SEARCH_URL,
                params=params,
                headers=self.HEADERS,
                timeout=self.TIMEOUT
            )
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, "html.parser")
            
            # Find first result
            result_div = soup.find("div", class_="jcn")
            if not result_div:
                return None
            
            # Extract phone
            phone_elem = result_div.find("span", class_="phno")
            phone = phone_elem.get_text(strip=True) if phone_elem else ""
            
            # Extract address
            address_elem = result_div.find("div", class_="locadd")
            address = address_elem.get_text(strip=True) if address_elem else ""
            
            # Extract category
            category_elem = result_div.find("div", class_="det_txt")
            category = category_elem.get_text(strip=True) if category_elem else ""
            
            return {
                "phone": phone,
                "address": address,
                "category": category,
            }
        
        except Exception as e:
            logger.debug(f"Error searching JustDial: {str(e)}")
            return None
