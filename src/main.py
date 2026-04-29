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
from src.utils.corporate_enricher import CorporateEnricher
from src.utils.growth_detector import GrowthDetector
from src.utils.gst_verifier import GSTVerifier

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

    # ============================================================
    # STEP 1: FETCH DATA
    # ============================================================
    try:
        indiamart_items = IndiaMART().fetch_all()
    except:
        indiamart_items = []

    try:
        tradeindia_items = TradeIndia().fetch_all()
    except:
        tradeindia_items = []

    try:
        justdial_items = JustdialScraper().fetch_all()
    except:
        justdial_items = []

    try:
        maps_items = GoogleMapsScraper().fetch_all()
    except:
        maps_items = []

    all_items = indiamart_items + tradeindia_items + justdial_items + maps_items

    if not all_items:
        telegram.send_message("⚠ No data fetched")
        return

    # ============================================================
    # STEP 2: DEDUP
    # ============================================================
    unique_items = deduplicate_items(all_items)

    # ============================================================
    # STEP 3: DEMAND HANDLING
    # ============================================================
    detector = DemandDetector()
    processed = []

    for item in unique_items:
        source = item.get("source", "").lower()

        if source in ["googlemaps", "justdial"]:
            processed.append(item)
        else:
            result = detector.analyze(item)
            if result.get("is_demand"):
                item.update(result)
                processed.append(item)

    if not processed:
        telegram.send_message("⚠ No leads found")
        return

    # ============================================================
    # STEP 4: LOCATION FILTER
    # ============================================================
    location_filter = LocationFilter()

    filtered = [
        x for x in processed
        if location_filter.is_target_location(
            f"{x.get('title','')} {x.get('description','')} {x.get('location','')}"
        )
    ]

    if len(filtered) < 10:
        filtered = processed[:30]

    # ============================================================
    # STEP 5: CONTACT EXTRACTION
    # ============================================================
    extractor = ContactExtractor()

    for item in filtered:
        text = f"{item.get('title','')} {item.get('description','')}"
        item.update(extractor.extract(text))

    # ONLY CALLABLE
    filtered = [x for x in filtered if x.get("phone")]

    if not filtered:
        telegram.send_message("⚠ No callable leads")
        return

    # ============================================================
    # STEP 6: ENRICHMENT
    # ============================================================
    enricher = CompanyEnricher()
    corporate = CorporateEnricher()
    growth = GrowthDetector()
    gst = GSTVerifier()

    for item in filtered:
        item.update(enricher.enrich(item))
        item.update(corporate.enrich(item))
        item.update(growth.detect(item))
        item.update(gst.verify(item))

    # ============================================================
    # STEP 7: SCORING
    # ============================================================
    scorer = LeadScorer()

    for item in filtered:
        item["score"] = scorer.calculate_score(item)
        item["lead_type"] = classify_lead(item)

    # ============================================================
    # STEP 8: FILTER + SORT
    # ============================================================
    qualified = [x for x in filtered if x.get("score", 0) >= 2]

    qualified.sort(key=lambda x: x.get("score", 0), reverse=True)

    random.shuffle(qualified)

    # ============================================================
    # STEP 9: FINAL DEDUP
    # ============================================================
    seen_ids = load_ids()
    final = []

    for lead in qualified:
        lead_id = generate_id(lead)

        if lead_id not in seen_ids:
            lead["id"] = lead_id
            final.append(lead)
            seen_ids.add(lead_id)

    save_ids(seen_ids)

    if not final:
        telegram.send_message("⚠ No new leads today")
        return

    final = final[:15]

    # ============================================================
    # STEP 10: SAVE + SEND
    # ============================================================
    for lead in final:
        send_to_sheet(lead)

    telegram.send_leads(final)

    logger.info("🎯 PIPELINE COMPLETE")


# ============================================================
# ENTRY POINT
# ============================================================
if __name__ == "__main__":
    print("🔥 FINAL SYSTEM LIVE")
    run_pipeline()
