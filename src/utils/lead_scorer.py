class LeadScorer:

    def calculate_score(self, item):
        score = 0

        title = item.get("title", "").lower()
        reviews = item.get("reviews", 0) or 0
        rating = item.get("rating", 0) or 0

        # =========================
        # 🔥 INDUSTRY (MANDATORY)
        # =========================
        if any(k in title for k in [
            "manufacturer", "factory", "exporter",
            "supplier", "industrial", "fabrication",
            "trader", "wholesaler"
        ]):
            score += 8
        else:
            return -100   # reject

        # =========================
        # 📞 PHONE (MANDATORY)
        # =========================
        if item.get("phone"):
            score += 5
        else:
            return -100

        # =========================
        # 🌐 WEBSITE (SERIOUS BUSINESS)
        # =========================
        if item.get("website"):
            score += 3

        # =========================
        # 📊 GROWTH SIGNAL (BEST RANGE)
        # =========================
        if 5 <= reviews <= 120:
            score += 6
        elif reviews < 5:
            score += 2  # very new business
        elif reviews > 300:
            score -= 4  # too big

        # =========================
        # ⭐ TRUST
        # =========================
        if rating >= 3.5:
            score += 2

        # =========================
        # 🚫 REMOVE LOW VALUE
        # =========================
        if any(k in title for k in [
            "salon", "spa", "gym", "cafe",
            "restaurant", "consultant",
            "digital marketing", "coaching"
        ]):
            return -100

        return score
