"""
model_v2.py
Multi-variable rain prediction model for Chicago.
Features: temp, dew point, humidity, pressure trend, wind direction,
          cloud cover, ENSO, lag precip, calendar features.
Outputs: model_predictions_v2.json
"""

import json
import math
import numpy as np
from datetime import date as ddate
from scipy.stats import norm

# ── LOAD DATA ─────────────────────────────────────────────
print("=" * 55)
print("  Rain Predictor — Model v2")
print("  Multi-variable XGBoost + blended ensemble")
print("=" * 55)

with open("data_full.json") as f:
    daily = json.load(f)

with open("data_monthly_full.json") as f:
    monthly = json.load(f)

with open("enso.json") as f:
    enso = json.load(f)

print(f"\n  Loaded {len(daily):,} daily records")
print(f"  Loaded {len(monthly)} monthly totals")
print(f"  Loaded {len(enso)} ENSO values")

# ── FEATURE ENGINEERING ───────────────────────────────────
FEATURE_COLS = [
    "year", "month", "day_of_year", "week_of_year",
    "temperature_2m_max", "temperature_2m_min", "temperature_2m_mean",
    "temp_range", "apparent_temperature_mean",
    "humidity_mean", "dew_point_mean",
    "surface_pressure_mean", "pressure_trend",
    "wind_speed_10m_max", "wind_south_component",
    "cloud_cover_mean", "shortwave_radiation_sum",
    "precip_lag1", "precip_7d_total",
    "enso_oni",
]

def to_row(rec):
    return [rec.get(f) or 0.0 for f in FEATURE_COLS]

# ── BUILD TRAINING SET ────────────────────────────────────
print("\nBuilding training set...")

X, y = [], []
dates_train = sorted(daily.keys())

for date in dates_train:
    rec = daily[date]
    precip = rec.get("precipitation_sum")
    if precip is None:
        continue
    X.append(to_row(rec))
    y.append(precip)

X = np.array(X, dtype=np.float32)
y = np.array(y, dtype=np.float32)
print(f"  Training rows : {len(X):,}")
print(f"  Features      : {len(FEATURE_COLS)}")
print(f"  Rainy days    : {(y > 1).sum():,} ({100*(y>1).mean():.1f}%)")

# ── MONTHLY AGGREGATION HELPER ────────────────────────────
def monthly_totals_from_daily(pred_dict):
    """Sum daily predictions into monthly totals."""
    monthly_pred = {}
    for date, val in pred_dict.items():
        ym = date[:7]
        monthly_pred[ym] = monthly_pred.get(ym, 0.0) + val
    return {k: round(v, 2) for k, v in monthly_pred.items()}

# ── MODEL 1: WEIGHTED HISTORICAL MONTHLY AVERAGE ──────────
print("\n[1/4] Weighted historical monthly average...")

# Weight: exponential decay, most recent = highest weight
year_weights = {}
base_year = 2024
for ym, total in monthly.items():
    y_int = int(ym[:4])
    age = base_year - y_int
    year_weights[ym] = math.exp(-0.2 * age)  # decay factor 0.2

def weighted_avg_for_month(month_int):
    vals, weights = [], []
    for ym, total in monthly.items():
        if int(ym[5:7]) == month_int:
            vals.append(total)
            weights.append(year_weights[ym])
    if not vals:
        return 0.0
    w = np.array(weights)
    v = np.array(vals)
    return float(np.average(v, weights=w))

monthly_wavg = {f"2026-{str(m).zfill(2)}": weighted_avg_for_month(m) for m in range(1, 13)}
print(f"  ✓ Weighted averages computed for all 12 months")

# ── MODEL 2: LINEAR REGRESSION (monthly level) ────────────
print("[2/4] Linear regression on monthly totals...")
from sklearn.linear_model import Ridge
from sklearn.preprocessing import StandardScaler

Xlr, ylr = [], []
for ym, total in monthly.items():
    yr = int(ym[:4])
    mo = int(ym[5:7])
    enso_val = enso.get(ym, 0.0) or 0.0
    # Month encoded as sin/cos to capture cyclicality
    Xlr.append([yr, math.sin(2*math.pi*mo/12), math.cos(2*math.pi*mo/12), mo, enso_val])
    ylr.append(total)

Xlr = np.array(Xlr)
ylr = np.array(ylr)
scaler_lr = StandardScaler()
Xlr_s = scaler_lr.fit_transform(Xlr)

lr = Ridge(alpha=1.0)
lr.fit(Xlr_s, ylr)

monthly_lr = {}
for m in range(1, 13):
    enso_val = enso.get(f"2026-{str(m).zfill(2)}", 0.0) or 0.0
    xp = np.array([[2026, math.sin(2*math.pi*m/12), math.cos(2*math.pi*m/12), m, enso_val]])
    pred = lr.predict(scaler_lr.transform(xp))[0]
    monthly_lr[f"2026-{str(m).zfill(2)}"] = max(0.0, round(float(pred), 2))

print(f"  ✓ Ridge regression trained on {len(ylr)} monthly observations")

