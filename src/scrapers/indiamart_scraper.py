"""IndiaMART B2B marketplace scraper."""

import logging
from typing import List, Dict, Any

try:
    from playwright.sync_api import sync_playwright
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False

logger = logging.getLogger(__name__)


class IndiaMART:
    """Scrapes buyer requirements from IndiaMART."""
    
    BASE_URL = "https://www.indiamart.com/os/general-requirement/"
    SEARCH_KEYWORDS = [
        "need supplier",
        "requirement",
        "vendor needed",
    ]
    TIMEOUT = 15000  # 15 seconds
    
    def fetch_all(self) -> List[Dict[str, Any]]:
        """Fetch buyer requirements from IndiaMART."""
        if not PLAYWRIGHT_AVAILABLE:
            logger.warning("Playwright not installed. Install with: pip install playwright")
            return []
        
        all_items = []
        
        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                page = browser.new_page()
                page.set_default_timeout(self.TIMEOUT)
                
                # Fetch general requirements page
                logger.debug(f"Visiting {self.BASE_URL}")
                page.goto(self.BASE_URL, wait_until="networkidle", timeout=self.TIMEOUT)
                
                # Extract requirements
                items = page.query_selector_all(".flxWrap.mt-10 .BuyrReqBox")
                
                for item_elem in items:
                    try:
                        item = self._parse_item(item_elem)
                        if item:
                            all_items.append(item)
                    except Exception as e:
                        logger.debug(f"Error parsing IndiaMART item: {str(e)}")
                        continue
                
                browser.close()
        
        except Exception as e:
            logger.error(f"IndiaMART scraping error: {str(e)}")
        
        return all_items
    
    def _parse_item(self, elem) -> Dict[str, Any]:
        """Parse IndiaMART requirement item."""
        try:
            title = elem.query_selector(".BrTitle")?.text_content("").strip() or ""
            description = elem.query_selector(".BrDesc")?.text_content("").strip() or ""
            location = elem.query_selector(".BrLoc")?.text_content("").strip() or ""
            url = elem.query_selector("a")?.get_attribute("href") or ""
            
            if not title or not url:
                return None
            
            # Ensure URL is absolute
            if url.startswith("/"):
                url = "https://www.indiamart.com" + url
            elif not url.startswith("http"):
                url = "https://www.indiamart.com" + url
            
            return {
                "title": title,
                "description": description,
                "location": location,
                "url": url,
                "source": "IndiaMART",
            }
        
        except Exception as e:
            logger.debug(f"Error parsing item element: {str(e)}")
            return None
