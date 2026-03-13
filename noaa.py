import time 
import requests

API_TOKEN = "WQiIjecJWQqBMobXiHJszlRtPfgRqbjf"

url = "https://www.ncdc.noaa.gov/cdo-web/api/v2/data"

headers = {
    "token": API_TOKEN
}

years = [2020, 2021, 2022, 2023, 2024]
all_results = []

for year in years:
    print(f"Fetching {year}...")
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
            "offset": offset
        }

        for attempt in range(3):
            response = requests.get(url, headers=headers, params=params)
            if response.status_code == 200:
                break
            print(f"  Got {response.status_code}, retrying in 10 seconds... (attempt {attempt + 1}/3)")
            time.sleep(10)

        if response.status_code != 200:
            print(f"  Failed after 3 attempts for {year}, skipping...")
            break
    

        data = response.json()

        if "results" not in data:
            print(f"No results for {year}")
            break

        batch = data["results"]
        all_results.extend(batch)
        print(f"  {year}: fetched {len(all_results)} total so far...")

        if len(batch) < limit:
            break

        offset += limit

daily = {}
for result in all_results:
    date = result["date"][:10]
    rainfall = result["value"] / 10
    if date not in daily:
        daily[date] = []
    daily[date].append(rainfall)

daily_averages = {}
for date, readings in daily.items():
    daily_averages[date] = sum(readings) / len(readings)

monthly = {}
for date, avg in daily_averages.items():
    month = date[:7]
    if month not in monthly:
        monthly[month] = 0
    monthly[month] += avg

print("\nMonthly rainfall totals for Chicago 2020-2024:")
print("-" * 45)
for month in sorted(monthly.keys()):
    total = monthly[month]
    bar = "█" * int(total / 3)
    print(f"{month} | {total:6.1f}mm | {bar}")
    import json

output = {}
for month in sorted(monthly.keys()):
    output[month] = round(monthly[month], 1)

with open("data.json", "w") as f:
    json.dump(output, f, indent=2)

print("\nData saved to data.json")