# ── MODEL 3: XGBOOST (daily level → aggregated monthly) ───
print("[3/4] XGBoost on daily features...")
try:
    import xgboost as xgb
    from sklearn.model_selection import TimeSeriesSplit

    tscv = TimeSeriesSplit(n_splits=5)
    xgb_params = {
        "n_estimators": 400,
        "max_depth": 5,
        "learning_rate": 0.05,
        "subsample": 0.8,
        "colsample_bytree": 0.8,
        "min_child_weight": 3,
        "reg_alpha": 0.1,
        "reg_lambda": 1.0,
        "random_state": 42,
        "n_jobs": -1,
        "verbosity": 0,
    }

    model_xgb = xgb.XGBRegressor(**xgb_params)
    model_xgb.fit(X, y, eval_set=[(X, y)], verbose=False)

    # Feature importance
    imp = model_xgb.feature_importances_
    top5 = sorted(zip(FEATURE_COLS, imp), key=lambda x: -x[1])[:5]
    print(f"  ✓ XGBoost trained")
    print(f"  Top features: {', '.join(f[0] for f in top5)}")

    # Predict for each day in 2026 using typical values
    # Use average of same month across all years as proxy features
    xgb_available = True

except ImportError:
    print("  ✗ XGBoost not installed — run: pip3 install xgboost --break-system-packages")
    xgb_available = False

# ── BUILD 2026 MONTHLY PREDICTIONS ────────────────────────
print("\n[4/4] Building 2026 monthly predictions...")

month_names = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"]
results = {}

for m in range(1, 13):
    ym_key = f"2026-{str(m).zfill(2)}"
    wa = monthly_wavg[ym_key]
    lr_pred = monthly_lr[ym_key]

    if xgb_available:
        # Build a synthetic "typical day" for this month using historical mean features
        month_days = [d for d in daily.values() if d.get("month") == m]
        if month_days:
            def safe_mean(key):
                vals = [r.get(key) for r in month_days if r.get(key) is not None]
                return float(np.mean(vals)) if vals else 0.0
            
            synthetic = {f: safe_mean(f) for f in FEATURE_COLS}
            synthetic["year"] = 2026
            synthetic["month"] = m
            # Estimate days in month
            days_in_month = [31,28,31,30,31,30,31,31,30,31,30,31][m-1]
            synthetic["day_of_year"] = sum([31,28,31,30,31,30,31,31,30,31,30,31][:m-1]) + 15
            # Get latest ENSO estimate (use last known value)
            synthetic["enso_oni"] = enso.get(f"2025-{str(m).zfill(2)}") or enso.get(f"2024-{str(m).zfill(2)}") or 0.0

            xrow = np.array([to_row(synthetic)], dtype=np.float32)
            daily_xgb = float(model_xgb.predict(xrow)[0])
            xgb_pred = max(0.0, round(daily_xgb * days_in_month, 2))
        else:
            xgb_pred = wa
        
        # Blended: 40% weighted avg, 30% linear, 30% xgboost
        blended = round(0.40 * wa + 0.30 * lr_pred + 0.30 * xgb_pred, 2)
    else:
        xgb_pred = None
        blended = round(0.57 * wa + 0.43 * lr_pred, 2)

    # Historical stats for this month (for probability calc)
    hist_vals = [monthly[ym] for ym in monthly if int(ym[5:7]) == m]
    hist_mean = float(np.mean(hist_vals))
    hist_std  = float(np.std(hist_vals))

    # Probability of exceeding each inch threshold
    INCH_THRESHOLDS = [1,2,3,4,5,6,7]
    thresholds = {}
    for inches in INCH_THRESHOLDS:
        mm = inches * 25.4
        if hist_std > 0:
            prob = round(float(1 - norm.cdf(mm, loc=blended, scale=hist_std)) * 100, 1)
        else:
            prob = 100.0 if blended >= mm else 0.0
        prob = max(0.0, min(100.0, prob))
        thresholds[f"Above {inches} inch{'es' if inches>1 else ''}"] = prob

    results[ym_key] = {
        "month_name": month_names[m-1],
        "month_num": m,
        "weighted_avg_mm": round(wa, 2),
        "linear_mm": round(lr_pred, 2),
        "xgboost_mm": round(xgb_pred, 2) if xgb_pred is not None else None,
        "blended_mm": blended,
        "hist_mean_mm": round(hist_mean, 2),
        "hist_std_mm": round(hist_std, 2),
        "thresholds": thresholds,
    }

# ── PRINT SUMMARY ─────────────────────────────────────────
print("\n" + "=" * 55)
print("  2026 Monthly Predictions")
print("=" * 55)
print(f"  {'Month':<6} {'WAvg':>7} {'LR':>7} {'XGB':>7} {'Blend':>7}")
print("  " + "-" * 38)
for m in range(1, 13):
    ym = f"2026-{str(m).zfill(2)}"
    r = results[ym]
    xgb_str = f"{r['xgboost_mm']:>7.1f}" if r['xgboost_mm'] is not None else "    n/a"
    print(f"  {r['month_name']:<6} {r['weighted_avg_mm']:>7.1f} {r['linear_mm']:>7.1f} {xgb_str} {r['blended_mm']:>7.1f}")

print("\n  March 2026 threshold probabilities:")
mar = results["2026-03"]
for label, prob in mar["thresholds"].items():
    bar = "█" * int(prob / 5)
    print(f"    {label:<18} {prob:>5.1f}%  {bar}")

# ── SAVE ──────────────────────────────────────────────────
with open("model_predictions_v2.json", "w") as f:
    json.dump(results, f, indent=2)

print(f"\n  ✓ Saved model_predictions_v2.json")
print("\n  Next step: run  python3 build_v2.py")
print("=" * 55)
