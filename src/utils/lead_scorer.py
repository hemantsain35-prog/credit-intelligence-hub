"""Lead scoring logic (FINAL PRODUCTION VERSION)."""

import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)


class LeadScorer:
    """Scores leads based on multiple factors (0-25 scale)."""

    def calculate_score(self, item: Dict[str, Any]) -> int:
        score = 0

        # ============================================================
        # 🔥 FUNDING INTENT (MOST IMPORTANT)
        # ============================================================
        if item.get("funding_intent"):
            score += 6   # 🔥 Strong boost

        # ============================================================
        # 💰 DEAL VALUE
        # ============================================================
        numeric_value = item.get("numeric_value", 0)

        if numeric_value >= 500:
            score += 5   # very high deal
        elif numeric_value >= 100:
            score += 3
        elif numeric_value >= 50:
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
        # 🏗 PROJECT / CONTRACT SIGNAL
        # ============================================================
        text = f"{item.get('title','')} {item.get('description','')}".lower()

        if any(word in text for word in ["project", "contract", "tender", "requirement"]):
            score += 2

        # ============================================================
        # 📞 CONTACT (VERY IMPORTANT)
        # ============================================================
        if item.get("phone"):
            score += 5

        if item.get("email"):
            score += 2

        # ============================================================
        # 🧾 BUSINESS LEGIT SIGNALS
        # ============================================================
        if item.get("gst_active"):
            score += 2

        if item.get("msme_signal"):
            score += 1

        # ============================================================
        # 🔒 FINAL CAP
        # ============================================================
        return min(score, 25)


# ============================================================
# 🔥 CLASSIFICATION (IMPORTANT)
# ============================================================
def classify_lead(item: Dict[str, Any]) -> str:
    score = item.get("score", 0)
    funding = item.get("funding_intent", False)

    if funding and score >= 7:
        return "🔥 HOT"
    elif score >= 4:
        return "🟡 WARM"
    else:
        return "❄️ COLD"
