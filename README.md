# Credit Intelligence Hub

## Overview

A lightweight, production-ready RSS-based lead intelligence system designed to identify and score high-value business opportunities in Gurgaon.

### Pipeline Flow

```
RSS Feeds → Demand Detection → Value Extraction → Gurgaon Filter → Lead Scoring → Company Enrichment → Telegram Alerts
```

## Filtering Criteria

Only leads meeting ALL criteria are included:

1. **Demand Signal**: Buyer needs supplier/service (keywords: need, supplier, requirement, tender, etc.)
2. **Deal Size**: ≥ ₹50 lakh
3. **Location**: Gurgaon / Gurugram ONLY
4. **Lead Score**: ≥ 5 (max 20)

## Setup

### Prerequisites

- Python 3.8+
- pip

### Installation

```bash
# Clone repository
git clone https://github.com/hemantsain35-prog/credit-intelligence-hub.git
cd credit-intelligence-hub

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### Configuration

Create `.env` file with Telegram credentials:

```bash
cp .env.example .env
```

Edit `.env` and add:

```
TELEGRAM_BOT_TOKEN=your_bot_token
TELEGRAM_CHAT_ID=your_chat_id
```

To get Telegram credentials:
1. Create a bot via [@BotFather](https://t.me/botfather)
2. Get your chat ID from [@userinfobot](https://t.me/userinfobot)

## Usage

### Run Pipeline

```bash
export PYTHONPATH=src
python -m src.main
```

### What Happens

1. Fetches latest items from 3 RSS feeds:
   - Google News: "tender india"
   - Google News: "construction project india"
   - Google News: "supplier requirement india"

2. Analyzes each item for:
   - Demand keywords (need, requirement, supplier, etc.)
   - Monetary value (₹3 Cr → 300L, "75 lakh" → 75L)
   - Location (Gurgaon/Gurugram only)

3. Filters by:
   - Deal size ≥ ₹50 lakh
   - Location = Gurgaon
   - Lead score ≥ 5

4. Enriches with:
   - Company name extraction
   - Business type detection
   - Turnover estimation
   - Risk assessment

5. Sends qualified leads to Telegram in markdown format

## Scoring System

| Factor | Points |
|--------|--------|
| Gurgaon location | +5 |
| Value ≥ ₹1 Cr | +3 |
| Demand signal | +3 |
| Urgency keywords | +4 |
| Project/Contract mention | +2 |
| **Maximum** | **20** |

## Project Structure

```
credit-intelligence-hub/
├── src/
│   ├── __init__.py
│   ├── main.py                 # Entry point
│   ├── scrapers/
│   │   ├── __init__.py
│   │   └── rss_scraper.py     # RSS fetcher
│   ├── utils/
│   │   ├── __init__.py
│   │   ├── demand_detector.py # Demand & value extraction
│   │   ├── location_filter.py # Gurgaon filtering
│   │   ├── lead_scorer.py     # Scoring logic
│   │   └── enrichment.py      # Company enrichment
│   └── services/
│       ├── __init__.py
│       └── telegram_service.py # Telegram integration
├── .env.example
├── .gitignore
├── requirements.txt
└── README.md
```

## Dependencies

- **feedparser** (6.0.10+): RSS feed parsing
- **requests** (2.31.0+): HTTP requests for Telegram API
- **python-dotenv** (1.0.0+): Environment variable loading

## RSS Feeds

The system monitors:

1. `https://news.google.com/rss/search?q=tender+india`
2. `https://news.google.com/rss/search?q=construction+project+india`
3. `https://news.google.com/rss/search?q=supplier+requirement+india`

Feed items are normalized into:

```python
{
    "title": str,
    "description": str,
    "url": str,
    "value": str,          # Raw value string
    "location": str,
    "is_demand": bool,
    "numeric_value": int,  # Value in lakhs
    "has_urgency": bool,
    "company": str,
    "business_type": str,
    "turnover": str,
    "risk": str,           # Low, Medium, High
    "score": int,          # 0-20
}
```

## Telegram Message Format

```
🔥 GURGAON HIGH-VALUE LEADS

1. Title
📍 Gurgaon
💰 Deal Size
🏢 Company
📊 Turnover
⚠️ Risk
⭐ Score
🔗 Read more

👉 Action: Call immediately
```

Messages are automatically split if they exceed 3500 characters.

## Troubleshooting

### ImportError: No module named 'src'

```bash
export PYTHONPATH=src
python -m src.main
```

### No leads found

- Check RSS feeds are accessible
- Verify location keywords match "gurgaon" or "gurugram"
- Ensure deal size is ≥ ₹50 lakh
- Check lead score ≥ 5

### Telegram not receiving messages

- Verify `TELEGRAM_BOT_TOKEN` and `TELEGRAM_CHAT_ID` in `.env`
- Check bot has permission to send messages to chat
- Review logs for API errors

## Features

✅ **Simple & Clean**: Only RSS + demand detection + filtering  
✅ **Production-Ready**: Error handling, logging, timeout management  
✅ **Gurgaon-Focused**: Strict location filtering  
✅ **Value-Based**: Minimum deal size ₹50 lakh  
✅ **Intelligent Scoring**: Multi-factor lead quality assessment  
✅ **Telegram Native**: Direct messaging integration  
✅ **Minimal Dependencies**: Only 3 required packages  

## What's NOT Included

❌ Google Sheets integration  
❌ GCP authentication  
❌ Playwright/browser scraping  
❌ Database dependencies  
❌ External APIs (except Telegram)  

## Logs

All operations are logged with timestamps:

```
2026-04-28 10:30:45 - src.main - INFO - Starting RSS lead intelligence pipeline...
2026-04-28 10:30:45 - src.main - INFO - Step 1: Fetching RSS feeds...
2026-04-28 10:30:50 - src.main - INFO - Fetched 45 items from RSS feeds
...
```

## Performance

- **Feed fetch**: ~5-10 seconds (3 feeds)
- **Processing**: <100ms per item
- **Total runtime**: ~30-60 seconds

## License

MIT

## Support

For issues, create a GitHub issue with:
- Python version
- Error logs
- Steps to reproduce
