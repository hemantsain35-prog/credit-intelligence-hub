import requests
import os


class GoogleMapsScraper:
    def __init__(self):
        self.api_key = os.getenv("GOOGLE_MAPS_API_KEY")

    def fetch_all(self):
        queries = [
            "manufacturers in gurgaon",
            "traders in gurugram",
            "wholesalers in manesar",
            "industrial suppliers in sohna"
        ]

        results = []

        for query in queries:
            url = "https://maps.googleapis.com/maps/api/place/textsearch/json"

            params = {
                "query": query,
                "key": self.api_key
            }

            res = requests.get(url, params=params)
            data = res.json()

            for place in data.get("results", [])[:10]:
                place_id = place.get("place_id")

                details = self.get_details(place_id)

                results.append({
                    "title": place.get("name"),
                    "location": place.get("formatted_address"),
                    "rating": place.get("rating"),
                    "reviews": place.get("user_ratings_total"),
                    "phone": details.get("phone"),
                    "website": details.get("website"),
                    "source": "googlemaps",
                    "url": f"https://www.google.com/maps/place/?q=place_id:{place_id}"
                })

        return results

    def get_details(self, place_id):
        url = "https://maps.googleapis.com/maps/api/place/details/json"

        params = {
            "place_id": place_id,
            "fields": "formatted_phone_number,website",
            "key": self.api_key
        }

        res = requests.get(url, params=params)
        data = res.json()

        result = data.get("result", {})

        return {
            "phone": result.get("formatted_phone_number"),
            "website": result.get("website")
        }
