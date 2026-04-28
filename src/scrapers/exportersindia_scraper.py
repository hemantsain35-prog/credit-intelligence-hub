import requests
from bs4 import BeautifulSoup


class ExportersIndia:
    def fetch_all(self):
        url = "https://www.exportersindia.com/buy-leads/"
        items = []

        try:
            res = requests.get(url, timeout=10)
            soup = BeautifulSoup(res.text, "html.parser")

            leads = soup.find_all("div", class_="product")

            for lead in leads:
                title = lead.get_text(strip=True)

                items.append({
                    "title": title,
                    "description": title,
                    "url": url,
                    "source": "ExportersIndia"
                })

        except Exception as e:
            print("ExportersIndia error:", e)

        return items
