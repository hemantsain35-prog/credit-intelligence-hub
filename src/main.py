"""Main entry point for B2B lead intelligence pipeline (FINAL STABLE VERSION)."""

from dotenv import load_dotenv

load_dotenv()

import logging
import hashlib
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
# OPTIONAL: Google Sheet webhook
from src.services.sheets_webhook import send_to_sheet


# ============================================================
# LOGGING
# ============================================================
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# ============================================================
# HELPERS
# ============================================================
def deduplicate_items(items):
    seen = set()
    unique = []

    for item in items:
        url = item.get("url", "")
        if url and url not in seen:
            seen.add(url)
            unique.append(item)
        elif not url:
            unique.append(item)

    return unique


def generate_id(item):
    text = (item.get("title", "") + item.get("url", "")).strip()
    return hashlib.md5(text.encode()).hexdigest()


# ============================================================
# MAIN PIPELINE
# ============================================================

    def run_pipeline():
    logger.info("Starting pipeline")

    telegram = TelegramService()

    # ✅ CORRECT PLACE
    telegram.send_message("🔥 TEST MESSAGE FROM GITHUB ACTION")

    telegram.send_message("🚀 Pipeline started")

    # ============================================================
    # STEP 1: FETCH DATA
    # ============================================================
    logger.info("Step 1: Fetching data...")

    try:
        indiamart_items = IndiaMART().fetch_all()
    except Exception as e:
        logger.error(f"IndiaMART error: {e}")
        indiamart_items = []

    try:
        tradeindia_items = TradeIndia().fetch_all()
    except Exception as e:
        logger.error(f"TradeIndia error: {e}")
        tradeindia_items = []

    try:
        rss_items = RssScraper().fetch_all()
    except Exception as e:
        logger.error(f"RSS error: {e}")
        rss_items = []

    all_items = indiamart_items + tradeindia_items + rss_items
    logger.info(f"Total items fetched: {len(all_items)}")

    if not all_items:
        telegram.send_message("⚠ No data fetched from any source")
        return

    # ============================================================
    # STEP 2: DEDUPLICATION
    # ============================================================
    unique_items = deduplicate_items(all_items)
    logger.info(f"After deduplication: {len(unique_items)}")

    # ============================================================
    # STEP 3: DEMAND DETECTION
    # ============================================================
    detector = DemandDetector()
    items_with_demand = []

    for item in unique_items:
        result = detector.analyze(item)
        if result.get("is_demand"):
            item.update(result)
            items_with_demand.append(item)

    logger.info(f"Demand items: {len(items_with_demand)}")

    if not items_with_demand:
        telegram.send_message("⚠ No demand detected")
        return

    # ============================================================
    # STEP 4: VALUE FILTER (TEMP DISABLED FOR DEBUG)
    # ============================================================
    high_value_items = items_with_demand
    logger.info(f"High value items (debug mode): {len(high_value_items)}")

    # ============================================================
    # STEP 5: LOCATION FILTER (RELAXED)
    # ============================================================
    location_filter = LocationFilter()

    gurgaon_items = [
        item for item in high_value_items
        if location_filter.is_gurgaon(item.get("title", "")) or
           location_filter.is_gurgaon(item.get("description", "")) or
           location_filter.is_gurgaon(item.get("location", ""))
    ]

    if not gurgaon_items:
        logger.warning("No Gurgaon leads — using fallback")
        gurgaon_items = high_value_items[:5]

    logger.info(f"Location filtered items: {len(gurgaon_items)}")

    # ============================================================
    # STEP 6: CONTACT EXTRACTION
    # ============================================================
    extractor = ContactExtractor()

    for item in gurgaon_items:
        text = f"{item.get('title', '')} {item.get('description', '')}"
        item.update(extractor.extract(text))

    # ============================================================
    # STEP 7: ENRICHMENT
    # ============================================================
    enricher = CompanyEnricher()

    for item in gurgaon_items:
        item.update(enricher.enrich(item))

    # ============================================================
    # STEP 8: SCORING
    # ============================================================
    scorer = LeadScorer()

    for item in gurgaon_items:
        item["score"] = scorer.calculate_score(item)

    # ============================================================
    # STEP 9: FINAL FILTER (RELAXED)
    # ============================================================
    qualified = [x for x in gurgaon_items if x.get("score", 0) >= 5]

    if not qualified:
        logger.warning("No qualified leads — using fallback")
        qualified = gurgaon_items[:5]

    # ============================================================
    # STEP 10: SORT
    # ============================================================
    qualified.sort(key=lambda x: x.get("score", 0), reverse=True)
    top_leads = qualified[:10]

    # ============================================================
    # STEP 11: SAVE TO SHEET
    # ============================================================
    for lead in top_leads:
        lead["id"] = generate_id(lead)
        try:
            send_to_sheet(lead)
        except Exception as e:
            logger.warning(f"Sheet error: {e}")

    # ============================================================
    # STEP 12: TELEGRAM SEND
    # ============================================================
    success = telegram.send_leads(top_leads)

    if success:
        logger.info("✅ Telegram sent successfully")
    else:
        logger.error("❌ Telegram failed")

    logger.info("🎯 PIPELINE COMPLETE")


# ============================================================
# ENTRY POINT
# ============================================================
if __name__ == "__main__":
    print("🔥 NEW VERSION DEPLOYED")
    run_pipeline()
