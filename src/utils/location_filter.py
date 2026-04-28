import re


class LocationFilter:
    """Advanced location detection with regex + pincode + district mapping"""

    TARGET_KEYWORDS = [
        "gurgaon", "gurugram", "ggn",
        "sohna", "manesar",
        "rewari", "nuh", "mewat"
    ]

    # Haryana pincodes (major regions)
    HARYANA_PINCODES = [
        "122",  # Gurgaon / Gurugram
        "123",  # Rewari / Mewat / Nuh
        "121",  # Faridabad (optional expansion)
    ]

    # District mapping (future-ready)
    DISTRICT_MAP = {
        "gurgaon": ["gurgaon", "gurugram", "ggn"],
        "sohna": ["sohna"],
        "manesar": ["manesar", "imt manesar"],
        "rewari": ["rewari", "bawal"],
        "nuh": ["nuh", "mewat"],
    }

    def is_target_location(self, text: str) -> bool:
        """Master function combining all checks"""
        if not text:
            return False

        text = text.lower()

        return (
            self._keyword_match(text)
            or self._regex_match(text)
            or self._pincode_match(text)
        )

    # ------------------------------------------------------------
    # 1. SIMPLE KEYWORD MATCH
    # ------------------------------------------------------------
    def _keyword_match(self, text: str) -> bool:
        return any(loc in text for loc in self.TARGET_KEYWORDS)

    # ------------------------------------------------------------
    # 2. REGEX MATCH (strong detection)
    # ------------------------------------------------------------
    def _regex_match(self, text: str) -> bool:
        patterns = [
            r"\bgurgaon\b",
            r"\bgurugram\b",
            r"\bggn\b",
            r"\bmanesar\b",
            r"\bsohna\b",
            r"\brewary?\b",
            r"\bnuh\b",
            r"\bmewat\b"
        ]

        return any(re.search(p, text) for p in patterns)

    # ------------------------------------------------------------
    # 3. PINCODE MATCH (VERY POWERFUL)
    # ------------------------------------------------------------
    def _pincode_match(self, text: str) -> bool:
        pincodes = re.findall(r"\b\d{6}\b", text)

        for pin in pincodes:
            if any(pin.startswith(prefix) for prefix in self.HARYANA_PINCODES):
                return True

        return False
