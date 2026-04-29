class LeadScorer:

    def calculate_score(self, item):
        score = 0

        title = item.get("title", "").lower()
        reviews = item.get("reviews", 0) or 0
        rating = item.get("rating", 0) or 0

        # =========================
        # 🔥 INDUSTRY (HIGH VALUE)
        # =========================
        if any(k in title for k in [
            "manufacturer", "factory", "exporter",
            "supplier", "industrial", "fabrication",
            "trader", "wholesaler"
        ]):
            score += 6
        else:
            score -= 3   # not reject, just lower priority

        # =========================
        # 📞 CONTACT (IMPORTANT)
        # =========================
        if item.get("phone"):
            score += 4
        else:
            score -= 2

        # =========================
        # 🌐 WEBSITE (SERIOUS BUSINESS)
        # =========================
        if item.get("website"):
            score += 3

        # =========================
        # 📊 GROWTH SIGNAL
        # =========================
        if 5 <= reviews <= 120:
            score += 5
        elif reviews < 5:
            score += 2
        elif reviews > 300:
            score -= 3

        # =========================
        # ⭐ TRUST
        # =========================
        if rating >= 4:
            score += 2
        elif rating < 3:
            score -= 2

        # =========================
        # 🚫 LOW VALUE FILTER (SOFT)
        # =========================
        if any(k in title for k in [
            "salon", "spa", "gym", "cafe",
            "restaurant", "consultant",
            "digital marketing", "coaching"
        ]):
            score -= 6

        return score
