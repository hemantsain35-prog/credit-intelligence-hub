from dotenv import load_dotenv
load_dotenv()

import logging
import hashlib
import random

from src.scrapers.google_maps_scraper import GoogleMapsScraper
from src.utils.location_filter import LocationFilter
from src.utils.contact_extractor import ContactExtractor
from src.utils.lead_scorer import LeadScorer
from src.services.telegram_service import TelegramService
from src.services.sheets_webhook import send_to_sheet


# ============================================================
# LOGGING
# ============================================================
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# ============================================================
# UNIQUE ID
# ============================================================
def generate_id(item):
    text = (
        item.get("title", "") +
        item.get("location", "")
    ).lower().strip()

    return hashlib.md5(text.encode()).hexdigest()


# ============================================================
# MAIN PIPELINE
# ============================================================
def run_pipeline():
    logger.info("🚀 Starting pipeline")

    telegram = TelegramService()

    # ============================================================
    # STEP 1: FETCH (Google Maps API)
    # ============================================================
    try:
        items = GoogleMapsScraper().fetch_all()
    except Exception as e:
        logger.error(f"Maps error: {e}")
        items = []

    logger.info(f"Fetched: {len(items)}")

    if not items:
        telegram.send_message("⚠ No data fetched")
        return

    # ============================================================
    # STEP 2: REMOVE DUPLICATES (same run)
    # ============================================================
    unique = {}
    for item in items:
        key = (item.get("title", "") + item.get("location", "")).lower().strip()
        unique[key] = item

    items = list(unique.values())

    logger.info(f"After dedup: {len(items)}")

    # ============================================================
    # STEP 3: LOCATION FILTER
    # ============================================================
    location_filter = LocationFilter()

    filtered = [
        x for x in items
        if location_filter.is_target_location(
            f"{x.get('title','')} {x.get('location','')}"
        )
    ]

    if not filtered:
        logger.warning("⚠ Location fallback used")
        filtered = items[:30]

    # ============================================================
    # STEP 4: CONTACT EXTRACTION
    # ============================================================
    extractor = ContactExtractor()

    for item in filtered:
        text = f"{item.get('title','')}"
        item.update(extractor.extract(text))

    # ============================================================
    # STEP 5: PRIORITIZE PHONE LEADS (BUT KEEP ALL)
    # ============================================================
    callable_leads = [x for x in filtered if x.get("phone")]
    non_callable = [x for x in filtered if not x.get("phone")]

    items = callable_leads + non_callable

    logger.info(f"With phone: {len(callable_leads)} | Without phone: {len(non_callable)}")

    # ============================================================
    # STEP 6: SCORING
    # ============================================================
    scorer = LeadScorer()

    for item in items:
        item["score"] = scorer.calculate_score(item)

    # Sort best first
    items.sort(key=lambda x: x.get("score", 0), reverse=True)

    # ============================================================
    # STEP 7: LIMIT TOP 25
    # ============================================================
    items = items[:25]

    # Slight shuffle to avoid same ordering daily
    random.shuffle(items)

    # ============================================================
    # STEP 8: FINAL FORMAT + SEND
    # ============================================================
    final = []

    for lead in items:
        lead["id"] = generate_id(lead)
        final.append(lead)

    if not final:
        telegram.send_message("⚠ No leads ready")
        return

    # Send to sheet
    for lead in final:
        try:
            send_to_sheet(lead)
        except Exception as e:
            logger.warning(f"Sheet error: {e}")

    # Send to Telegram
    telegram.send_leads(final[:10])

    logger.info("🎯 PIPELINE COMPLETE")


# ============================================================
# ENTRY
# ============================================================
if __name__ == "__main__":
    run_pipeline()
