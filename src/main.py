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
# FETCH
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
# PIPELINE
# ============================================================
def run_pipeline():
    logger.info("🚀 Starting pipeline")

    telegram = TelegramService()
    now = datetime.utcnow()

    # ================= FETCH =================
    items = fetch_maps()

    if now.hour == 0:
        logger.info("🔥 Running full scrape")
        items += fetch_all_sources()

    logger.info(f"Fetched: {len(items)}")

    if not items:
        telegram.send_message("⚠ No data fetched")
        return

    # ================= DEDUP =================
    unique = {}
    for item in items:
        key = (item.get("title", "") + item.get("location", "")).lower().strip()
        unique[key] = item

    items = list(unique.values())

    logger.info(f"After dedup: {len(items)}")

    # ================= LOCATION =================
    location_filter = LocationFilter()

    items = [
        x for x in items
        if location_filter.is_target_location(
            f"{x.get('title','')} {x.get('location','')}"
        )
    ]

    if not items:
        logger.warning("Location fallback used")
        items = list(unique.values())[:30]

    # ================= CONTACT =================
    extractor = ContactExtractor()

    for item in items:
        item.update(extractor.extract(item.get("title", "")))

    # ================= SCORING =================
    scorer = LeadScorer()

    for item in items:
        item["score"] = scorer.calculate_score(item)

    # 🔥 BALANCED FILTER (FIXED)
    items = [x for x in items if x.get("score", 0) >= 6]

    logger.info(f"After scoring filter: {len(items)}")

    if not items:
        telegram.send_message("⚠ No high-quality leads")
        return

    # ================= SORT =================
    items.sort(key=lambda x: x.get("score", 0), reverse=True)

    # ================= LIMIT =================
    items = items[:25]

    random.shuffle(items)

    # ================= FINAL =================
    final = []

    for lead in items:
        lead["id"] = generate_id(lead)
        final.append(lead)

    # Send to sheet
    for lead in final:
        try:
            send_to_sheet(lead)
        except Exception as e:
            logger.warning(f"Sheet error: {e}")

    # Telegram
    telegram.send_leads(final[:10])

    logger.info("🎯 PIPELINE COMPLETE")


# ============================================================
# ENTRY
# ============================================================
if __name__ == "__main__":
    run_pipeline()
