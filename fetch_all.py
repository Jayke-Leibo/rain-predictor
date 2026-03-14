"""
fetch_all.py
Fetches 25 years of daily weather data for Chicago from Open-Meteo (free, no API key).
Variables: precipitation, temp, dew point, humidity, pressure, wind, cloud cover.
Also fetches ENSO (El Nino/La Nina) index from NOAA.
Saves everything to data_full.json for model training.
"""

import urllib.request
import json
import time

# Chicago coordinates
LAT = 41.85
LON = -87.65
START = "2000-01-01"
END   = "2024-12-31"

print("=" * 55)
print("  Chicago Weather Data Fetcher")
print("  Open-Meteo archive + NOAA ENSO index")
print("=" * 55)

# ── 1. OPEN-METEO ─────────────────────────────────────────
print("\n[1/3] Fetching Open-Meteo daily data (2000–2024)...")
print("      This may take 30–60 seconds...")

VARS = ",".join([
    "precipitation_sum",
    "temperature_2m_max",
    "temperature_2m_min",
    "temperature_2m_mean",
    "apparent_temperature_mean",
    "relative_humidity_2m_max",
    "relative_humidity_2m_min",
    "dew_point_2m_max",
    "dew_point_2m_min",
    "surface_pressure_mean",
    "wind_speed_10m_max",
    "wind_direction_10m_dominant",
    "cloud_cover_mean",
    "shortwave_radiation_sum",
    "et0_fao_evapotranspiration",
])

url = (
    f"https://archive-api.open-meteo.com/v1/archive"
    f"?latitude={LAT}&longitude={LON}"
    f"&start_date={START}&end_date={END}"
    f"&daily={VARS}"
    f"&timezone=America%2FChicago"
)

for attempt in range(4):
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "RainPredictor/1.0"})
        with urllib.request.urlopen(req, timeout=60) as resp:
            raw = json.loads(resp.read().decode())
        break
    except Exception as e:
        if attempt < 3:
            print(f"  Attempt {attempt+1} failed ({e}), retrying in 15s...")
            time.sleep(15)
        else:
            raise RuntimeError(f"Open-Meteo fetch failed after 4 attempts: {e}")

dates  = raw["daily"]["time"]
fields = {k: raw["daily"][k] for k in raw["daily"] if k != "time"}
print(f"  ✓ {len(dates)} daily records fetched")

# Build daily records
daily_records = {}
for i, date in enumerate(dates):
    rec = {"date": date}
    for k, v in fields.items():
        val = v[i]
        rec[k] = round(val, 3) if val is not None else None
    daily_records[date] = rec

# ── 2. ENSO INDEX ─────────────────────────────────────────
print("\n[2/3] Fetching ENSO (El Nino/La Nina) index from NOAA...")
print("      Using Oceanic Nino Index (ONI)...")

ONI_URL = "https://www.cpc.ncep.noaa.gov/data/indices/oni.ascii.txt"

