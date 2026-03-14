"""
fetch_indices.py
Fetches all major climate forcing variables that influence Chicago rainfall:
  - AO  (Arctic Oscillation)        — NOAA CPC
  - NAO (North Atlantic Oscillation) — NOAA CPC
  - MJO (Madden-Julian Oscillation)  — NOAA CPC
  - PDO (Pacific Decadal Oscillation)— NOAA NCEI
  - AMO (Atlantic Multidecadal Osc)  — NOAA PSL
  - Gulf of Mexico SST               — Open-Meteo marine
  - Surface Relative Humidity        — Open-Meteo archive
  - 500mb Geopotential Height        — Open-Meteo archive
Saves: indices_current.json, indices_history.json
"""

import urllib.request
import json
import time
import ssl
import certifi
from datetime import date, timedelta
from collections import defaultdict

CTX = ssl.create_default_context(cafile=certifi.where())

def fetch(url, timeout=30, retries=3):
    for attempt in range(retries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "RainPredictor/2.0"})
            with urllib.request.urlopen(req, timeout=timeout, context=CTX) as r:
                return r.read().decode("utf-8", errors="replace")
        except Exception as e:
            if attempt < retries - 1:
                print(f"    retry {attempt+2}/{retries} ({e})")
                time.sleep(8)
            else:
                raise

def fetch_json(url, timeout=60, retries=3):
    return json.loads(fetch(url, timeout, retries))

print("=" * 60)
print("  Climate Indices Fetcher v2")
print("=" * 60)

history = {}
current = {}

TODAY     = date.today()
YESTERDAY = TODAY - timedelta(days=1)

# ── 1. ARCTIC OSCILLATION (AO) ───────────────────────────
print("\n[1/8] Arctic Oscillation (AO)...")
try:
    txt = fetch("https://www.cpc.ncep.noaa.gov/products/precip/CWlink/daily_ao_index/monthly.ao.index.b50.current.ascii")
    ao_hist = {}
    latest_ao = None
    latest_ao_ym = None
    for line in txt.strip().splitlines():
        parts = line.split()
        if len(parts) >= 3:
            try:
                yr, mo, val = int(parts[0]), int(parts[1]), float(parts[2])
                if 2000 <= yr <= 2026:
                    ym = f"{yr}-{str(mo).zfill(2)}"
                    ao_hist[ym] = round(val, 3)
                    latest_ao = round(val, 3)
                    latest_ao_ym = ym
            except ValueError:
                continue
    history["ao"] = ao_hist
    sig = "wet" if latest_ao and latest_ao < -1.0 else ("dry" if latest_ao and latest_ao > 1.0 else "neutral")
    current["ao"] = {
        "value": latest_ao,
        "date": latest_ao_ym,
        "signal": sig,
        "label": "Arctic Oscillation",
        "unit": "index",
        "description": "Negative = polar vortex weakens, cold/stormy air invades Midwest",
        "favorable_for_rain": "negative"
    }
    print(f"  ✓ AO {latest_ao_ym}: {latest_ao:+.3f} → {sig}")
except Exception as e:
    print(f"  ✗ AO failed: {e}")
    current["ao"] = {"value": None, "signal": "unknown", "label": "Arctic Oscillation"}

# ── 2. NORTH ATLANTIC OSCILLATION (NAO) ──────────────────
print("[2/8] North Atlantic Oscillation (NAO)...")
try:
    txt = fetch("https://www.cpc.ncep.noaa.gov/products/precip/CWlink/pna/norm.nao.monthly.b5001.current.ascii")
    nao_hist = {}
    latest_nao = None
    latest_nao_ym = None
    for line in txt.strip().splitlines():
        parts = line.split()
        if len(parts) >= 3:
            try:
                yr, mo, val = int(parts[0]), int(parts[1]), float(parts[2])
                if 2000 <= yr <= 2026:
                    ym = f"{yr}-{str(mo).zfill(2)}"
                    nao_hist[ym] = round(val, 3)
                    latest_nao = round(val, 3)
                    latest_nao_ym = ym
            except ValueError:
                continue
    history["nao"] = nao_hist
    sig = "wet" if latest_nao and latest_nao < -1.0 else ("dry" if latest_nao and latest_nao > 1.0 else "neutral")
    current["nao"] = {
        "value": latest_nao,
        "date": latest_nao_ym,
        "signal": sig,
        "label": "North Atlantic Oscillation",
        "unit": "index",
        "description": "Negative NAO shifts storm track southward toward the US",
        "favorable_for_rain": "negative"
    }
    print(f"  ✓ NAO {latest_nao_ym}: {latest_nao:+.3f} → {sig}")
