"""Main entry point for multi-source B2B lead intelligence pipeline."""

import logging
import hashlib

from src.scrapers.indiamart_scraper import IndiaMART
from src.scrapers.tradeindia_scraper import TradeIndia
from src.scrapers.rss_scraper import RssScraper
from src.utils.demand_detector import DemandDetector
from src.utils.location_filter import LocationFilter
from src.utils.contact_extractor import ContactExtractor
from src.utils.lead_scorer import LeadScorer
from src.utils.enrichment import CompanyEnricher
from src.services.telegram_service import TelegramService

# ✅ NEW: Sheets webhook
from src.services.sheets_webhook import send_to_sheet


logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def deduplicate_items(items):
    """Remove duplicate items by URL."""
    seen_urls = set()
    unique_items = []
    
    for item in items:
        url = item.get("url", "")
        if url and url not in seen_urls:
            seen_urls.add(url)
            unique_items.append(item)
        elif not url:
            unique_items.append(item)
    
    return unique_items


# ✅ NEW: ID generator
def generate_id(item):
    text = (item.get("title", "") + item.get("url", "")).strip()
    return hashlib.md5(text.encode()).hexdigest()


def run_pipeline():
    """Execute the complete multi-source B2B lead intelligence pipeline."""
    logger.info("="*60)
    logger.info("Starting Multi-Source B2B Lead Intelligence Pipeline")
    logger.info("="*60)
    
    # ============================================================
    # STEP 1: FETCH FROM ALL SOURCES
    # ============================================================
    logger.info("\nStep 1a: Fetching from IndiaMART...")
    try:
        indiamart = IndiaMART()
        indiamart_items = indiamart.fetch_all()
        logger.info(f"✓ IndiaMART: {len(indiamart_items)} items fetched")
    except Exception as e:
        logger.error(f"✗ IndiaMART error: {str(e)}")
        indiamart_items = []
    
    logger.info("Step 1b: Fetching from TradeIndia...")
    try:
        tradeindia = TradeIndia()
        tradeindia_items = tradeindia.fetch_all()
        logger.info(f"✓ TradeIndia: {len(tradeindia_items)} items fetched")
    except Exception as e:
        logger.error(f"✗ TradeIndia error: {str(e)}")
        tradeindia_items = []
    
    logger.info("Step 1c: Fetching from RSS feeds...")
    try:
        rss = RssScraper()
        rss_items = rss.fetch_all()
        logger.info(f"✓ RSS: {len(rss_items)} items fetched")
    except Exception as e:
        logger.error(f"✗ RSS error: {str(e)}")
        rss_items = []
    
    all_items = indiamart_items + tradeindia_items + rss_items
    logger.info(f"\n{'='*60}")
    logger.info(f"Total items from all sources: {len(all_items)}")
    logger.info(f"{'='*60}")
    
    if not all_items:
        logger.warning("No items fetched from any source. Exiting.")
        return
    
    # ============================================================
    # STEP 2: DEDUPLICATION
    # ============================================================
    logger.info("\nStep 2: Removing duplicates...")
    unique_items = deduplicate_items(all_items)
    logger.info(f"After deduplication: {len(unique_items)} unique items")
    
    # ============================================================
    # STEP 3: DEMAND DETECTION
    # ============================================================
    logger.info("\nStep 3: Detecting demand and extracting values...")
    detector = DemandDetector()
    items_with_demand = []
    
    for item in unique_items:
        demand_info = detector.analyze(item)
        if demand_info["is_demand"]:
            item.update(demand_info)
            items_with_demand.append(item)
    
    logger.info(f"✓ Demand detected in {len(items_with_demand)} items")
    
    # ============================================================
    # STEP 4: VALUE FILTER
    # ============================================================
    logger.info("\nStep 4: Filtering by deal size (>= 50 lakh)...")
    high_value_items = [
        item for item in items_with_demand
        if item.get("numeric_value", 0) >= 50
    ]
    logger.info(f"✓ High-value deals (>= 50L): {len(high_value_items)}")
    
    # ============================================================
    # STEP 5: LOCATION FILTER
    # ============================================================
    logger.info("\nStep 5: Filtering by Gurgaon location (STRICT)...")
    location_filter = LocationFilter()
    gurgaon_items = [
        item for item in high_value_items
        if location_filter.is_gurgaon(item.get("title", "")) or
           location_filter.is_gurgaon(item.get("description", "")) or
           location_filter.is_gurgaon(item.get("location", ""))
    ]
    logger.info(f"✓ Gurgaon-based opportunities: {len(gurgaon_items)}")
    
    if not gurgaon_items:
        logger.info("No Gurgaon-based opportunities found. Exiting.")
        return
    
    # ============================================================
    # STEP 6: CONTACT EXTRACTION
    # ============================================================
    logger.info("\nStep 6: Extracting contact information...")
    contact_extractor = ContactExtractor()
    
    for item in gurgaon_items:
        full_text = f"{item.get('title', '')} {item.get('description', '')}"
        contacts = contact_extractor.extract(full_text)
        item.update(contacts)
    
    # ============================================================
    # STEP 7: ENRICHMENT
    # ============================================================
    logger.info("\nStep 7: Enriching company information...")
    enricher = CompanyEnricher()
    
    for item in gurgaon_items:
        enrichment = enricher.enrich(item)
        item.update(enrichment)
    
    # ============================================================
    # STEP 8: SCORING
    # ============================================================
    logger.info("\nStep 8: Scoring leads...")
    scorer = LeadScorer()
    
    for item in gurgaon_items:
        item["score"] = scorer.calculate_score(item)
    
    # ============================================================
    # STEP 9: FINAL FILTER
    # ============================================================
    logger.info("\nStep 9: Final quality filter (score >= 5)...")
    qualified_leads = [
        item for item in gurgaon_items
        if item.get("score", 0) >= 5
    ]
    
    if not qualified_leads:
        logger.info("No qualified leads found. Exiting.")
        return
    
    # ============================================================
    # STEP 10: RANKING
    # ============================================================
    qualified_leads.sort(key=lambda x: x.get("score", 0), reverse=True)
    top_leads = qualified_leads[:10]
    
    # ============================================================
    # ✅ NEW STEP: SAVE TO GOOGLE SHEET (CRM)
    # ============================================================
    logger.info("\nStep 10.1: Saving leads to CRM...")
    
    for lead in top_leads:
        lead["id"] = generate_id(lead)
        try:
            send_to_sheet(lead)
        except Exception as e:
            logger.warning(f"Sheet save failed: {str(e)}")
    
    logger.info("✓ Leads saved to CRM")
    
    # ============================================================
    # STEP 11: TELEGRAM
    # ============================================================
    logger.info("\nStep 11: Sending alerts to Telegram...")
    telegram = TelegramService()
    telegram.send_leads(top_leads)
    
    logger.info("\nPipeline execution complete!")


if __name__ == "__main__":
    run_pipeline()
