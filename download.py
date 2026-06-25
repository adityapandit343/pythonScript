"""
download.py — Daily Mandi Price Downloader
==========================================
Fetches today's commodity prices from data.gov.in and saves them as:
    data/mandi_prices_YYYY-MM-DD.csv

Run once per day (cron, Task Scheduler, etc.).

Usage:
    python download.py

Cron (daily at 08:00):
    0 8 * * * /usr/bin/python3 /path/to/mandi-price-tracker/download.py
"""

import os
from dotenv import load_dotenv
import csv
import sys
import logging
import requests
from datetime import datetime

# ── Configuration ─────────────────────────────────────────────────────────────
load_dotenv()  # ← ADD THIS LINE (optional, but recommended)
API_KEY = os.environ.get("API_KEY")

headers = {
    "Authorization": API_KEY
} # Replace with your data.gov.in API key
RESOURCE_ID  = "9ef84268-d588-465a-a308-a864a43d0070"
BASE_URL     = "https://api.data.gov.in/resource/{resource_id}"
DATA_DIR     = os.path.join(os.path.dirname(__file__), "data")
LIMIT        = 10000                   # Records per request (max allowed)
LOG_FORMAT   = "%(asctime)s [%(levelname)s] %(message)s"

logging.basicConfig(level=logging.INFO, format=LOG_FORMAT,
                    handlers=[logging.StreamHandler(sys.stdout)])
log = logging.getLogger(__name__)

# ── Core functions ────────────────────────────────────────────────────────────

def build_url():
    return BASE_URL.format(resource_id=RESOURCE_ID)


def fetch_page(session, offset=0, target_date=None):
    """Fetch a single page of records from the API."""
    params = {
        "api-key": API_KEY,
        "format":  "json",
        "limit":   LIMIT,
        "offset":  offset,
    }
    
    # Date filter add karo
    if target_date:
        params["filters[arrival_date]"] = target_date
    
    log.info(f"📡 Requesting offset: {offset}, limit: {LIMIT}")
    resp = session.get(build_url(), params=params, timeout=30)
    resp.raise_for_status()
    data = resp.json()
    log.info(f"📡 Response has {len(data.get('records', []))} records")
    return data


def fetch_all_records(target_date=None):
    """
    Paginate through the API until all records for a specific date are collected.
    
    Args:
        target_date (str): Date in YYYY-MM-DD format
    
    Returns:
        list: All records for that date
    """
    records = []
    session = requests.Session()
    session.headers.update({"User-Agent": "MandiPriceTracker/1.0"})

    log.info("Connecting to data.gov.in …")
    
    # Pehla page fetch karo
    first_page = fetch_page(session, offset=0, target_date=target_date)

    total = int(first_page.get("total", 0))
    log.info("Total records available: %d", total)

    batch = first_page.get("records", [])
    records.extend(batch)
    log.info("Fetched %d / %d records", len(records), total)

    # 🔥 Pagination loop - baaki ke pages fetch karo
    offset = LIMIT
    while len(records) < total:
        log.info(f"🔄 Fetching next page at offset: {offset}")
        page = fetch_page(session, offset=offset, target_date=target_date)
        batch = page.get("records", [])
        
        log.info(f"📦 Received {len(batch)} records in this batch")
        
        if not batch:
            log.warning("⚠️ Empty batch received! Breaking loop.")
            break
            
        records.extend(batch)
        offset += LIMIT
        log.info("Fetched %d / %d records", len(records), total)
        
        # Rate limit se bachne ke liye thoda ruko
        time.sleep(0.5)

    log.info(f"✅ Total records fetched: {len(records)}")
    return records


def save_csv(records, date_str):
    """Write records list to a dated CSV file, return path."""
    os.makedirs(DATA_DIR, exist_ok=True)
    filename = f"mandi_prices_{date_str}.csv"
    filepath = os.path.join(DATA_DIR, filename)

    if not records:
        log.warning("No records to save.")
        return None

    fieldnames = list(records[0].keys())

    with open(filepath, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(records)

    log.info("Saved %d records → %s", len(records), filepath)
    return filepath


def already_downloaded(date_str):
    """Return True if today's file already exists."""
    filepath = os.path.join(DATA_DIR, f"mandi_prices_{date_str}.csv")
    return os.path.isfile(filepath)


# ── Entry-point ───────────────────────────────────────────────────────────────

def main():
    date_str = datetime.now().strftime("%Y-%m-%d")
    log.info("=== Mandi Price Downloader — %s ===", date_str)

    if already_downloaded(date_str):
        log.info("Today's data already exists. Nothing to do.")
        return 0

    try:
        # 🔥 Saara data pehle fetch karo
        records = fetch_all_records(target_date=date_str)
        
        if not records:
            log.error("API returned 0 records. Aborting.")
            return 1

        # 🔥 Save SIRF EK BAAR, loop ke BAHAR
        path = save_csv(records, date_str)
        if path:
            log.info("✅  Download complete: %s", path)
            return 0
        return 1

    except requests.exceptions.ConnectionError:
        log.error("❌  Network error — check your internet connection.")
    except requests.exceptions.Timeout:
        log.error("❌  Request timed out — try again later.")
    except requests.exceptions.HTTPError as e:
        log.error("❌  HTTP %s — %s", e.response.status_code, e.response.text[:200])
    except KeyboardInterrupt:
        log.info("Interrupted by user.")
    except Exception as e:
        log.exception("❌  Unexpected error: %s", e)

    return 1


if __name__ == "__main__":
    sys.exit(main())