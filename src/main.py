"""Main entry point for B2B lead intelligence pipeline (FINAL BUSINESS VERSION)."""

from dotenv import load_dotenv
load_dotenv()

import logging
import hashlib
import random

from src.scrapers.indiamart_scraper import IndiaMART
from src.scrapers.tradeindia_scraper import TradeIndia
from src.scrapers.justdial_scraper import JustdialScraper
from src.scrapers.google_maps_scraper import GoogleMapsScraper

from src.utils.demand_detector import DemandDetector
from src.utils.location_filter import LocationFilter
from src.utils.contact_extractor import ContactExtractor
from src.utils.lead_scorer import LeadScorer, classify_lead
from src.utils.enrichment import CompanyEnricher

from src.services.telegram_service import TelegramService
from src.services.sheets_webhook import send_to_sheet

from src.utils.dedup_store import load_ids, save_ids


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
        key = item.get("url") or item.get("title")

        if key and key not in seen:
            seen.add(key)
            unique.append(item)

    return unique


def generate_id(item):
    """Strong ID to prevent duplicate leads"""
    text = (
        item.get("title", "") +
        item.get("company", "") +
        item.get("location", "") +
        item.get("phone", "")
    ).lower().strip()

    return hashlib.md5(text.encode()).hexdigest()


# ============================================================
# MAIN PIPELINE
# ============================================================
def run_pipeline():
    logger.info("🚀 Starting pipeline")

    telegram = TelegramService()
    telegram.send_message("🚀 Pipeline started")

    # ============================================================
    # STEP 1: FETCH DATA (NO RSS)
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
        justdial_items = JustdialScraper().fetch_all()
    except Exception as e:
        logger.error(f"Justdial error: {e}")
        justdial_items = []

    try:
        maps_items = GoogleMapsScraper().fetch_all()
    except Exception as e:
        logger.error(f"Google Maps error: {e}")
        maps_items = []

    # 🔥 FINAL SOURCES (NO NEWS)
    all_items = indiamart_items + tradeindia_items + justdial_items + maps_items
    logger.info(f"Total items fetched: {len(all_items)}")

    if not all_items:
        telegram.send_message("⚠ No data fetched")
        return

    # ============================================================
    # STEP 2: DEDUP
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
    # STEP 4: LOCATION FILTER
    # ============================================================
    location_filter = LocationFilter()

    filtered_items = [
        item for item in items_with_demand
        if location_filter.is_target_location(
            f"{item.get('title','')} {item.get('description','')} {item.get('location','')}"
        )
    ]

    # fallback
    if len(filtered_items) < 10:
        logger.warning("⚠ Expanding location filter")
        filtered_items = items_with_demand[:30]

    logger.info(f"Location filtered: {len(filtered_items)}")

    # ============================================================
    # STEP 5: CONTACT EXTRACTION
    # ============================================================
    extractor = ContactExtractor()

    for item in filtered_items:
        text = f"{item.get('title','')} {item.get('description','')}"
        item.update(extractor.extract(text))

    # 🔥 ONLY KEEP CALLABLE LEADS
    filtered_items = [
        x for x in filtered_items
        if x.get("phone")
    ]

    logger.info(f"After contact filter: {len(filtered_items)}")

    if not filtered_items:
        telegram.send_message("⚠ No callable leads found")
        return

    # ============================================================
    # STEP 6: ENRICHMENT
    # ============================================================
    enricher = CompanyEnricher()

    for item in filtered_items:
        item.update(enricher.enrich(item))

    # ============================================================
    # STEP 7: SCORING + CLASSIFICATION
    # ============================================================
    scorer = LeadScorer()

    for item in filtered_items:
        item["score"] = scorer.calculate_score(item)
        item["lead_type"] = classify_lead(item)

    # ============================================================
    # STEP 8: FILTER
    # ============================================================
    qualified = [x for x in filtered_items if x.get("score", 0) >= 2]

    if not qualified:
        qualified = filtered_items[:15]

    # ============================================================
    # STEP 9: SORT + RANDOM
    # ============================================================
    qualified.sort(key=lambda x: x.get("score", 0), reverse=True)
    top_leads = qualified[:25]

    random.shuffle(top_leads)

    # ============================================================
    # STEP 10: FINAL DEDUP (NO REPEAT)
    # ============================================================
    seen_ids = load_ids()
    final_leads = []

    for lead in top_leads:
        lead_id = generate_id(lead)

        if lead_id not in seen_ids:
            lead["id"] = lead_id
            final_leads.append(lead)
            seen_ids.add(lead_id)

    save_ids(seen_ids)

    if not final_leads:
        telegram.send_message("⚠ No new leads today")
        return

    final_leads = final_leads[:15]

    logger.info(f"Final leads count: {len(final_leads)}")

    # ============================================================
    # STEP 11: SAVE TO SHEET
    # ============================================================
    for lead in final_leads:
        try:
            send_to_sheet(lead)
        except Exception as e:
            logger.warning(f"Sheet error: {e}")

    # ============================================================
    # STEP 12: TELEGRAM
    # ============================================================
    success = telegram.send_leads(final_leads)

    if success:
        logger.info("✅ Telegram sent")
    else:
        logger.error("❌ Telegram failed")

    logger.info("🎯 PIPELINE COMPLETE")


# ============================================================
# ENTRY POINT
# ============================================================
if __name__ == "__main__":
    print("🔥 BUSINESS LEAD SYSTEM LIVE")
    run_pipeline()
