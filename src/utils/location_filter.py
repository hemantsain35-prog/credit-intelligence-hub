class LocationFilter:
    """Filters leads based on target locations."""

    TARGET_LOCATIONS = [
        "gurgaon",
        "gurugram",
        "sohna",
        "manesar",
        "rewari",
        "nuh",
        "mewat",
        "g-town",          # optional slang
        "g town",
        "ggn"              # VERY common abbreviation
    ]

    def is_target_location(self, text: str) -> bool:
        if not text:
            return False

        text = text.lower()

        return any(loc in text for loc in self.TARGET_LOCATIONS)
