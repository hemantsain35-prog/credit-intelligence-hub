"""Main entry point for multi-source B2B lead intelligence pipeline."""

import logging
from src.scrapers.rss_scraper import RssScraper
from src.scrapers.indiamart_scraper import IndiaMartScraper
from src.scrapers.tradeindia_scraper import TradeIndiaScraper
from src.utils.demand_detector import DemandDetector
from src.utils.location_filter import LocationFilter
from src.utils.lead_scorer import LeadScorer
from src.utils.contact_extractor import ContactExtractor
from src.utils.enrichment import CompanyEnricher
from src.services.telegram_service import TelegramService

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def run_pipeline():
    """Execute the complete multi-source B2B lead intelligence pipeline."""
    logger.info("="*60)
    logger.info("Starting Multi-Source B2B Lead Intelligence Pipeline")
    logger.info("="*60)
    
    all_items = []
    
    # Step 1a: Fetch from IndiaMART
    logger.info("\nStep 1a: Fetching from IndiaMART...")
    try:
        indiamart = IndiaMartScraper()
        indiamart_items = indiamart.fetch_all()
        all_items.extend(indiamart_items)
        logger.info(f"✓ IndiaMART: {len(indiamart_items)} items fetched")
    except Exception as e:
        logger.error(f"✗ IndiaMART scraping failed: {str(e)}")
    
    # Step 1b: Fetch from TradeIndia
    logger.info("\nStep 1b: Fetching from TradeIndia...")
    try:
        tradeindia = TradeIndiaScraper()
        tradeindia_items = tradeindia.fetch_all()
        all_items.extend(tradeindia_items)
        logger.info(f"✓ TradeIndia: {len(tradeindia_items)} items fetched")
    except Exception as e:
        logger.error(f"✗ TradeIndia scraping failed: {str(e)}")
    
    # Step 1c: Fetch from RSS
    logger.info("\nStep 1c: Fetching from RSS feeds...")
    try:
        rss = RssScraper()
        rss_items = rss.fetch_all()
        all_items.extend(rss_items)
        logger.info(f"✓ RSS: {len(rss_items)} items fetched")
    except Exception as e:
        logger.error(f"✗ RSS scraping failed: {str(e)}")
    
    logger.info(f"\n{'='*60}")
    logger.info(f"Total items from all sources: {len(all_items)}")
    logger.info(f"{'='*60}")
    
    if not all_items:
        logger.warning("No items fetched from any source. Exiting.")
        return
    
    # Step 2: Remove duplicates by URL
    logger.info("\nStep 2: Removing duplicates...")
    unique_items = {}
    for item in all_items:
        url = item.get("url", "")
        if url and url not in unique_items:
            unique_items[url] = item
    all_items = list(unique_items.values())
    logger.info(f"After deduplication: {len(all_items)} unique items")
    
    # Step 3: Demand detection & value extraction
    logger.info("\nStep 3: Detecting demand and extracting values...")
    detector = DemandDetector()
    items_with_demand = []
    
    for item in all_items:
        demand_info = detector.analyze(item)
        if demand_info["is_demand"]:
            item.update(demand_info)
            items_with_demand.append(item)
    
    logger.info(f"✓ Demand detected in {len(items_with_demand)} items")
    
    # Step 4: Value filter (>= 50 lakh)
    logger.info("\nStep 4: Filtering by deal size (>= 50 lakh)...")
    high_value_items = [
        item for item in items_with_demand
        if item.get("numeric_value", 0) >= 50
    ]
    logger.info(f"✓ High-value deals (>= 50L): {len(high_value_items)}")
    
    # Step 5: Gurgaon location filter (STRICT)
    logger.info("\nStep 5: Filtering by Gurgaon location (STRICT)...")
    location_filter = LocationFilter()
    gurgaon_items = [
        item for item in high_value_items
        if location_filter.is_gurgaon(item.get("title", "")) or 
           location_filter.is_gurgaon(item.get("description", "")) or
           location_filter.is_gurgaon(item.get("location", ""))
    ]
    logger.info(f"✓ Gurgaon-based opportunities: {len(gurgaon_items)}")
    
    # Step 6: Contact extraction
    logger.info("\nStep 6: Extracting contact information...")
    contact_extractor = ContactExtractor()
    for item in gurgaon_items:
        contacts = contact_extractor.extract(item)
        item.update(contacts)
    
    items_with_contacts = [
        item for item in gurgaon_items
        if item.get("phone") or item.get("email")
    ]
    logger.info(f"✓ Items with contact info: {len(items_with_contacts)}/{len(gurgaon_items)}")
    
    # Step 7: Company enrichment
    logger.info("\nStep 7: Enriching company information...")
    enricher = CompanyEnricher()
    for item in gurgaon_items:
        enrichment = enricher.enrich(item)
        item.update(enrichment)
    
    # Step 8: Lead scoring (with contact bonus)
    logger.info("\nStep 8: Scoring leads...")
    scorer = LeadScorer()
    for item in gurgaon_items:
        item["score"] = scorer.calculate_score(item)
    
    # Step 9: Final filter (score >= 5)
    logger.info("\nStep 9: Final quality filter (score >= 5)...")
    qualified_leads = [
        item for item in gurgaon_items
        if item.get("score", 0) >= 5
    ]
    logger.info(f"✓ Qualified leads: {len(qualified_leads)}")
    
    if not qualified_leads:
        logger.info("\nNo qualified leads found. Pipeline complete.")
        return
    
    # Step 10: Sort by score (highest first) and take top 10
    logger.info("\nStep 10: Ranking leads by quality...")
    qualified_leads.sort(key=lambda x: x.get("score", 0), reverse=True)
    top_leads = qualified_leads[:10]
    logger.info(f"✓ Top {len(top_leads)} leads selected")
    
    # Step 11: Send to Telegram
    logger.info("\nStep 11: Sending alerts to Telegram...")
    telegram = TelegramService()
    success = telegram.send_leads(top_leads)
    
    if success:
        logger.info(f"✓ Successfully sent {len(top_leads)} leads to Telegram")
    else:
        logger.warning("Telegram delivery pending (credentials may not be configured)")
    
    logger.info(f"\n{'='*60}")
    logger.info("Pipeline execution complete!")
    logger.info(f"{'='*60}\n")


if __name__ == "__main__":
    run_pipeline()
