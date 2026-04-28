"""IndiaMART B2B marketplace scraper."""

import logging
import requests
from typing import List, Dict, Any
from bs4 import BeautifulSoup
from urllib.parse import urljoin

logger = logging.getLogger(__name__)


class IndiaMartScraper:
    """Scrapes IndiaMART for buyer requirements and supplier needs."""
    
    BASE_URL = "https://www.indiamart.com"
    SEARCH_URL = "https://www.indiamart.com/os/general-requirement"
    
    KEYWORDS = [
        "supplier",
        "requirement",
        "vendor needed",
        "buyer requirement",
    ]
    
    TIMEOUT = 10
    HEADERS = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }
    
    def fetch_all(self) -> List[Dict[str, Any]]:
        """Fetch all relevant listings from IndiaMART."""
        items = []
        
        try:
            logger.debug("Attempting IndiaMART scrape...")
            # Note: IndiaMART requires JavaScript rendering
            # For MVP, we'll collect items from static content if available
            items.extend(self._fetch_requirement_page())
        except Exception as e:
            logger.debug(f"IndiaMART scrape encountered issue: {str(e)}")
        
        return items
    
    def _fetch_requirement_page(self) -> List[Dict[str, Any]]:
        """Fetch from general requirements page."""
        items = []
        
        try:
            response = requests.get(
                self.SEARCH_URL,
                headers=self.HEADERS,
                timeout=self.TIMEOUT
            )
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, "html.parser")
            listings = soup.find_all("div", class_="os-item")
            
            for listing in listings:
                item = self._parse_listing(listing)
                if item:
                    items.append(item)
            
            logger.debug(f"IndiaMART: Parsed {len(items)} listings")
        
        except requests.RequestException as e:
            logger.debug(f"IndiaMART request failed: {str(e)}")
        except Exception as e:
            logger.debug(f"IndiaMART parsing error: {str(e)}")
        
        return items
    
    def _parse_listing(self, listing) -> Dict[str, Any]:
        """Parse individual IndiaMART listing."""
        try:
            title_elem = listing.find("h4", class_="os-title")
            desc_elem = listing.find("div", class_="os-desc")
            link_elem = listing.find("a")
            location_elem = listing.find("span", class_="os-location")
            
            title = title_elem.get_text(strip=True) if title_elem else ""
            description = desc_elem.get_text(strip=True) if desc_elem else ""
            url = link_elem.get("href", "") if link_elem else ""
            location = location_elem.get_text(strip=True) if location_elem else ""
            
            if url and url.startswith("/"):
                url = urljoin(self.BASE_URL, url)
            
            if not title:
                return None
            
            return {
                "title": title,
                "description": description,
                "location": location,
                "url": url,
                "source": "IndiaMART",
                "phone": "",
                "email": "",
            }
        
        except Exception as e:
            logger.debug(f"Error parsing IndiaMART listing: {str(e)}")
            return None
