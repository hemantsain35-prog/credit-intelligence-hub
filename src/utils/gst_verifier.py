import requests
import os
import re


class GSTVerifier:
    """Verify GST details using external API"""

    def __init__(self):
        self.api_key = os.getenv("GST_API_KEY")
        self.base_url = "https://api.mastersindia.co/gst/gstin"

    def extract_gstin(self, text):
        """Extract GSTIN from text"""
        pattern = r"\b\d{2}[A-Z]{5}\d{4}[A-Z]{1}[A-Z\d]{1}[Z]{1}[A-Z\d]{1}\b"
        match = re.search(pattern, text)
        return match.group(0) if match else None

    def verify(self, item):
        """Verify GST if available"""
        text = f"{item.get('title','')} {item.get('description','')}"

        gstin = self.extract_gstin(text)

        if not gstin or not self.api_key:
            item["gst_verified"] = False
            return item

        try:
            response = requests.get(
                self.base_url,
                params={
                    "gstin": gstin,
                    "client_id": self.api_key
                },
                timeout=10
            )

            data = response.json()

            if data.get("data"):
                item["gst_verified"] = True
                item["gst_status"] = data["data"].get("sts")
                item["legal_name"] = data["data"].get("lgnm")
            else:
                item["gst_verified"] = False

        except Exception:
            item["gst_verified"] = False

        return item