except Exception as e:
    print(f"  ✗ NAO failed: {e}")
    current["nao"] = {"value": None, "signal": "unknown", "label": "North Atlantic Oscillation"}

# ── 3. MJO ───────────────────────────────────────────────
print("[3/8] Madden-Julian Oscillation (MJO)...")
try:
    txt = fetch("https://www.cpc.ncep.noaa.gov/products/precip/CWlink/MJO/full_data_realtime.txt")
    mjo_hist = {}
    latest_mjo = None
    latest_mjo_date = None
    for line in txt.strip().splitlines():
        parts = line.split()
        if len(parts) >= 6:
            try:
                yr, mo, dy = int(parts[0]), int(parts[1]), int(parts[2])
                rmm1, rmm2 = float(parts[3]), float(parts[4])
                phase = int(float(parts[5]))
                amp = round((rmm1**2 + rmm2**2)**0.5, 3)
                d = f"{yr}-{str(mo).zfill(2)}-{str(dy).zfill(2)}"
                mjo_hist[d] = {"phase": phase, "amplitude": amp}
                latest_mjo = {"phase": phase, "amplitude": amp}
                latest_mjo_date = d
            except (ValueError, IndexError):
                continue
    history["mjo"] = mjo_hist
    if latest_mjo:
        p = latest_mjo["phase"]
        a = latest_mjo["amplitude"]
        if a < 1.0:
            sig = "neutral"
        elif p in [4, 5, 6]:
            sig = "wet"
        elif p in [1, 2, 8]:
            sig = "dry"
        else:
            sig = "neutral"
    else:
        sig = "unknown"
    current["mjo"] = {
        "value": latest_mjo,
        "date": latest_mjo_date,
        "signal": sig,
        "label": "Madden-Julian Oscillation",
        "unit": "phase + amplitude",
        "description": "Phases 4-6 with amplitude >1 enhance Midwest precipitation 2-3 weeks out",
        "favorable_for_rain": "phase 4-6, amplitude > 1"
    }
    if latest_mjo:
        print(f"  ✓ MJO {latest_mjo_date}: phase {latest_mjo['phase']} amp {latest_mjo['amplitude']:.2f} → {sig}")
    else:
        print("  ✗ MJO: no data parsed")
except Exception as e:
    print(f"  ✗ MJO failed: {e}")
    current["mjo"] = {"value": None, "signal": "unknown", "label": "Madden-Julian Oscillation"}

# ── 4. PDO ───────────────────────────────────────────────
print("[4/8] Pacific Decadal Oscillation (PDO)...")
try:
    txt = fetch("https://www.ncei.noaa.gov/pub/data/cmb/ersst/v5/index/ersst.v5.pdo.dat")
    pdo_hist = {}
    latest_pdo = None
    latest_pdo_ym = None
    for line in txt.strip().splitlines():
        parts = line.split()
        if len(parts) >= 13:
            try:
                yr = int(parts[0])
                if 2000 <= yr <= 2026:
                    for mo in range(1, 13):
                        val_str = parts[mo]
                        if val_str not in ("99.99", "-99.99", "999.99"):
                            val = float(val_str)
                            ym = f"{yr}-{str(mo).zfill(2)}"
                            pdo_hist[ym] = round(val, 3)
                            latest_pdo = round(val, 3)
                            latest_pdo_ym = ym
            except (ValueError, IndexError):
                continue
    history["pdo"] = pdo_hist
    sig = "wet" if latest_pdo and latest_pdo > 0.5 else ("dry" if latest_pdo and latest_pdo < -0.5 else "neutral")
    current["pdo"] = {
        "value": latest_pdo,
        "date": latest_pdo_ym,
        "signal": sig,
        "label": "Pacific Decadal Oscillation",
        "unit": "index",
        "description": "Positive PDO amplifies El Nino moisture patterns over North America",
        "favorable_for_rain": "positive"
    }
    print(f"  ✓ PDO {latest_pdo_ym}: {latest_pdo:+.3f} → {sig}")
