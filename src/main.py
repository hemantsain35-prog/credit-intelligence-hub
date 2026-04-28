"""Main entry point for B2B lead intelligence pipeline (FINAL PRODUCTION VERSION)."""

from dotenv import load_dotenv
load_dotenv()

import logging
import hashlib

from src.scrapers.indiamart_scraper import IndiaMART
from src.scrapers.tradeindia_scraper import TradeIndia
from src.scrapers.rss_scraper import RssScraper
from src.utils.demand_detector import DemandDetector
from src.utils.location_filter import LocationFilter
from src.utils.contact_extractor import ContactExtractor
from src.utils.lead_scorer import LeadScorer, classify_lead
from src.utils.enrichment import CompanyEnricher
from src.services.telegram_service import TelegramService
from src.services.sheets_webhook import send_to_sheet
from src.utils.dedup_store import load_ids, save_ids, is_new_lead


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
    logger.info("🚀 Starting pipeline")

    telegram = TelegramService()
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
        telegram.send_message("⚠ No data fetched")
        return

    # ============================================================
    # STEP 2: DEDUPLICATION (RUN LEVEL)
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

    if not filtered_items:
        logger.warning("⚠ No location match — fallback used")
        filtered_items = items_with_demand[:15]

    logger.info(f"Location filtered: {len(filtered_items)}")

    # ============================================================
    # STEP 5: CONTACT EXTRACTION
    # ============================================================
    extractor = ContactExtractor()

    for item in filtered_items:
        text = f"{item.get('title','')} {item.get('description','')}"
        item.update(extractor.extract(text))

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
    qualified = [x for x in filtered_items if x.get("score", 0) >= 3]

    if not qualified:
        logger.warning("⚠ No qualified leads — fallback used")
        qualified = filtered_items[:10]

    # ============================================================
    # STEP 9: SORT
    # ============================================================
    qualified.sort(key=lambda x: x.get("score", 0), reverse=True)
    top_leads = qualified[:10]

    # ============================================================
    # STEP 10: SMART FALLBACK (ENSURE 10–15 LEADS)
    # ============================================================
    if len(top_leads) < 10:
        logger.warning("⚠ Low leads — filling fallback")

        existing_urls = {x.get("url") for x in top_leads}

        fallback = [
            x for x in items_with_demand
            if x.get("funding_intent") and x.get("url") not in existing_urls
        ]

        fallback.sort(key=lambda x: x.get("score", 0), reverse=True)

        top_leads.extend(fallback)
        top_leads.sort(key=lambda x: x.get("score", 0), reverse=True)

        top_leads = top_leads[:15]

    logger.info(f"Final leads count: {len(top_leads)}")

    # ============================================================
    # STEP 11: PERMANENT DEDUP (ACROSS DAYS)
    # ============================================================
    seen_ids = load_ids()
    final_leads = []

    for lead in top_leads:
        lead_id = generate_id(lead)

        if is_new_lead(lead_id, seen_ids):
            lead["id"] = lead_id
            final_leads.append(lead)
            seen_ids.add(lead_id)

    save_ids(seen_ids)
    top_leads = final_leads

    logger.info(f"After permanent dedup: {len(top_leads)}")

    if not top_leads:
        telegram.send_message("⚠ All leads already processed")
        return

    # ============================================================
    # STEP 12: SAVE TO SHEET
    # ============================================================
    for lead in top_leads:
        try:
            send_to_sheet(lead)
        except Exception as e:
            logger.warning(f"Sheet error: {e}")

    # ============================================================
    # STEP 13: TELEGRAM
    # ============================================================
    success = telegram.send_leads(top_leads)

    if success:
        logger.info("✅ Telegram sent")
    else:
        logger.error("❌ Telegram failed")

    logger.info("🎯 PIPELINE COMPLETE")


# ============================================================
# ENTRY POINT
# ============================================================
if __name__ == "__main__":
    print("🔥 FINAL PRODUCTION SYSTEM LIVE")
    run_pipeline()
