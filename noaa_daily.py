import requests
import time
import json

API_TOKEN = "WQiIjecJWQqBMobXiHJszlRtPfgRqbjf"
url = "https://www.ncdc.noaa.gov/cdo-web/api/v2/data"
headers = {"token": API_TOKEN}

years = [2020, 2021, 2022, 2023, 2024]
all_results = []

for year in years:
    print(f"Fetching daily data for {year}...")
    offset = 1
    limit = 1000

    while True:
        params = {
            "datasetid": "GHCND",
            "datatypeid": "PRCP",
            "locationid": "CITY:US390029",
            "startdate": f"{year}-01-01",
            "enddate": f"{year}-12-31",
            "limit": limit,
            "offset": offset,
            "units": "metric"
        }

        for attempt in range(3):
            response = requests.get(url, headers=headers, params=params)
            if response.status_code == 200:
                break
            print(f"  Got {response.status_code}, retrying in 10s... (attempt {attempt+1}/3)")
            time.sleep(10)

        if response.status_code != 200:
            print(f"  Failed for {year}, skipping...")
            break

        data = response.json()
        if "results" not in data:
            print(f"  No results for {year}")
            break

        batch = data["results"]
        all_results.extend(batch)
        print(f"  {year}: {len(all_results)} total records so far...")

        if len(batch) < limit:
            break
        offset += limit
        time.sleep(1)

# Group by date, average across stations
daily = {}
for result in all_results:
    date = result["date"][:10]
    rainfall = result["value"] / 10
    if date not in daily:
        daily[date] = []
    daily[date].append(rainfall)

daily_averages = {}
for date, readings in daily.items():
    daily_averages[date] = round(sum(readings) / len(readings), 2)

# Save
with open("data_daily.json", "w") as f:
    json.dump(daily_averages, f, indent=2)

print(f"\nDone! {len(daily_averages)} days saved to data_daily.json")

# Preview
print("\nSample (first 10 days of 2020):")
for date in sorted(daily_averages.keys())[:10]:
    bar = "█" * int(daily_averages[date])
    print(f"  {date}: {daily_averages[date]:5.1f}mm {bar}")