except Exception as e:
    print(f"  ✗ PDO failed: {e}")
    current["pdo"] = {"value": None, "signal": "unknown", "label": "Pacific Decadal Oscillation"}

# ── 5. AMO ───────────────────────────────────────────────
print("[5/8] Atlantic Multidecadal Oscillation (AMO)...")
try:
    txt = fetch("https://psl.noaa.gov/data/correlation/amon.us.long.data")
    amo_hist = {}
    latest_amo = None
    latest_amo_ym = None
    for line in txt.strip().splitlines():
        parts = line.split()
        if not parts:
            continue
        try:
            yr = int(parts[0])
            if 2000 <= yr <= 2026 and len(parts) >= 13:
                for mo in range(1, 13):
                    val_str = parts[mo]
                    if val_str not in ("-99.990", "-99.99", "99.990"):
                        val = float(val_str)
                        ym = f"{yr}-{str(mo).zfill(2)}"
                        amo_hist[ym] = round(val, 4)
                        latest_amo = round(val, 4)
                        latest_amo_ym = ym
        except (ValueError, IndexError):
            continue
    history["amo"] = amo_hist
    sig = "wet" if latest_amo and latest_amo > 0.1 else ("dry" if latest_amo and latest_amo < -0.1 else "neutral")
    current["amo"] = {
        "value": latest_amo,
        "date": latest_amo_ym,
        "signal": sig,
        "label": "Atlantic Multidecadal Oscillation",
        "unit": "°C anomaly",
        "description": "Warm Atlantic SST increases moisture available for Midwest storms",
        "favorable_for_rain": "positive"
    }
    print(f"  ✓ AMO {latest_amo_ym}: {latest_amo:+.4f} → {sig}")
except Exception as e:
    print(f"  ✗ AMO failed: {e}")
    current["amo"] = {"value": None, "signal": "unknown", "label": "Atlantic Multidecadal Oscillation"}

# ── 6. GULF SST ───────────────────────────────────────────
print("[6/8] Gulf of Mexico Sea Surface Temperature...")
try:
    url = (
        "https://marine-api.open-meteo.com/v1/marine"
        "?latitude=25.0&longitude=-90.0"
        "&daily=sea_surface_temperature_max"
        f"&start_date=2024-01-01&end_date={TODAY.isoformat()}"
        "&timezone=UTC"
    )
    data = fetch_json(url)
    dates_sst = data["daily"]["time"]
    temps_sst = data["daily"]["sea_surface_temperature_max"]
    gulf_hist = {}
    latest_sst = None
    latest_sst_date = None
    for d, t in zip(dates_sst, temps_sst):
        if t is not None:
            gulf_hist[d] = round(t, 2)
            latest_sst = round(t, 2)
            latest_sst_date = d
    history["gulf_sst"] = gulf_hist
    baseline = 27.0
    sig = "wet" if latest_sst and latest_sst > baseline + 0.5 else ("dry" if latest_sst and latest_sst < baseline - 0.5 else "neutral")
    current["gulf_sst"] = {
        "value": latest_sst,
        "date": latest_sst_date,
        "signal": sig,
        "label": "Gulf of Mexico SST",
        "unit": "°C",
        "description": "Warmer Gulf increases moisture available for the low-level jet feeding Chicago",
        "favorable_for_rain": "> 27.5°C",
        "baseline": baseline
    }
    print(f"  ✓ Gulf SST {latest_sst_date}: {latest_sst}°C → {sig}")
except Exception as e:
    print(f"  ✗ Gulf SST failed: {e}")
    current["gulf_sst"] = {"value": None, "signal": "unknown", "label": "Gulf of Mexico SST"}

