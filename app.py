"""
Mandi Price Tracker - Flask Web Application
Reads daily CSV files from data/ and displays market prices.
"""

import os
import csv
import glob
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for

app = Flask(__name__)

DATA_DIR = os.path.join(os.path.dirname(__file__), "data")

# ── Helpers ──────────────────────────────────────────────────────────────────

def get_latest_csv():
    pattern = os.path.join(DATA_DIR, "mandi_prices_*.csv")
    files = sorted(glob.glob(pattern), reverse=True)
    return files[0] if files else None


def get_unique_values(csv_path, column):
    """CSV से unique sorted values निकालता है (states/crops के लिए)"""
    values = set()
    try:
        with open(csv_path, newline="", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            for row in reader:
                norm = {k.strip().lower().replace(" ", "_"): v.strip()
                        for k, v in row.items()}
                val = norm.get(column, "").strip()
                if val:
                    values.add(val)
    except Exception as e:
        app.logger.error("Error reading CSV %s: %s", csv_path, e)
    return sorted(values)


def read_prices(csv_path, crop=None, state=None):
    rows = []
    try:
        with open(csv_path, newline="", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            for row in reader:
                norm = {k.strip().lower().replace(" ", "_"): v.strip()
                        for k, v in row.items()}

                commodity = (norm.get("commodity") or norm.get("commodity_name") or "").strip()
                state_val  = (norm.get("state") or norm.get("state_name") or "").strip()

                if crop  and crop.lower()  not in commodity.lower():
                    continue
                if state and state.lower() not in state_val.lower():
                    continue

                rows.append(norm)
    except Exception as e:
        app.logger.error("Error reading CSV %s: %s", csv_path, e)
    return rows


def safe_float(value, default=0.0):
    try:
        return float(str(value).replace(",", "").strip())
    except (ValueError, TypeError):
        return default


# ── Routes ───────────────────────────────────────────────────────────────────

@app.route("/")
def index():
    latest = get_latest_csv()
    last_updated = None
    crops = []
    states = []

    if latest:
        basename = os.path.basename(latest)
        try:
            date_str = basename.replace("mandi_prices_", "").replace(".csv", "")
            last_updated = datetime.strptime(date_str, "%Y-%m-%d").strftime("%d %B %Y")
        except ValueError:
            last_updated = basename

        # CSV से automatically पढ़ो
        crops  = get_unique_values(latest, "commodity")
        states = get_unique_values(latest, "state")

    return render_template("index.html",
                           crops=crops,
                           states=states,
                           last_updated=last_updated,
                           has_data=latest is not None)


@app.route("/prices", methods=["POST"])
def prices():
    crop  = request.form.get("crop", "").strip()
    state = request.form.get("state", "").strip()

    if not crop or not state:
        return render_template("error.html",
                               message="Please select both a crop and a state.",
                               retry_url=url_for("index"))

    latest = get_latest_csv()
    if not latest:
        return render_template("error.html",
                               message="No price data available yet. Run download.py to fetch today's data.",
                               retry_url=url_for("index"))

    rows = read_prices(latest, crop=crop, state=state)
    rows.sort(key=lambda r: safe_float(r.get("modal_price") or r.get("modal price") or 0), reverse=True)

    best = rows[0] if rows else None

    basename = os.path.basename(latest)
    try:
        date_str = basename.replace("mandi_prices_", "").replace(".csv", "")
        data_date = datetime.strptime(date_str, "%Y-%m-%d").strftime("%d %B %Y")
    except ValueError:
        data_date = "Latest"

    return render_template("prices.html",
                           rows=rows,
                           best=best,
                           crop=crop,
                           state=state,
                           data_date=data_date,
                           total=len(rows))


if __name__ == "__main__":
    os.makedirs(DATA_DIR, exist_ok=True)
    app.run(debug=True, host="0.0.0.0", port=5000)