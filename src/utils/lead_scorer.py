"""Lead scoring logic (FINAL PRODUCTION VERSION)."""

import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)


class LeadScorer:
    """Scores leads based on business + funding signals (0–25 scale)."""

    def calculate_score(self, item: Dict[str, Any]) -> int:
        score = 0

        # ============================================================
        # 🔥 FUNDING INTENT (highest priority)
        # ============================================================
        if item.get("funding_intent"):
            score += 6

        # ============================================================
        # 💰 DEAL VALUE
        # ============================================================
        value = item.get("numeric_value", 0)

        if value >= 500:
            score += 5
        elif value >= 100:
            score += 3
        elif value >= 50:
            score += 1

        # ============================================================
        # 📈 DEMAND SIGNAL
        # ============================================================
        if item.get("is_demand"):
            score += 3

        # ============================================================
        # ⚡ URGENCY
        # ============================================================
        if item.get("has_urgency"):
            score += 4

        # ============================================================
        # 🏗 PROJECT / CONTRACT
        # ============================================================
        text = f"{item.get('title','')} {item.get('description','')}".lower()

        if any(word in text for word in ["project", "contract", "tender", "requirement"]):
            score += 2

        # ============================================================
        # 📞 CONTACT (VERY IMPORTANT)
        # ============================================================
        if item.get("phone"):
            score += 7   # 🔥 strongest practical signal

        if item.get("email"):
            score += 2

        # ============================================================
        # 🏢 CORPORATE SIGNALS
        # ============================================================
        if item.get("is_registered"):
            score += 2

        if item.get("industry") == "manufacturing":
            score += 3

        if item.get("funding_signal"):
            score += 4

        if item.get("new_business"):
            score += 2

        # ============================================================
        # 🧾 GST VERIFIED
        # ============================================================
        if item.get("gst_verified"):
            score += 3

        # ============================================================
        # 📈 GROWTH SIGNAL
        # ============================================================
        if item.get("growth_signal"):
            score += 4

        return min(score, 25)


# ============================================================
# 🔥 CLASSIFICATION
# ============================================================
def classify_lead(item: Dict[str, Any]) -> str:
    score = item.get("score", 0)
    funding = item.get("funding_intent", False)

    if funding and score >= 8:
        return "🔥 HOT"
    elif score >= 4:
        return "🟡 WARM"
    else:
        return "❄️ COLD"
