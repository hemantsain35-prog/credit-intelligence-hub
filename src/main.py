from dotenv import load_dotenv
load_dotenv()

import logging
import hashlib
import random
from datetime import datetime

from src.scrapers.google_maps_scraper import GoogleMapsScraper
from src.scrapers.indiamart_scraper import IndiaMART
from src.scrapers.tradeindia_scraper import TradeIndia
from src.scrapers.justdial_scraper import JustdialScraper

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
# FETCH FUNCTIONS
# ============================================================
def fetch_maps():
    try:
        return GoogleMapsScraper().fetch_all()
    except Exception as e:
        logger.warning(f"Maps error: {e}")
        return []


def fetch_all_sources():
    items = []

    try:
        items += IndiaMART().fetch_all()
    except:
        logger.warning("IndiaMART failed")

    try:
        items += TradeIndia().fetch_all()
    except:
        logger.warning("TradeIndia failed")

    try:
        items += JustdialScraper().fetch_all()
    except:
        logger.warning("Justdial failed")

    return items


# ============================================================
# MAIN PIPELINE
# ============================================================
def run_pipeline():
    logger.info("🚀 Starting pipeline")

    telegram = TelegramService()

    now = datetime.utcnow()

    # ============================================================
    # STEP 1: FETCH DATA
    # ============================================================
    items = fetch_maps()

    # Daily deep scrape (once per day at ~UTC 00)
    if now.hour == 0:
        logger.info("🔥 Running full scraper (daily)")
        items += fetch_all_sources()

    logger.info(f"Fetched: {len(items)}")

    if not items:
        telegram.send_message("⚠ No data fetched")
        return

    # ============================================================
    # STEP 2: DEDUP (same run)
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

    items = [
        x for x in items
        if location_filter.is_target_location(
            f"{x.get('title','')} {x.get('location','')}"
        )
    ]

    if not items:
        telegram.send_message("⚠ No location matched")
        return

    # ============================================================
    # STEP 4: CONTACT EXTRACTION
    # ============================================================
    extractor = ContactExtractor()

    for item in items:
        item.update(extractor.extract(item.get("title", "")))

    # ============================================================
    # STEP 5: SCORING (HIGH + ULTRA)
    # ============================================================
    scorer = LeadScorer()

    for item in items:
        item["score"] = scorer.calculate_score(item)

    # 🔥 FINAL FILTER
    items = [x for x in items if x.get("score", 0) >= 12]

    logger.info(f"After scoring filter: {len(items)}")

    if not items:
        telegram.send_message("⚠ No high-quality leads")
        return

    # ============================================================
    # STEP 6: SORT + LIMIT
    # ============================================================
    items.sort(key=lambda x: x.get("score", 0), reverse=True)

    items = items[:25]  # top 25 only

    random.shuffle(items)  # avoid same ordering

    # ============================================================
    # STEP 7: FINAL OUTPUT
    # ============================================================
    final = []

    for lead in items:
        lead["id"] = generate_id(lead)
        final.append(lead)

    # Send to Google Sheet
    for lead in final:
        try:
            send_to_sheet(lead)
        except Exception as e:
            logger.warning(f"Sheet error: {e}")

    # Send top 10 to Telegram
    telegram.send_leads(final[:10])

    logger.info("🎯 PIPELINE COMPLETE")


# ============================================================
# ENTRY
# ============================================================
if __name__ == "__main__":
    run_pipeline()
