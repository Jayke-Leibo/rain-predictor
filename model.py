import json
import numpy as np
from sklearn.linear_model import LinearRegression
from xgboost import XGBRegressor
from sklearn.preprocessing import StandardScaler

# Load data
with open("data.json") as f:
    raw = json.load(f)

# Build dataset
X, y = [], []
for key, val in raw.items():
    year, month = map(int, key.split("-"))
    X.append([year, month, month**2])
    y.append(val)

X = np.array(X)
y = np.array(y)

# --- Layer 1: Weighted historical average (recent years weighted more) ---
def weighted_avg_predict(target_month):
    weights = {"2020": 1, "2021": 2, "2022": 3, "2023": 4, "2024": 5}
    total_weight = 0
    weighted_sum = 0
    for key, val in raw.items():
        year, month = key.split("-")
        if int(month) == target_month:
            w = weights.get(year, 1)
            weighted_sum += val * w
            total_weight += w
    return weighted_sum / total_weight if total_weight > 0 else 0

# --- Layer 2: Linear regression ---
lr = LinearRegression()
lr.fit(X, y)

# --- Layer 3: XGBoost ---
xgb = XGBRegressor(n_estimators=100, max_depth=3, learning_rate=0.1, verbosity=0)
xgb.fit(X, y)

# --- Blend all three for target month ---
THRESHOLDS_MM = [25.4, 50.8, 76.2, 101.6, 127.0]
THRESHOLD_LABELS = ["Above 1 inch", "Above 2 inches", "Above 3 inches", "Above 4 inches", "Above 5 inches"]

TARGET_YEAR = 2026
TARGET_MONTH = 3  # March

wa = weighted_avg_predict(TARGET_MONTH)
lr_pred = lr.predict([[TARGET_YEAR, TARGET_MONTH, TARGET_MONTH**2]])[0]
xgb_pred = xgb.predict([[TARGET_YEAR, TARGET_MONTH, TARGET_MONTH**2]])[0]

# Blend: 40% weighted avg, 30% linear, 30% XGBoost
blended = (wa * 0.4) + (lr_pred * 0.3) + (xgb_pred * 0.3)

print(f"\nPredictions for Chicago — March 2026")
print(f"{'='*45}")
print(f"  Weighted avg:     {wa:.1f}mm")
print(f"  Linear regression:{lr_pred:.1f}mm")
print(f"  XGBoost:          {xgb_pred:.1f}mm")
print(f"  BLENDED:          {blended:.1f}mm")
print(f"\nThreshold probabilities (based on blended prediction):")
print(f"{'-'*45}")

# Use historical variance to estimate probabilities
march_vals = [v for k, v in raw.items() if k.endswith("-03")]
std = np.std(march_vals)
mean = np.mean(march_vals)

results = {}
for label, thresh in zip(THRESHOLD_LABELS, THRESHOLDS_MM):
    # Probability using normal distribution around blended prediction
    from scipy import stats
    prob = 1 - stats.norm.cdf(thresh, loc=blended, scale=std)
    prob_pct = round(prob * 100)
    results[label] = prob_pct
    print(f"  {label:<20} {prob_pct}%")

# Save results
with open("model_predictions.json", "w") as f:
    json.dump({
        "month": "March 2026",
        "blended_mm": round(float(blended), 1),
        "weighted_avg_mm": round(float(wa), 1),
        "linear_mm": round(float(lr_pred), 1),
        "xgboost_mm": round(float(xgb_pred), 1),
        "probabilities": {k: int(v) for k, v in results.items()}
    }, f, indent=2)
    

print(f"\nSaved to model_predictions.json")
