import requests


class StartupSignals:
    def fetch_all(self):
        items = []

        try:
            url = "https://news.google.com/rss/search?q=startup+funding+india"
            res = requests.get(url, timeout=10)

            items.append({
                "title": "Startup expansion / funding activity",
                "description": "Companies scaling = need working capital",
                "url": url,
                "source": "StartupNews"
            })

        except Exception as e:
            print("Startup signal error:", e)

        return items
