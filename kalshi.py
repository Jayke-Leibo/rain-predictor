import requests
import json

KALSHI_API_KEY = "your_new_api_key_here"

BASE_URL = "https://api.elections.kalshi.com/trade-api/v2"

headers = {
    "accept": "application/json",
    "Authorization": f"Bearer {KALSHI_API_KEY}",
    "Content-Type": "application/json"
}

TICKERS = [
    "KXRAINCHIM-26MAR-1",
    "KXRAINCHIM-26MAR-2",
    "KXRAINCHIM-26MAR-3",
    "KXRAINCHIM-26MAR-4",
    "KXRAINCHIM-26MAR-5",
    "KXRAINCHIM-26MAR-6",
    "KXRAINCHIM-26MAR-7",
]

kalshi_data = {}

for ticker in TICKERS:
    response = requests.get(
        f"{BASE_URL}/markets/{ticker}",
        headers=headers
    )

    if response.status_code == 200:
        market = response.json()["market"]

        subtitle = market.get("yes_sub_title", "")
        yes_bid = float(market.get("yes_bid_dollars", 0)) * 100
        yes_ask = float(market.get("yes_ask_dollars", 0)) * 100
        mid = round((yes_bid + yes_ask) / 2)

        print(f"{subtitle}")
        print(f"  Bid: {yes_bid:.0f}¢  Ask: {yes_ask:.0f}¢  Mid: {mid}%")
        print()

        kalshi_data[ticker] = {
            "threshold": subtitle,
            "yes_bid": round(yes_bid),
            "yes_ask": round(yes_ask),
            "mid": mid
        }
    else:
        print(f"Error {response.status_code}: {response.text}")

# Save raw data
with open("kalshi_prices.json", "w") as f:
    json.dump(kalshi_data, f, indent=2)

# Save dashboard-friendly version
dashboard_kalshi = {}
for ticker, d in kalshi_data.items():
    threshold = d["threshold"]
    dashboard_kalshi[threshold] = d["mid"]

with open("kalshi_dashboard.json", "w") as f:
    json.dump(dashboard_kalshi, f, indent=2)

import re

# Load model predictions
with open("model_predictions.json") as f:
    model_data = json.load(f)

# Merge Kalshi + model into one dashboard object
combined = {}
for label in dashboard_kalshi:
    combined[label] = {
        "kalshi": dashboard_kalshi[label],
        "model": model_data["probabilities"].get(label, None)
    }

# Read dashboard
with open("dashboard.html", "r") as f:
    html = f.read()

# Build JS strings
kalshi_js = "const KALSHI_DATA = " + json.dumps(dashboard_kalshi, indent=2) + ";"
model_js = "const MODEL_DATA = " + json.dumps(model_data["probabilities"], indent=2) + ";"
model_meta_js = f'const MODEL_META = {json.dumps({"blended_mm": model_data["blended_mm"], "weighted_avg_mm": model_data["weighted_avg_mm"], "linear_mm": model_data["linear_mm"], "xgboost_mm": model_data["xgboost_mm"]})};'

# Replace KALSHI_DATA
if "const KALSHI_DATA" in html:
    html = re.sub(r"const KALSHI_DATA = \{[^}]+\};", kalshi_js, html, flags=re.DOTALL)
else:
    html = html.replace("<script>", "<script>\n" + kalshi_js)

# Replace or insert MODEL_DATA
if "const MODEL_DATA" in html:
    html = re.sub(r"const MODEL_DATA = \{[^}]+\};", model_js, html, flags=re.DOTALL)
else:
    html = html.replace(kalshi_js, kalshi_js + "\n" + model_js)

# Replace or insert MODEL_META
if "const MODEL_META" in html:
    html = re.sub(r"const MODEL_META = \{[^;]+\};", model_meta_js, html)
else:
    html = html.replace(model_js, model_js + "\n" + model_meta_js)

with open("dashboard.html", "w") as f:
    f.write(html)

print("Dashboard updated with live Kalshi + model predictions!")
