import re


class CorporateEnricher:
    """Adds corporate signals (MCA/GST/Zauba style intelligence)."""

    def enrich(self, item: dict) -> dict:
        text = f"{item.get('title','')} {item.get('company','')}".lower()

        # ============================================================
        # 🏢 COMPANY TYPE DETECTION
        # ============================================================
        if "private limited" in text or "pvt ltd" in text:
            item["company_type"] = "pvt_ltd"
            item["is_registered"] = True

        elif "llp" in text:
            item["company_type"] = "llp"
            item["is_registered"] = True

        elif "proprietor" in text or "traders" in text:
            item["company_type"] = "proprietorship"
            item["is_registered"] = False

        else:
            item["company_type"] = "unknown"

        # ============================================================
        # 📊 INDUSTRY SIGNAL
        # ============================================================
        if any(word in text for word in ["manufacturing", "factory", "plant"]):
            item["industry"] = "manufacturing"
        elif any(word in text for word in ["trader", "supplier", "wholesale"]):
            item["industry"] = "trading"
        else:
            item["industry"] = "general"

        # ============================================================
        # 💰 FUNDING NEED SIGNAL (VERY IMPORTANT)
        # ============================================================
        if any(word in text for word in [
            "expansion", "requirement", "bulk", "project",
            "urgent", "tender", "supply", "order"
        ]):
            item["funding_signal"] = True
        else:
            item["funding_signal"] = False

        # ============================================================
        # 🧾 GST DETECTION (simple pattern)
        # ============================================================
        gst_pattern = r"\b\d{2}[A-Z]{5}\d{4}[A-Z]{1}[A-Z\d]{1}[Z]{1}[A-Z\d]{1}\b"

        combined_text = f"{item.get('description','')} {item.get('title','')}"

        if re.search(gst_pattern, combined_text):
            item["gst_detected"] = True
        else:
            item["gst_detected"] = False

        # ============================================================
        # 🆕 NEW BUSINESS SIGNAL (Google Maps)
        # ============================================================
        reviews = item.get("reviews", 0)

        if reviews and reviews < 10:
            item["new_business"] = True
        else:
            item["new_business"] = False

        return item
