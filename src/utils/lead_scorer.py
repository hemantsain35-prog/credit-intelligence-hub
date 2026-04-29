class LeadScorer:

    def calculate_score(self, item):
        score = 0

        if item.get("phone"):
            score += 5

        if item.get("rating", 0) >= 4:
            score += 3

        if item.get("reviews", 0) and item.get("reviews", 0) < 200:
            score += 2  # small growing business

        title = item.get("title", "").lower()

        if any(k in title for k in ["manufacturer", "trader", "supplier"]):
            score += 3

        return score
