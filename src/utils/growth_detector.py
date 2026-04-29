class GrowthDetector:
    """Detect fast-growing companies"""

    def detect(self, item):
        text = f"{item.get('title','')} {item.get('description','')}".lower()

        growth_keywords = [
            "expansion",
            "new unit",
            "new plant",
            "increase production",
            "scaling",
            "growing",
            "bulk order",
            "large order",
            "new project",
            "capacity expansion"
        ]

        item["growth_signal"] = any(word in text for word in growth_keywords)

        return item
