class LeadScorer:

    def calculate_score(self, item):
        score = 0

        # Phone priority
        if item.get("phone"):
            score += 5
        else:
            score += 1  # don't eliminate lead

        # Rating
        if item.get("rating", 0) >= 4:
            score += 3

        # Small growing business
        reviews = item.get("reviews", 0)
        if reviews and reviews < 200:
            score += 2

        # Business type keywords
        title = item.get("title", "").lower()

        if any(k in title for k in ["manufacturer", "trader", "supplier", "wholesaler"]):
            score += 3

        return score
