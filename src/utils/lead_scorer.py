class LeadScorer:

    def calculate_score(self, item):
        score = 0

        title = item.get("title", "").lower()
        reviews = item.get("reviews", 0) or 0
        rating = item.get("rating", 0) or 0

        # INDUSTRY
        if any(k in title for k in [
            "manufacturer", "factory", "supplier",
            "industrial", "fabrication", "trader"
        ]):
            score += 5
        else:
            score -= 2

        # PHONE
        if item.get("phone"):
            score += 4

        # WEBSITE
        if item.get("website"):
            score += 2

        # REVIEWS
        if 5 <= reviews <= 120:
            score += 4
        elif reviews > 300:
            score -= 2

        # RATING
        if rating >= 4:
            score += 2

        # LOW VALUE BUSINESSES (SOFT FILTER)
        if any(k in title for k in [
            "salon", "spa", "gym", "cafe",
            "restaurant", "consultant"
        ]):
            score -= 4

        return score
