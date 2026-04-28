import requests
from bs4 import BeautifulSoup


class TenderScraper:
    def fetch_all(self):
        url = "https://etenders.gov.in/eprocure/app"
        items = []

        try:
            res = requests.get(url, timeout=10)
            soup = BeautifulSoup(res.text, "html.parser")

            items.append({
                "title": "Government Tender Opportunity",
                "description": "Businesses bidding for tenders need working capital",
                "url": url,
                "source": "Tender"
            })

        except Exception as e:
            print("Tender error:", e)

        return items