# ── 7. SURFACE RELATIVE HUMIDITY ─────────────────────────
print("[7/8] Surface Relative Humidity — Chicago...")
try:
    url = (
        "https://archive-api.open-meteo.com/v1/archive"
        "?latitude=41.85&longitude=-87.65"
        "&hourly=relative_humidity_2m"
        f"&start_date=2024-01-01&end_date={YESTERDAY.isoformat()}"
        "&timezone=America%2FChicago"
    )
    data = fetch_json(url, timeout=60)
    times_rh = data["hourly"]["time"]
    vals_rh  = data["hourly"]["relative_humidity_2m"]
    day_rh = defaultdict(list)
    for t, v in zip(times_rh, vals_rh):
        if v is not None:
            day_rh[t[:10]].append(v)
    rh_hist = {}
    latest_rh = None
    latest_rh_date = None
    for d in sorted(day_rh.keys()):
        mean_v = round(sum(day_rh[d]) / len(day_rh[d]), 1)
        rh_hist[d] = mean_v
        latest_rh = mean_v
        latest_rh_date = d
    history["humidity"] = rh_hist
    sig = "wet" if latest_rh and latest_rh > 75 else ("dry" if latest_rh and latest_rh < 50 else "neutral")
    current["tpw"] = {
        "value": latest_rh,
        "date": latest_rh_date,
        "signal": sig,
        "label": "Surface Relative Humidity",
        "unit": "%",
        "description": "High surface humidity means the atmosphere is close to saturation and rain-ready",
        "favorable_for_rain": "> 75%"
    }
    print(f"  ✓ Humidity {latest_rh_date}: {latest_rh}% → {sig}")
except Exception as e:
    print(f"  ✗ Humidity failed: {e}")
    current["tpw"] = {"value": None, "signal": "unknown", "label": "Surface Relative Humidity"}

# ── 8. 500MB GEOPOTENTIAL HEIGHT ─────────────────────────
print("[8/8] 500mb Geopotential Height — Chicago...")
try:
    url = (
        "https://archive-api.open-meteo.com/v1/archive"
        "?latitude=41.85&longitude=-87.65"
        "&hourly=geopotential_height_500hPa"
        f"&start_date=2024-01-01&end_date={YESTERDAY.isoformat()}"
        "&timezone=America%2FChicago"
    )
    data = fetch_json(url, timeout=90)
    times_z = data["hourly"]["time"]
    vals_z  = data["hourly"]["geopotential_height_500hPa"]
    day_z = defaultdict(list)
    for t, v in zip(times_z, vals_z):
        if v is not None:
            day_z[t[:10]].append(v)
    z500_hist = {}
    latest_z500 = None
    latest_z500_date = None
    for d in sorted(day_z.keys()):
        mean_v = round(sum(day_z[d]) / len(day_z[d]), 1)
        z500_hist[d] = mean_v
        latest_z500 = mean_v
        latest_z500_date = d
    history["z500"] = z500_hist
    baseline = 5500
    sig = "wet" if latest_z500 and latest_z500 < baseline - 60 else ("dry" if latest_z500 and latest_z500 > baseline + 60 else "neutral")
    current["z500"] = {
        "value": latest_z500,
        "date": latest_z500_date,
        "signal": sig,
        "label": "500mb Geopotential Height",
        "unit": "m",
        "description": "Low 500mb heights = upper-level trough = storm-favorable pattern over Chicago",
        "favorable_for_rain": "< 5440m",
        "typical_range": "5400-5640m"
    }
    print(f"  ✓ Z500 {latest_z500_date}: {latest_z500}m → {sig}")
except Exception as e:
    print(f"  ✗ Z500 failed: {e}")
    current["z500"] = {"value": None, "signal": "unknown", "label": "500mb Geopotential Height"}

# ── SAVE ─────────────────────────────────────────────────
print("\nSaving...")
with open("indices_current.json", "w") as f:
    json.dump(current, f, indent=2)
print("  ✓ indices_current.json")

with open("indices_history.json", "w") as f:
    json.dump(history, f, separators=(',', ':'))
print("  ✓ indices_history.json")

# ── SUMMARY ──────────────────────────────────────────────
print("\n" + "=" * 60)
print("  Current Signal Summary")
print("=" * 60)
emoji = {"wet": "🌧  WET", "dry": "☀️  DRY", "neutral": "⚪ neutral", "unknown": "❓ unknown"}
for key, info in current.items():
    sig = emoji.get(info.get("signal", "unknown"), "❓")
    val = info.get("value")
    if isinstance(val, dict):
        val_str = f"phase {val.get('phase')} amp {val.get('amplitude', 0):.2f}"
    elif isinstance(val, float):
        val_str = f"{val:+.2f}"
    elif val is not None:
        val_str = str(val)
    else:
        val_str = "n/a"
    print(f"  {info.get('label',''):<38} {val_str:<15} {sig}")

print("\n  Next step: run  python3 build_v2.py")
print("=" * 60)
