class LocationFilter:

    TARGET = [
        "gurgaon",
        "gurugram",
        "manesar",
        "sohna",
        "rewari",
        "nuh",
        "mewat"
    ]

    def is_target_location(self, text):
        text = text.lower()
        return any(loc in text for loc in self.TARGET)