enso_monthly = {}
try:
    req = urllib.request.Request(ONI_URL, headers={"User-Agent": "RainPredictor/1.0"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        lines = resp.read().decode().splitlines()

    month_map = {
        "DJF":12,"JFM":1,"FMA":2,"MAM":3,"AMJ":4,"MJJ":5,
        "JJA":6,"JAS":7,"ASO":8,"SON":9,"OND":10,"NDJ":11
    }

    for line in lines[1:]:
        parts = line.split()
        if len(parts) >= 4:
            season, yr, anom = parts[0], parts[1], parts[3]
            try:
                m = month_map.get(season)
                y = int(yr)
                oni = float(anom)
                if m and 2000 <= y <= 2025:
                    key = f"{y}-{str(m).zfill(2)}"
                    enso_monthly[key] = oni
            except ValueError:
                continue

    print(f"  ✓ {len(enso_monthly)} monthly ONI values loaded")

except Exception as e:
    print(f"  ✗ ENSO fetch failed: {e}")
    print("    Continuing without ENSO data...")

# Attach monthly ENSO to each daily record
for date, rec in daily_records.items():
    ym = date[:7]
    rec["enso_oni"] = enso_monthly.get(ym, None)

# ── 3. DERIVED FEATURES ───────────────────────────────────
print("\n[3/3] Computing derived features...")

sorted_dates = sorted(daily_records.keys())

for i, date in enumerate(sorted_dates):
    rec = daily_records[date]

    # Temp range
    tmax = rec.get("temperature_2m_max")
    tmin = rec.get("temperature_2m_min")
    rec["temp_range"] = round(tmax - tmin, 2) if tmax is not None and tmin is not None else None

    # Humidity range
    hmax = rec.get("relative_humidity_2m_max")
    hmin = rec.get("relative_humidity_2m_min")
    rec["humidity_mean"] = round((hmax + hmin) / 2, 1) if hmax and hmin else None

    # Dew point mean
    dpmax = rec.get("dew_point_2m_max")
    dpmin = rec.get("dew_point_2m_min")
    rec["dew_point_mean"] = round((dpmax + dpmin) / 2, 2) if dpmax is not None and dpmin is not None else None

    # Pressure trend (vs yesterday)
    if i > 0:
        prev_date = sorted_dates[i-1]
        prev_p = daily_records[prev_date].get("surface_pressure_mean")
        curr_p = rec.get("surface_pressure_mean")
        rec["pressure_trend"] = round(curr_p - prev_p, 2) if curr_p and prev_p else None
    else:
        rec["pressure_trend"] = None

    # Wind direction encoded: S/SW = wet (high), N/NW = dry (low)
    wd = rec.get("wind_direction_10m_dominant")
    if wd is not None:
        import math
        # southerly component: sin(wd in radians), negative = from south
        south_component = -math.cos(math.radians(wd))
        rec["wind_south_component"] = round(south_component, 3)
    else:
        rec["wind_south_component"] = None

    # Lag: yesterday's precip
    if i > 0:
        prev_date = sorted_dates[i-1]
        rec["precip_lag1"] = daily_records[prev_date].get("precipitation_sum")
    else:
        rec["precip_lag1"] = None

    # 7-day rolling precip total
    if i >= 7:
        seven_days = [daily_records[sorted_dates[j]].get("precipitation_sum", 0) or 0 for j in range(i-7, i)]
        rec["precip_7d_total"] = round(sum(seven_days), 2)
    else:
        rec["precip_7d_total"] = None

    # Calendar features
    from datetime import date as ddate
    d = ddate.fromisoformat(date)
    rec["year"] = d.year
    rec["month"] = d.month
    rec["day"] = d.day
    rec["day_of_year"] = d.timetuple().tm_yday
    rec["week_of_year"] = d.isocalendar()[1]

print(f"  ✓ Derived features added to all {len(daily_records)} records")

# ── ALSO REBUILD MONTHLY SUMMARY ──────────────────────────
print("\nBuilding monthly summary...")
monthly_summary = {}
for date, rec in daily_records.items():
    ym = date[:7]
    p = rec.get("precipitation_sum") or 0
    if ym not in monthly_summary:
        monthly_summary[ym] = 0.0
    monthly_summary[ym] = round(monthly_summary[ym] + p, 2)

print(f"  ✓ {len(monthly_summary)} monthly totals computed")

# ── SAVE ──────────────────────────────────────────────────
print("\nSaving files...")

with open("data_full.json", "w") as f:
    json.dump(daily_records, f, separators=(',', ':'))
print(f"  ✓ data_full.json — {len(daily_records)} daily records")

with open("data_monthly_full.json", "w") as f:
    json.dump(monthly_summary, f, indent=2)
print(f"  ✓ data_monthly_full.json — {len(monthly_summary)} months")

with open("enso.json", "w") as f:
    json.dump(enso_monthly, f, indent=2)
print(f"  ✓ enso.json — {len(enso_monthly)} ENSO values")

# ── SUMMARY STATS ─────────────────────────────────────────
precip_vals = [r["precipitation_sum"] for r in daily_records.values() if r.get("precipitation_sum") is not None]
rainy_days = sum(1 for v in precip_vals if v > 1)

print("\n" + "=" * 55)
print("  Summary")
print("=" * 55)
print(f"  Date range   : {sorted_dates[0]}  →  {sorted_dates[-1]}")
print(f"  Total days   : {len(daily_records):,}")
print(f"  Rainy days   : {rainy_days:,} ({100*rainy_days/len(precip_vals):.1f}%)")
print(f"  Avg precip   : {sum(precip_vals)/len(precip_vals):.2f} mm/day")
print(f"  ENSO months  : {len(enso_monthly)}")
print(f"  Features/day : {len(next(iter(daily_records.values())))}")
print("\n  Next step: run  python3 model_v2.py")
print("=" * 55)
