import requests


class JustDial:
    def fetch_all(self):
        items = []

        try:
            url = "https://www.justdial.com/Gurgaon/B2B-Services"
            res = requests.get(url, timeout=10)

            items.append({
                "title": "B2B Services Demand - Justdial",
                "description": "Businesses searching for suppliers/services",
                "url": url,
                "source": "JustDial"
            })

        except Exception as e:
            print("Justdial error:", e)

        return items
