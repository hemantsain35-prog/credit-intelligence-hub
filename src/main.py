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


# ================= ID =================
def generate_id(item):
    text = (
        item.get("title", "") +
        item.get("location", "") +
        str(item.get("phone", ""))
    ).lower()

    return hashlib.md5(text.encode()).hexdigest()


# ================= PIPELINE =================
def run_pipeline():
    logger.info("🚀 Starting pipeline")

    telegram = TelegramService()

    # ================= FETCH =================
    try:
        items = GoogleMapsScraper().fetch_all()
    except Exception as e:
        logger.error(f"Maps error: {e}")
        items = []

    logger.info(f"GoogleMaps fetched: {len(items)}")

    if not items:
        telegram.send_message("⚠ No data fetched")
        return

    # ================= LOCATION =================
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

    # ================= CONTACT =================
    extractor = ContactExtractor()

    for item in filtered:
        text = f"{item.get('title','')}"
        item.update(extractor.extract(text))

    # ================= FIX: KEEP ALL LEADS =================
    callable_leads = [x for x in filtered if x.get("phone")]
    non_callable = [x for x in filtered if not x.get("phone")]

    # priority to phone leads but don't drop others
    items = callable_leads + non_callable

    logger.info(f"With phone: {len(callable_leads)} | Without phone: {len(non_callable)}")

    # limit size
    items = items[:30]

    if not items:
        telegram.send_message("⚠ No leads after filtering")
        return

    # ================= SCORING =================
    scorer = LeadScorer()

    for item in items:
        item["score"] = scorer.calculate_score(item)

    # sort + slight shuffle to avoid repetition
    items.sort(key=lambda x: x.get("score", 0), reverse=True)
    items = items[:20]
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
        try:
            send_to_sheet(lead)
        except Exception as e:
            logger.warning(f"Sheet error: {e}")

    telegram.send_leads(final)

    logger.info("🎯 PIPELINE COMPLETE")


# ================= ENTRY =================
if __name__ == "__main__":
    run_pipeline()
