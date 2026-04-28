"""RSS feed scraper for lead intelligence."""

import logging
from typing import List, Dict, Any

try:
    import feedparser
    FEEDPARSER_AVAILABLE = True
except ImportError:
    FEEDPARSER_AVAILABLE = False

logger = logging.getLogger(__name__)


class RssScraper:
    """Scrapes RSS feeds and normalizes items."""
    
    RSS_FEEDS = [
        "https://news.google.com/rss/search?q=tender+india",
        "https://news.google.com/rss/search?q=construction+project+india",
        "https://news.google.com/rss/search?q=supplier+requirement+india",
    ]
    
    TIMEOUT = 10  # seconds
    
    def fetch_all(self) -> List[Dict[str, Any]]:
        """Fetch and normalize items from all RSS feeds."""
        if not FEEDPARSER_AVAILABLE:
            logger.warning("feedparser not installed. Install with: pip install feedparser")
            return []
        
        all_items = []
        
        for feed_url in self.RSS_FEEDS:
            try:
                logger.debug(f"Fetching feed: {feed_url}")
                items = self._fetch_feed(feed_url)
                all_items.extend(items)
                logger.debug(f"Fetched {len(items)} items from {feed_url}")
            except Exception as e:
                logger.debug(f"Error fetching {feed_url}: {str(e)}")
                continue
        
        # Remove duplicates based on URL
        unique_items = {}
        for item in all_items:
            url = item.get("url", "")
            if url and url not in unique_items:
                unique_items[url] = item
        
        return list(unique_items.values())
    
    def _fetch_feed(self, feed_url: str) -> List[Dict[str, Any]]:
        """Fetch items from a single RSS feed."""
        feed = feedparser.parse(feed_url)
        items = []
        
        if feed.bozo:
            logger.debug(f"Feed parsing warning for {feed_url}")
        
        for entry in feed.entries[:20]:  # Limit to 20 items per feed
            item = self._normalize_entry(entry)
            if item:
                items.append(item)
        
        return items
    
    def _normalize_entry(self, entry: Any) -> Dict[str, str]:
        """Normalize RSS entry into standard format."""
        try:
            title = entry.get("title", "").strip()
            description = entry.get("summary", "").strip()
            url = entry.get("link", "").strip()
            
            if not title or not url:
                return None
            
            return {
                "title": title,
                "description": description,
                "location": "",
                "url": url,
                "source": "RSS",
            }
        except Exception as e:
            logger.debug(f"Error normalizing entry: {str(e)}")
            return None
