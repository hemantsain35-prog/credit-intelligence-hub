"""TradeIndia B2B marketplace scraper."""

import logging
import requests
from typing import List, Dict, Any
from bs4 import BeautifulSoup
from urllib.parse import urljoin

logger = logging.getLogger(__name__)


class TradeIndiaScraper:
    """Scrapes TradeIndia for buyer requirements and supplier needs."""
    
    BASE_URL = "https://www.tradeindia.com"
    SEARCH_URL = "https://www.tradeindia.com/buyerRequirements.html"
    
    TIMEOUT = 10
    HEADERS = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }
    
    def fetch_all(self) -> List[Dict[str, Any]]:
        """Fetch all relevant listings from TradeIndia."""
        items = []
        
        try:
            logger.debug("Attempting TradeIndia scrape...")
            items.extend(self._fetch_buyer_requirements())
        except Exception as e:
            logger.debug(f"TradeIndia scrape encountered issue: {str(e)}")
        
        return items
    
    def _fetch_buyer_requirements(self) -> List[Dict[str, Any]]:
        """Fetch from buyer requirements page."""
        items = []
        
        try:
            response = requests.get(
                self.SEARCH_URL,
                headers=self.HEADERS,
                timeout=self.TIMEOUT
            )
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, "html.parser")
            
            # TradeIndia uses different structure
            listings = soup.find_all("div", class_="requirement-item")
            if not listings:
                listings = soup.find_all("div", class_="buyerRequirement")
            
            for listing in listings:
                item = self._parse_listing(listing)
                if item:
                    items.append(item)
            
            logger.debug(f"TradeIndia: Parsed {len(items)} listings")
        
        except requests.RequestException as e:
            logger.debug(f"TradeIndia request failed: {str(e)}")
        except Exception as e:
            logger.debug(f"TradeIndia parsing error: {str(e)}")
        
        return items
    
    def _parse_listing(self, listing) -> Dict[str, Any]:
        """Parse individual TradeIndia listing."""
        try:
            title_elem = listing.find("a", class_="req-title")
            if not title_elem:
                title_elem = listing.find("h3")
            
            desc_elem = listing.find("p", class_="req-desc")
            if not desc_elem:
                desc_elem = listing.find("p")
            
            location_elem = listing.find("span", class_="req-location")
            url_elem = listing.find("a", href=True)
            
            title = title_elem.get_text(strip=True) if title_elem else ""
            description = desc_elem.get_text(strip=True) if desc_elem else ""
            location = location_elem.get_text(strip=True) if location_elem else ""
            url = url_elem.get("href", "") if url_elem else ""
            
            if url and url.startswith("/"):
                url = urljoin(self.BASE_URL, url)
            
            if not title:
                return None
            
            return {
                "title": title,
                "description": description,
                "location": location,
                "url": url,
                "source": "TradeIndia",
                "phone": "",
                "email": "",
            }
        
        except Exception as e:
            logger.debug(f"Error parsing TradeIndia listing: {str(e)}")
            return None
