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
from src.utils.dedup_store import load_ids, save_ids


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def generate_id(item):
    text = (
        item.get("title", "") +
        item.get("location", "") +
        str(item.get("phone", ""))
    ).lower()

    return hashlib.md5(text.encode()).hexdigest()


def run_pipeline():
    logger.info("🚀 Starting pipeline")

    telegram = TelegramService()

    # ================= FETCH =================
    try:
        items = GoogleMapsScraper().fetch_all()
    except Exception as e:
        logger.error(f"Maps error: {e}")
        items = []

    logger.info(f"GoogleMaps: {len(items)}")

    if not items:
        telegram.send_message("⚠ No data fetched")
        return

    # ================= LOCATION =================
    location_filter = LocationFilter()

    items = [
        x for x in items
        if location_filter.is_target_location(
            f"{x.get('title','')} {x.get('location','')}"
        )
    ]

    if not items:
        items = items[:20]

    # ================= CONTACT =================
    extractor = ContactExtractor()

    for item in items:
        text = f"{item.get('title','')}"
        item.update(extractor.extract(text))

    # keep only callable
    items = [x for x in items if x.get("phone")]

    if not items:
        telegram.send_message("⚠ No callable leads")
        return

    # ================= SCORING =================
    scorer = LeadScorer()

    for item in items:
        item["score"] = scorer.calculate_score(item)

    items.sort(key=lambda x: x.get("score", 0), reverse=True)
    random.shuffle(items)

    # ================= DEDUP =================
    seen = load_ids()
    final = []

    for lead in items:
        lead_id = generate_id(lead)

        if lead_id not in seen:
            lead["id"] = lead_id
            final.append(lead)
            seen.add(lead_id)

    save_ids(seen)

    if not final:
        telegram.send_message("⚠ No new leads")
        return

    final = final[:15]

    # ================= OUTPUT =================
    for lead in final:
        send_to_sheet(lead)

    telegram.send_leads(final)

    logger.info("🎯 COMPLETE")


if __name__ == "__main__":
    run_pipeline()
