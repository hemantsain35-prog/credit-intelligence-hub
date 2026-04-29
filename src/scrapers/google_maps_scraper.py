import requests
import os


class GoogleMapsScraper:
    """Fetch business leads from Google Places API"""

    def __init__(self):
        self.api_key = os.getenv("GOOGLE_MAPS_API_KEY")

        if not self.api_key:
            raise ValueError("GOOGLE_MAPS_API_KEY not set")

    def fetch_all(self):
        queries = [
            "manufacturers in gurgaon",
            "traders in gurgaon",
            "industrial suppliers gurgaon",
            "small business gurgaon",
            "msme gurgaon",
            "exporters gurgaon"
        ]

        all_results = []

        for query in queries:
            results = self.search_places(query)
            all_results.extend(results)

        return all_results

    def search_places(self, query):
        url = "https://maps.googleapis.com/maps/api/place/textsearch/json"

        params = {
            "query": query,
            "key": self.api_key
        }

        try:
            response = requests.get(url, params=params, timeout=10)
            data = response.json()

            results = []

            for place in data.get("results", [])[:20]:
                place_id = place.get("place_id")

                details = self.get_place_details(place_id)

                results.append({
                    "title": place.get("name"),
                    "company": place.get("name"),
                    "location": place.get("formatted_address"),
                    "phone": details.get("phone"),
                    "url": details.get("website"),
                    "source": "GoogleMaps"
                })

            return results

        except Exception as e:
            print(f"Google Maps error: {e}")
            return []

    def get_place_details(self, place_id):
        url = "https://maps.googleapis.com/maps/api/place/details/json"

        params = {
            "place_id": place_id,
            "fields": "formatted_phone_number,website",
            "key": self.api_key
        }

        try:
            response = requests.get(url, params=params, timeout=10)
            data = response.json()

            result = data.get("result", {})

            return {
                "phone": result.get("formatted_phone_number", ""),
                "website": result.get("website", "")
            }

        except Exception:
            return {}
