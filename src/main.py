"""Main entry point for RSS-based lead intelligence pipeline."""

import logging
from src.scrapers.rss_scraper import RssScraper
from src.utils.demand_detector import DemandDetector
from src.utils.location_filter import LocationFilter
from src.utils.lead_scorer import LeadScorer
from src.utils.enrichment import CompanyEnricher
from src.services.telegram_service import TelegramService

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def run_pipeline():
    """Execute the complete RSS-to-Telegram pipeline."""
    logger.info("Starting RSS lead intelligence pipeline...")
    
    # Step 1: Fetch RSS feeds
    logger.info("Step 1: Fetching RSS feeds...")
    scraper = RssScraper()
    raw_items = scraper.fetch_all()
    logger.info(f"Fetched {len(raw_items)} items from RSS feeds")
    
    if not raw_items:
        logger.warning("No items fetched from RSS feeds. Exiting.")
        return
    
    # Step 2: Demand detection & value extraction
    logger.info("Step 2: Detecting demand and extracting values...")
    detector = DemandDetector()
    items_with_demand = []
    
    for item in raw_items:
        demand_info = detector.analyze(item)
        if demand_info["is_demand"]:
            item.update(demand_info)
            items_with_demand.append(item)
    
    logger.info(f"Demand detected in {len(items_with_demand)} items")
    
    # Step 3: Value filter (>= 50 lakh)
    logger.info("Step 3: Filtering by deal size (>= 50 lakh)...")
    high_value_items = [
        item for item in items_with_demand
        if item.get("numeric_value", 0) >= 50
    ]
    logger.info(f"High-value deals (>= 50L): {len(high_value_items)}")
    
    # Step 4: Gurgaon location filter
    logger.info("Step 4: Filtering by Gurgaon location...")
    location_filter = LocationFilter()
    gurgaon_items = [
        item for item in high_value_items
        if location_filter.is_gurgaon(item.get("title", "")) or 
           location_filter.is_gurgaon(item.get("description", ""))
    ]
    logger.info(f"Gurgaon-based opportunities: {len(gurgaon_items)}")
    
    # Step 5: Lead scoring
    logger.info("Step 5: Scoring leads...")
    scorer = LeadScorer()
    for item in gurgaon_items:
        item["score"] = scorer.calculate_score(item)
    
    # Step 6: Final filter (score >= 5)
    logger.info("Step 6: Final quality filter (score >= 5)...")
    qualified_leads = [
        item for item in gurgaon_items
        if item.get("score", 0) >= 5
    ]
    logger.info(f"Qualified leads: {len(qualified_leads)}")
    
    if not qualified_leads:
        logger.info("No qualified leads found. Pipeline complete.")
        return
    
    # Step 7: Company enrichment
    logger.info("Step 7: Enriching company information...")
    enricher = CompanyEnricher()
    for item in qualified_leads:
        enrichment = enricher.enrich(item)
        item.update(enrichment)
    
    # Step 8: Send to Telegram
    logger.info("Step 8: Sending alerts to Telegram...")
    telegram = TelegramService()
    telegram.send_leads(qualified_leads)
    logger.info(f"Successfully sent {len(qualified_leads)} leads to Telegram")
    
    logger.info("Pipeline execution complete!")


if __name__ == "__main__":
    run_pipeline()
