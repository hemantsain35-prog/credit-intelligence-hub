import re


class DemandDetector:
    """Detects real demand + funding intent + extracts deal value"""

    # 🔥 HIGH-INTENT (Loan / Funding signals)
    FUNDING_KEYWORDS = [
        "working capital",
        "business loan",
        "loan required",
        "need loan",
        "looking for finance",
        "credit facility",
        "cash flow issue",
        "short term funding",
        "invoice discounting",
        "bill discounting",
        "overdraft",
        "od limit",
        "cc limit",
        "inventory financing",
        "purchase financing",
        "expansion funding",
        "project funding"
    ]

    # 🔥 DEMAND KEYWORDS (General business demand)
    DEMAND_KEYWORDS = [
        "require supplier",
        "need supplier",
        "bulk order",
        "urgent requirement",
        "looking for vendor",
        "rfq",
        "tender",
        "quotation required",
        "purchase requirement",
        "buy requirement"
    ]

    # 💰 VALUE patterns
    VALUE_PATTERNS = [
        r"₹\s?(\d+)\s?(lakh|lac|lacs|lakhs)",
        r"₹\s?(\d+)\s?(crore|cr)",
        r"(\d+)\s?(lakh|lac|lacs|lakhs)",
        r"(\d+)\s?(crore|cr)"
    ]

    def analyze(self, item):
        """Main analysis function"""

        text = (
            (item.get("title", "") + " " + item.get("description", ""))
            .lower()
        )

        funding_score = self._detect_funding_intent(text)
        demand_score = self._detect_general_demand(text)
        value = self._extract_value(text)

        is_demand = funding_score > 0 or demand_score > 0

        return {
            "is_demand": is_demand,
            "funding_intent": funding_score > 0,
            "funding_score": funding_score,
            "demand_score": demand_score,
            "numeric_value": value
        }

    # ------------------------------------------------------------
    # 🔥 FUNDING DETECTION (MOST IMPORTANT)
    # ------------------------------------------------------------
    def _detect_funding_intent(self, text):
        score = 0

        for keyword in self.FUNDING_KEYWORDS:
            if keyword in text:
                score += 2   # higher weight

        return score

    # ------------------------------------------------------------
    # 🔍 GENERAL DEMAND
    # ------------------------------------------------------------
    def _detect_general_demand(self, text):
        score = 0

        for keyword in self.DEMAND_KEYWORDS:
            if keyword in text:
                score += 1

        return score

    # ------------------------------------------------------------
    # 💰 VALUE EXTRACTION
    # ------------------------------------------------------------
    def _extract_value(self, text):
        for pattern in self.VALUE_PATTERNS:
            match = re.search(pattern, text)

            if match:
                number = int(match.group(1))
                unit = match.group(2)

                if "cr" in unit:
                    return number * 100   # convert to lakh
                else:
                    return number

        return 0
