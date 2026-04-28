import requests
from bs4 import BeautifulSoup


class JustdialScraper:
    BASE_URL = "https://www.justdial.com/Gurgaon"

    def fetch_all(self):
        query = "business loan"
        url = f"{self.BASE_URL}/{query.replace(' ', '-')}"

        try:
            headers = {
                "User-Agent": "Mozilla/5.0"
            }

            res = requests.get(url, headers=headers, timeout=10)
            soup = BeautifulSoup(res.text, "html.parser")

            results = []

            listings = soup.select(".resultbox")[:20]

            for item in listings:
                title = item.select_one(".lng_cont_name")

                results.append({
                    "title": title.text.strip() if title else "",
                    "description": query,
                    "url": url,
                    "source": "Justdial"
                })

            return results

        except Exception as e:
            print(f"Justdial error: {e}")
            return []
