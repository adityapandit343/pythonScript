# 🌾 Mandi Price Tracker

Real-time agricultural commodity price tracker for Indian mandis,
powered by [data.gov.in](https://data.gov.in).

---

## Project Structure

```
mandi-price-tracker/
├── app.py              ← Flask web app
├── download.py         ← Daily data downloader
├── requirements.txt
├── templates/
│   ├── index.html      ← Home / search page
│   ├── prices.html     ← Price results page
│   ├── success.html    ← Download success
│   └── error.html      ← Error page
└── data/
    └── mandi_prices_YYYY-MM-DD.csv   ← Daily CSV files
```

---

## Quick Start

### 1. Install dependencies

```bash
pip install -r requirements.txt
```

### 2. Get your API key

1. Register at https://data.gov.in
2. Go to **My Account → API Keys**
3. Copy your key

### 3. Configure the downloader

Open `download.py` and replace:
```python
API_KEY = "YOUR_API_KEY"
```
with your actual key.

### 4. Download today's data

```bash
python download.py
```

The file `data/mandi_prices_YYYY-MM-DD.csv` will be created.

### 5. Run the web app

```bash
python app.py
```

Open http://localhost:5000 in your browser.

---

## Automate daily downloads

**Linux / macOS (cron) — run at 8 AM daily:**
```cron
0 8 * * * cd /path/to/mandi-price-tracker && python download.py >> logs/download.log 2>&1
```

**Windows (Task Scheduler):**
- Action: `python C:\path\to\mandi-price-tracker\download.py`
- Trigger: Daily at 08:00

---

## Features

| Feature | Details |
|---|---|
| Crops | Tomato, Potato, Wheat, Rice, Onion |
| States | UP, Bihar, MP, Rajasthan, Punjab, Haryana |
| Price sort | Highest modal price first |
| Data storage | CSV files (no database required) |
| Auto-detect | Picks the latest dated CSV automatically |
| Mobile UI | Fully responsive design |

---

## API Details

- **Source:** data.gov.in — Agmarknet Daily Mandi Prices
- **Resource ID:** `9ef84268-d588-465a-a308-a864a43d0070`
- **Rate limit:** 1 download per day (the script skips if already downloaded)
- **Records:** Up to 10,000 per request with pagination support

---

## Tech Stack

- **Python 3.8+**
- **Flask** — web framework
- **requests** — API calls
- **csv / datetime / os / glob** — stdlib only (no database)

---

*Prices are in ₹ per quintal. Data sourced from Agmarknet via data.gov.in.*
