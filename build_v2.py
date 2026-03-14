"""
build_v2.py
Reads data_full.json, data_monthly_full.json, model_predictions_v2.json
and generates index.html + dashboard.html
"""
import json

print("Reading data files...")

with open("data_monthly_full.json") as f:
    monthly = json.load(f)

with open("data_full.json") as f:
    daily_full = json.load(f)

with open("model_predictions_v2.json") as f:
    predictions = json.load(f)

try:
    with open("indices_current.json") as f:
        indices = json.load(f)
except FileNotFoundError:
    indices = {}

# Build compact daily precip dict {date: mm}
daily_precip = {d: round(r.get("precipitation_sum") or 0, 2) for d, r in daily_full.items()}

# Kalshi data (March 2026 - run kalshi.py to refresh)
kalshi = {
    "Above 1 inch": 100,
    "Above 2 inches": 99,
    "Above 3 inches": 90,
    "Above 4 inches": 58,
    "Above 5 inches": 18,
    "Above 6 inches": 5,
    "Above 7 inches": 1,
}

monthly_js   = json.dumps(monthly,      separators=(',',':'))
daily_js     = json.dumps(daily_precip, separators=(',',':'))
pred_js      = json.dumps(predictions,  separators=(',',':'))
kalshi_js    = json.dumps(kalshi,        separators=(',',':'))
indices_js   = json.dumps(indices,       separators=(',',':'))

print(f"  {len(monthly)} monthly totals")
print(f"  {len(daily_precip)} daily records")
print(f"  {len(predictions)} monthly predictions")

HTML = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Rain Predictor — Chicago</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=DM+Mono:wght@400;500&family=Inter:wght@400;500;600;700;800&display=swap" rel="stylesheet">
<script src="https://cdnjs.cloudflare.com/ajax/libs/Chart.js/4.4.1/chart.umd.min.js"></script>
<style>
:root {
  --bg:        #f5f2ec;
  --surface:   #ffffff;
  --surface2:  #f0ece3;
  --border:    #e4ddd0;
  --border2:   #cfc8b8;
  --navy:      #1c2333;
  --navy2:     #3d4a60;
  --sky:       #0284c7;
  --sky-light: #e0f2fe;
  --sky-mid:   #7dd3fc;
  --amber:     #b45309;
  --amber-bg:  #fef3c7;
  --amber-bdr: #fde68a;
  --green:     #047857;
  --green-bg:  #d1fae5;
  --green-bdr: #6ee7b7;
  --red:       #b91c1c;
  --red-bg:    #fee2e2;
  --red-bdr:   #fca5a5;
  --muted:     #6b7280;
  --muted2:    #9ca3af;
}
*{box-sizing:border-box;margin:0;padding:0}
body{font-family:'Inter',sans-serif;background:var(--bg);color:var(--navy);min-height:100vh}

/* ── HEADER ── */
header{
  background:var(--surface);border-bottom:1px solid var(--border);
  padding:0 2rem;display:flex;align-items:stretch;
  position:sticky;top:0;z-index:100;
  box-shadow:0 1px 4px rgba(0,0,0,0.07);
}
.logo-area{
  display:flex;align-items:center;gap:10px;
  padding:0.85rem 1.4rem 0.85rem 0;
  border-right:1px solid var(--border);margin-right:0.5rem;
}
.logo-icon{
  width:32px;height:32px;
  background:linear-gradient(135deg,#0ea5e9,#0284c7);
  border-radius:8px;display:flex;align-items:center;justify-content:center;font-size:16px;
}
.logo-text h1{font-size:0.88rem;font-weight:700;color:var(--navy)}
.logo-text p{font-size:0.6rem;color:var(--muted);font-family:'DM Mono',monospace;margin-top:1px}
nav{display:flex;align-items:stretch;flex:1}
.tab-btn{
  display:flex;align-items:center;gap:7px;padding:0 1.1rem;
  font-size:0.78rem;font-weight:500;color:var(--muted);
  background:none;border:none;border-bottom:2px solid transparent;
  cursor:pointer;transition:color .15s,border-color .15s;white-space:nowrap;
}
.tab-btn:hover{color:var(--navy)}
.tab-btn.active{color:var(--navy);border-bottom-color:var(--sky);font-weight:600}
.live-badge{
  display:flex;align-items:center;gap:5px;margin-left:auto;
  font-family:'DM Mono',monospace;font-size:0.6rem;color:var(--green);padding:0 0.5rem;
}
.live-dot{width:5px;height:5px;border-radius:50%;background:var(--green);animation:blink 2s infinite}
@keyframes blink{0%,100%{opacity:1}50%{opacity:.3}}

/* ── LAYOUT ── */
.container{max-width:1140px;margin:0 auto;padding:1.5rem}
.tab-content{display:none}
.tab-content.active{display:block}
.page-title{font-size:1.05rem;font-weight:700;color:var(--navy);margin-bottom:3px}
.page-sub{font-size:0.68rem;color:var(--muted);font-family:'DM Mono',monospace;margin-bottom:1.4rem}

/* ── CONTROLS ── */
.controls{display:flex;gap:10px;align-items:center;margin-bottom:1.2rem;flex-wrap:wrap}
.ctrl-label{font-size:0.65rem;font-weight:600;color:var(--muted);text-transform:uppercase;letter-spacing:.08em}
select{
  background:var(--surface);border:1px solid var(--border);color:var(--navy);
  font-family:'Inter',sans-serif;font-size:0.8rem;font-weight:500;
  padding:7px 12px;border-radius:8px;cursor:pointer;outline:none;
  box-shadow:0 1px 2px rgba(0,0,0,0.04);
}
select:hover{border-color:var(--sky)}
select:focus{border-color:var(--sky);box-shadow:0 0 0 3px rgba(2,132,199,.12)}

/* ── STAT CARDS ── */
.stats-grid{display:grid;grid-template-columns:repeat(4,1fr);gap:10px;margin-bottom:1.2rem}
.stat-card{
  background:var(--surface);border:1px solid var(--border);
  border-radius:12px;padding:1rem 1.1rem;
  box-shadow:0 1px 3px rgba(0,0,0,0.05);
}
.stat-label{font-size:0.58rem;font-weight:600;color:var(--muted);text-transform:uppercase;letter-spacing:.1em;margin-bottom:7px}
.stat-value{font-size:1.65rem;font-weight:800;letter-spacing:-.04em;line-height:1}
.stat-sub{font-family:'DM Mono',monospace;font-size:0.6rem;color:var(--muted);margin-top:5px}
.c-sky .stat-value{color:var(--sky)}
.c-green .stat-value{color:var(--green)}
.c-amber .stat-value{color:var(--amber)}
.c-purple .stat-value{color:#6d28d9}

/* ── MONTH STRIP ── */
.month-strip{display:grid;grid-template-columns:repeat(12,1fr);gap:5px;margin-bottom:1.2rem}
.month-cell{
  background:var(--surface);border:1px solid var(--border);
  border-radius:8px;padding:7px 3px;text-align:center;cursor:pointer;
  transition:all .12s;box-shadow:0 1px 2px rgba(0,0,0,0.03);
}
.month-cell:hover{border-color:var(--sky);background:var(--sky-light)}
.month-cell.active{border-color:var(--sky);background:var(--sky-light)}
.month-cell .mn{font-size:0.55rem;font-weight:600;color:var(--muted);text-transform:uppercase;letter-spacing:.05em}
.month-cell .mv{font-family:'DM Mono',monospace;font-size:0.75rem;font-weight:700;margin-top:3px;color:var(--navy)}
.month-cell.active .mv{color:var(--sky)}

/* ── CARDS ── */
.card{
  background:var(--surface);border:1px solid var(--border);
  border-radius:14px;padding:1.3rem;margin-bottom:1.2rem;
  box-shadow:0 1px 3px rgba(0,0,0,0.06);
}
.card-header{display:flex;justify-content:space-between;align-items:center;margin-bottom:1rem}
.card-header h2{font-size:0.82rem;font-weight:600;color:var(--navy)}
.tag{
  font-family:'DM Mono',monospace;font-size:0.56rem;
  padding:3px 8px;border-radius:5px;
  background:var(--surface2);color:var(--muted);border:1px solid var(--border);
}
.two-col{display:grid;grid-template-columns:1fr 1fr;gap:1.2rem;margin-bottom:1.2rem}
@keyframes fadeIn{from{opacity:0;transform:translateY(4px)}to{opacity:1;transform:translateY(0)}}

/* ── PREDICTION HERO ── */
.pred-hero{
  background:linear-gradient(135deg,#f0f9ff 0%,#fffbeb 100%);
  border:1px solid var(--border);border-radius:16px;
  padding:1.8rem;margin-bottom:1.2rem;
  display:flex;justify-content:space-between;align-items:flex-start;
}
.pred-hero-left h2{font-size:1rem;font-weight:700;color:var(--navy);margin-bottom:4px}
.pred-hero-left p{font-size:0.68rem;color:var(--muted);font-family:'DM Mono',monospace}
.pred-mm{font-size:2.8rem;font-weight:800;letter-spacing:-.06em;color:var(--sky);line-height:1}
.pred-mm-sub{font-family:'DM Mono',monospace;font-size:0.62rem;color:var(--muted);margin-top:4px;text-align:right}

.pred-month-select{display:flex;align-items:center;gap:10px;margin-bottom:1.3rem}

/* ── PRED SOURCE CARDS ── */
.pred-sources{display:grid;grid-template-columns:repeat(3,1fr);gap:10px;margin-bottom:1.2rem}
.psc{background:var(--surface);border:1px solid var(--border);border-radius:12px;padding:1rem 1.1rem;box-shadow:0 1px 3px rgba(0,0,0,0.05)}
.psc-label{font-size:0.56rem;font-weight:600;color:var(--muted);text-transform:uppercase;letter-spacing:.1em;margin-bottom:6px}
.psc-val{font-family:'DM Mono',monospace;font-size:1.3rem;font-weight:700;color:var(--navy)}
.psc-note{font-size:0.6rem;color:var(--muted);margin-top:2px}
.psc-weight{display:inline-block;margin-top:5px;background:var(--sky-light);color:var(--sky);border-radius:4px;padding:2px 7px;font-family:'DM Mono',monospace;font-size:0.56rem;font-weight:600}

/* ── PROB BARS ── */
.prob-card{background:var(--surface);border:1px solid var(--border);border-radius:14px;padding:1.3rem;margin-bottom:1.2rem;box-shadow:0 1px 3px rgba(0,0,0,0.06)}
.prob-card-header{display:flex;justify-content:space-between;align-items:center;margin-bottom:1.2rem;flex-wrap:wrap;gap:8px}
.prob-card-header h2{font-size:0.82rem;font-weight:600;color:var(--navy)}
.prob-legend{display:flex;gap:12px}
.prob-legend-item{display:flex;align-items:center;gap:5px;font-size:0.6rem;color:var(--muted);font-family:'DM Mono',monospace}
.prob-legend-dot{width:8px;height:8px;border-radius:2px}
.prob-row{margin-bottom:1.1rem}
.prob-row:last-child{margin-bottom:0}
.prob-row-header{display:flex;justify-content:space-between;align-items:baseline;margin-bottom:6px}
.prob-row-label{font-size:0.8rem;font-weight:600;color:var(--navy)}
.prob-row-mm{font-family:'DM Mono',monospace;font-size:0.6rem;color:var(--muted2)}
.prob-bars{display:flex;flex-direction:column;gap:4px}
.prob-bar-row{display:flex;align-items:center;gap:10px}
.prob-bar-src{font-family:'DM Mono',monospace;font-size:0.56rem;color:var(--muted);width:36px;text-align:right}
.prob-bar-track{flex:1;height:8px;background:var(--surface2);border-radius:5px;overflow:hidden;border:1px solid var(--border)}
.prob-bar-fill{height:100%;border-radius:4px;transition:width .6s cubic-bezier(.4,0,.2,1)}
.prob-bar-pct{font-family:'DM Mono',monospace;font-size:0.62rem;font-weight:700;width:36px}

/* ── KALSHI LINK ── */
.kalshi-link-card{
  background:linear-gradient(135deg,#fffbeb,#fef3c7);
  border:1px solid var(--amber-bdr);border-radius:14px;
  padding:1.1rem 1.4rem;margin-bottom:1.2rem;
  display:flex;justify-content:space-between;align-items:center;gap:1rem;
}
.klc-left h3{font-size:0.85rem;font-weight:600;color:var(--navy);margin-bottom:3px}
.klc-left p{font-size:0.65rem;color:var(--muted);font-family:'DM Mono',monospace}
.klc-btn{
  background:var(--amber);color:white;border:none;border-radius:8px;
  padding:9px 18px;font-size:0.78rem;font-weight:600;cursor:pointer;
  text-decoration:none;display:inline-block;transition:background .15s;white-space:nowrap;
}
.klc-btn:hover{background:#92400e}

/* ── EDGE TABLE ── */
.edge-card{background:var(--surface);border:1px solid var(--border);border-radius:14px;overflow:hidden;margin-bottom:1.2rem;box-shadow:0 1px 3px rgba(0,0,0,0.06)}
.edge-card-header{padding:1rem 1.3rem;border-bottom:1px solid var(--border);display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:8px}
.edge-card-header h2{font-size:0.82rem;font-weight:600}
.edge-badges-legend{display:flex;gap:6px}
.edge-col-headers{
  display:grid;grid-template-columns:1fr 80px 80px 140px;
  gap:10px;padding:8px 1.3rem;
  background:var(--surface2);border-bottom:1px solid var(--border);
}
.edge-col-headers span{font-size:0.56rem;font-weight:600;color:var(--muted);text-transform:uppercase;letter-spacing:.1em;text-align:center}
.edge-col-headers span:first-child{text-align:left}
.edge-row{
  display:grid;grid-template-columns:1fr 80px 80px 140px;
  gap:10px;align-items:center;
  padding:11px 1.3rem;border-bottom:1px solid var(--border);
  transition:background .1s;
}
.edge-row:last-child{border-bottom:none}
.edge-row:hover{background:var(--surface2)}
.edge-thresh{font-size:0.8rem;font-weight:600;color:var(--navy)}
.edge-thresh small{display:block;font-family:'DM Mono',monospace;font-size:0.56rem;color:var(--muted);margin-top:2px;font-weight:400}
.edge-prob{font-family:'DM Mono',monospace;font-size:0.9rem;font-weight:700;text-align:center}
.edge-badge{font-family:'DM Mono',monospace;font-size:0.65rem;font-weight:700;padding:6px 10px;border-radius:8px;text-align:center;line-height:1.5}
.badge-yes{background:var(--green-bg);color:var(--green);border:1px solid var(--green-bdr)}
.badge-no{background:var(--red-bg);color:var(--red);border:1px solid var(--red-bdr)}
.badge-neu{background:var(--surface2);color:var(--muted);border:1px solid var(--border)}

.info-note{
  font-family:'DM Mono',monospace;font-size:0.6rem;color:var(--muted);
  background:var(--surface2);border:1px solid var(--border);
  border-radius:8px;padding:8px 12px;margin-bottom:1.2rem;line-height:1.7;
}
/* ── SIGNAL CARDS ── */
.signals-grid{display:grid;grid-template-columns:repeat(2,1fr);gap:14px;margin-bottom:1.4rem}
.signal-card{
  background:var(--surface);border:1px solid var(--border);
  border-radius:16px;padding:1.4rem 1.5rem;
  box-shadow:0 2px 8px rgba(0,0,0,0.06);
  position:relative;overflow:hidden;
  transition:transform .15s,box-shadow .15s;
}
.signal-card:hover{transform:translateY(-2px);box-shadow:0 6px 20px rgba(0,0,0,0.1)}
.signal-card.sig-wet{background:linear-gradient(135deg,#f0f9ff 0%,#ffffff 60%);border-color:#bae6fd}
.signal-card.sig-dry{background:linear-gradient(135deg,#fffbeb 0%,#ffffff 60%);border-color:#fde68a}
.signal-card.sig-neutral{background:#ffffff}
.signal-card.sig-unknown{background:#fafafa}
.sc-top{display:flex;justify-content:space-between;align-items:flex-start;margin-bottom:1rem}
.sc-left{}
.sc-label{font-size:0.58rem;font-weight:700;color:var(--muted);text-transform:uppercase;letter-spacing:.12em;margin-bottom:5px}
.sc-name{font-size:0.9rem;font-weight:700;color:var(--navy)}
.sc-emoji{font-size:2.2rem;line-height:1;opacity:0.85}
.sc-mid{display:flex;align-items:baseline;gap:8px;margin-bottom:6px}
.sc-value{font-family:'DM Mono',monospace;font-size:1.6rem;font-weight:700;color:var(--navy);letter-spacing:-.02em}
.sc-unit{font-family:'DM Mono',monospace;font-size:0.65rem;color:var(--muted);font-weight:400}
.sc-date{font-family:'DM Mono',monospace;font-size:0.56rem;color:var(--muted2);margin-bottom:10px}
.sc-gauge{height:5px;background:var(--surface2);border-radius:3px;overflow:hidden;margin-bottom:10px;border:1px solid var(--border)}
.sc-gauge-fill{height:100%;border-radius:3px;transition:width .8s cubic-bezier(.4,0,.2,1)}
.sc-bottom{display:flex;justify-content:space-between;align-items:center;padding-top:10px;border-top:1px solid var(--border)}
.sc-badge{display:inline-flex;align-items:center;gap:5px;font-family:'DM Mono',monospace;font-size:0.62rem;font-weight:700;padding:4px 10px;border-radius:6px}
.sc-badge.sig-wet{background:var(--sky-light);color:var(--sky);border:1px solid #7dd3fc}
.sc-badge.sig-dry{background:var(--amber-bg);color:var(--amber);border:1px solid var(--amber-bdr)}
.sc-badge.sig-neutral{background:var(--surface2);color:var(--muted);border:1px solid var(--border)}
.sc-badge.sig-unknown{background:var(--surface2);color:var(--muted2);border:1px solid var(--border)}
.sc-desc{font-size:0.62rem;color:var(--muted);line-height:1.5;max-width:260px;text-align:right}

/* ── SIGNAL SUMMARY BAR ── */
.signal-summary{
  background:var(--surface);border:1px solid var(--border);
  border-radius:16px;padding:1.4rem 1.8rem;margin-bottom:1.4rem;
  box-shadow:0 2px 8px rgba(0,0,0,0.05);
}
.ss-top{display:flex;justify-content:space-between;align-items:center;margin-bottom:1.2rem}
.ss-title{font-size:0.82rem;font-weight:700;color:var(--navy)}
.ss-date{font-family:'DM Mono',monospace;font-size:0.6rem;color:var(--muted)}
.ss-counts{display:flex;gap:1.5rem;margin-bottom:1rem}
.ss-item{display:flex;align-items:center;gap:8px}
.ss-dot{width:10px;height:10px;border-radius:50%}
.ss-count{font-size:1.4rem;font-weight:800;letter-spacing:-.03em;line-height:1}
.ss-label{font-size:0.6rem;color:var(--muted);font-family:'DM Mono',monospace;margin-top:1px}
.ss-bar-wrap{margin-bottom:0.5rem}
.ss-bar-track{height:10px;background:var(--surface2);border-radius:5px;overflow:hidden;border:1px solid var(--border);position:relative}
.ss-bar-wet{position:absolute;left:0;top:0;height:100%;background:linear-gradient(90deg,#0284c7,#38bdf8);border-radius:5px 0 0 5px;transition:width .8s cubic-bezier(.4,0,.2,1)}
.ss-bar-dry{position:absolute;right:0;top:0;height:100%;background:linear-gradient(270deg,#b45309,#fbbf24);border-radius:0 5px 5px 0;transition:width .8s cubic-bezier(.4,0,.2,1)}
.ss-bar-labels{display:flex;justify-content:space-between;margin-top:5px}
.ss-bar-label{font-family:'DM Mono',monospace;font-size:0.56rem;color:var(--muted)}
.overall-verdict{
  margin-top:1rem;padding:0.9rem 1.2rem;border-radius:10px;
  display:flex;align-items:center;justify-content:space-between;
}
.ov-wet{background:var(--sky-light);border:1px solid #7dd3fc}
.ov-dry{background:var(--amber-bg);border:1px solid var(--amber-bdr)}
.ov-neutral{background:var(--surface2);border:1px solid var(--border)}
.ov-label{font-size:0.6rem;font-weight:600;color:var(--muted);text-transform:uppercase;letter-spacing:.08em}
.ov-value{font-size:0.9rem;font-weight:700}
canvas{max-width:100%}
</style>
</head>
<body>

<header>
  <div class="logo-area">
    <div class="logo-icon">🌧</div>
    <div class="logo-text">
      <h1>Rain Predictor</h1>
      <p>Chicago, IL · NOAA + Kalshi</p>
    </div>
  </div>
  <nav>
    <button class="tab-btn active" data-tab="historical" onclick="showTab('historical')">Historical</button>
    <button class="tab-btn" data-tab="predictions" onclick="showTab('predictions')">Predictions</button>
    <button class="tab-btn" data-tab="edge" onclick="showTab('edge')">Kalshi Edge</button>
    <button class="tab-btn" data-tab="signals" onclick="showTab('signals')">Climate Signals</button>
  </nav>
  <div class="live-badge"><div class="live-dot"></div>live</div>
</header>

<div class="container">

<!-- ══ TAB 1: HISTORICAL ══════════════════════════════════ -->
<div id="tab-historical" class="tab-content active">
  <p class="page-title">Historical Rainfall</p>
  <p class="page-sub">Chicago, IL · 2000–2024 · 25 years · Open-Meteo / NOAA</p>

  <div class="controls">
    <span class="ctrl-label">Year</span>
    <select id="yearSelect" onchange="renderHistorical()">
      <option value="all">25-yr average</option>
    </select>
  </div>

  <div class="stats-grid">
    <div class="stat-card c-sky">
      <div class="stat-label">Wettest Month</div>
      <div class="stat-value" id="wettestMonth">—</div>
      <div class="stat-sub" id="wettestVal">—</div>
    </div>
    <div class="stat-card c-green">
      <div class="stat-label">Driest Month</div>
      <div class="stat-value" id="driestMonth">—</div>
      <div class="stat-sub" id="driestVal">—</div>
    </div>
    <div class="stat-card c-amber">
      <div class="stat-label">Annual Total</div>
      <div class="stat-value" id="annualTotal">—</div>
      <div class="stat-sub" id="annualSub">—</div>
    </div>
    <div class="stat-card c-purple">
      <div class="stat-label">25yr Monthly Avg</div>
      <div class="stat-value" id="globalAvg">—</div>
      <div class="stat-sub">all months 2000–2024</div>
    </div>
  </div>

  <div class="month-strip" id="monthStrip"></div>

  <div class="card">
    <div class="card-header">
      <h2 id="barChartTitle">Monthly Rainfall</h2>
      <span class="tag">click bar or month to see daily breakdown</span>
    </div>
    <canvas id="barChart" height="75"></canvas>
  </div>

  <div id="dailySection" style="display:none;animation:fadeIn .2s ease">
    <div class="card">
      <div class="card-header">
        <h2 id="dailyTitle">Daily Rainfall</h2>
        <span class="tag">25yr average by day of month</span>
      </div>
      <canvas id="dailyChart" height="75"></canvas>
    </div>
  </div>

  <div class="two-col">
    <div class="card">
      <div class="card-header">
        <h2>Year-over-year comparison</h2>
        <span class="tag">monthly totals</span>
      </div>
      <canvas id="lineChart" height="155"></canvas>
    </div>
    <div class="card">
      <div class="card-header">
        <h2>Annual totals 2000–2024</h2>
        <span class="tag">mm per year</span>
      </div>
      <canvas id="annualChart" height="155"></canvas>
    </div>
  </div>
</div>

<!-- ══ TAB 2: PREDICTIONS ════════════════════════════════ -->
<div id="tab-predictions" class="tab-content">
  <p class="page-title">Model Predictions</p>
  <p class="page-sub">Blended forecast · weighted avg + ridge regression + XGBoost · 25 years training data</p>

  <div class="pred-month-select">
    <span class="ctrl-label">Month</span>
    <select id="predMonthSelect" onchange="renderPredictions()">
      <option value="2026-01">January 2026</option>
      <option value="2026-02">February 2026</option>
      <option value="2026-03" selected>March 2026</option>
      <option value="2026-04">April 2026</option>
      <option value="2026-05">May 2026</option>
      <option value="2026-06">June 2026</option>
      <option value="2026-07">July 2026</option>
      <option value="2026-08">August 2026</option>
      <option value="2026-09">September 2026</option>
      <option value="2026-10">October 2026</option>
      <option value="2026-11">November 2026</option>
      <option value="2026-12">December 2026</option>
    </select>
  </div>

  <div class="pred-hero" id="predHero">
    <div class="pred-hero-left">
      <h2 id="predHeroTitle">March 2026 Forecast — Chicago</h2>
      <p>3-model blend · trained on 25yr NOAA/Open-Meteo data · 20 features</p>
    </div>
    <div>
      <div class="pred-mm" id="predHeroMM">—</div>
      <div class="pred-mm-sub">mm predicted total</div>
    </div>
  </div>

  <div class="pred-sources" id="predSources"></div>

  <div class="prob-card">
    <div class="prob-card-header">
      <h2>Threshold probabilities</h2>
      <div class="prob-legend">
        <div class="prob-legend-item"><div class="prob-legend-dot" style="background:#0284c7"></div>Our model</div>
        <div class="prob-legend-item"><div class="prob-legend-dot" style="background:#b45309"></div>Kalshi market</div>
      </div>
    </div>
    <div id="probRows"></div>
  </div>

  <div class="card">
    <div class="card-header">
      <h2 id="predChartTitle">Historical March totals + 2026 prediction</h2>
      <span class="tag">25yr context</span>
    </div>
    <canvas id="predHistChart" height="80"></canvas>
  </div>

  <div class="kalshi-link-card">
    <div class="klc-left">
      <h3>View live Chicago rain market on Kalshi</h3>
      <p>kxrainchim-26mar · March 2026 · Above 1–7 inches</p>
    </div>
    <a href="https://kalshi.com/markets/kxrainchim/rain-chicago/kxrainchim-26mar" target="_blank" class="klc-btn">Open Kalshi →</a>
  </div>
</div>

<!-- ══ TAB 3: EDGE ════════════════════════════════════════ -->
<div id="tab-edge" class="tab-content">
  <p class="page-title">Kalshi Edge</p>
  <p class="page-sub">Model vs live Kalshi prices · March 2026 · find mispriced markets</p>

  <div class="info-note">
    Kalshi prices shown are for the active <strong>March 2026</strong> market. Model probabilities use the full 25-year blended prediction.
    Run <strong>kalshi.py</strong> to refresh prices. Edge &gt; 5% = tradeable signal.
  </div>

  <div class="edge-card">
    <div class="edge-card-header">
      <h2>March 2026 — Chicago rain</h2>
      <div class="edge-badges-legend">
        <span class="tag" style="background:var(--green-bg);color:var(--green);border-color:var(--green-bdr)">+ edge → BUY YES</span>
        <span class="tag" style="background:var(--red-bg);color:var(--red);border-color:var(--red-bdr)">− edge → BUY NO</span>
      </div>
    </div>
    <div class="edge-col-headers">
      <span>Threshold</span><span>Model</span><span>Kalshi</span><span>Signal</span>
    </div>
    <div id="edgeRows"></div>
  </div>

  <div class="card">
    <div class="card-header">
      <h2>Edge size by threshold</h2>
      <span class="tag">model % minus kalshi % · positive = BUY YES</span>
    </div>
    <canvas id="edgeChart" height="80"></canvas>
  </div>
</div>

<!-- ══ TAB 4: CLIMATE SIGNALS ════════════════════════════ -->
<div id="tab-signals" class="tab-content">
  <p class="page-title">Climate Signals</p>
  <p class="page-sub">Live atmospheric indices that drive Chicago rainfall · run fetch_indices.py to refresh</p>

  <div class="signal-summary" id="signalSummary"></div>
  <div class="signals-grid" id="signalsGrid"></div>

  <div class="card">
    <div class="card-header">
      <h2>Index reference guide</h2>
      <span class="tag">what each signal means for Chicago</span>
    </div>
    <div style="display:grid;grid-template-columns:1fr 1fr;gap:1.2rem 2rem;font-size:0.72rem;line-height:1.65;color:var(--navy2)">
      <p><strong>AO</strong> — Negative polar vortex = cold air masses push south, collide with Gulf moisture over the Midwest.</p>
      <p><strong>NAO</strong> — Negative NAO steers Atlantic storm systems southward toward the central US.</p>
      <p><strong>MJO</strong> — A 30–60 day tropical wave. Phases 4–6 with amplitude above 1 boost Midwest rain 2–3 weeks out.</p>
      <p><strong>PDO</strong> — Positive PDO amplifies El Niño, strengthening the subtropical jet and Midwest moisture transport.</p>
      <p><strong>AMO</strong> — Warm Atlantic increases evaporation and moisture feeding into continental storm systems.</p>
      <p><strong>Gulf SST</strong> — Primary Midwest moisture source. Warmer Gulf = more water vapor on the low-level jet.</p>
      <p><strong>Humidity</strong> — Above 75% RH means near-saturation. Small triggers can set off rain events.</p>
      <p><strong>500mb Height</strong> — Low heights = upper trough = storms. High heights = ridge = dry and sunny.</p>
    </div>
  </div>
</div>

</div><!-- /container -->

<script>
const MONTHLY  = __MONTHLY__;
const DAILY    = __DAILY__;
const PREDS    = __PREDS__;
const KALSHI   = __KALSHI__;

const INDICES  = __INDICES__;

const MONTHS      = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"];
const MONTHS_FULL = ["January","February","March","April","May","June","July","August","September","October","November","December"];
const YEARS       = Array.from({length:25},(_,i)=>2000+i);
const THRESHOLDS  = [
  {label:"Above 1 inch", mm:25.4},
  {label:"Above 2 inches",mm:50.8},
  {label:"Above 3 inches",mm:76.2},
  {label:"Above 4 inches",mm:101.6},
  {label:"Above 5 inches",mm:127.0},
  {label:"Above 6 inches",mm:152.4},
  {label:"Above 7 inches",mm:177.8},
];

const PALETTE = [
  "#ef4444","#f97316","#eab308","#22c55e","#06b6d4",
  "#3b82f6","#8b5cf6","#ec4899","#14b8a6","#f59e0b",
  "#6366f1","#10b981","#f87171","#60a5fa","#a78bfa",
  "#34d399","#fbbf24","#fb923c","#818cf8","#4ade80",
  "#38bdf8","#c084fc","#f472b6","#2dd4bf","#facc15"
];

const charts = {};
let selMonth = 2; // March

// ── populate year select ──
const ys = document.getElementById('yearSelect');
YEARS.slice().reverse().forEach(y => {
  const o = document.createElement('option');
  o.value = y; o.textContent = y; ys.appendChild(o);
});

function destroyChart(id){if(charts[id]){charts[id].destroy();charts[id]=null}}

function monthlyArr(year){
  return Array.from({length:12},(_,i)=>MONTHLY[`${year}-${String(i+1).padStart(2,'0')}`]||0);
}
function avgMonthlyArr(){
  return Array.from({length:12},(_,i)=>{
    const v=YEARS.map(y=>MONTHLY[`${y}-${String(i+1).padStart(2,'0')}`]||0);
    return Math.round(v.reduce((a,b)=>a+b,0)/v.length*10)/10;
  });
}
function dailyAvgArr(monthIdx){
  const ms=String(monthIdx+1).padStart(2,'0');
  const byDay={};
  YEARS.forEach(y=>{
    Object.keys(DAILY).filter(k=>k.startsWith(`${y}-${ms}-`)).forEach(k=>{
      const d=parseInt(k.slice(-2));
      if(!byDay[d])byDay[d]=[];
      byDay[d].push(DAILY[k]);
    });
  });
  const maxD=Math.max(...Object.keys(byDay).map(Number));
  return Array.from({length:maxD},(_,i)=>{
    const d=i+1;
    return byDay[d]?Math.round(byDay[d].reduce((a,b)=>a+b,0)/byDay[d].length*10)/10:0;
  });
}
function annualTotals(){
  return YEARS.map(y=>{
    const v=Array.from({length:12},(_,i)=>MONTHLY[`${y}-${String(i+1).padStart(2,'0')}`]||0);
    return Math.round(v.reduce((a,b)=>a+b,0));
  });
}

function renderHistorical(){
  const yv = document.getElementById('yearSelect').value;
  const isAll = yv==='all';
  const data = isAll ? avgMonthlyArr() : monthlyArr(parseInt(yv));
  const label = isAll ? '25-Year Avg' : yv;

  const nonZero=data.filter(v=>v>0);
  const max=Math.max(...data); const min=nonZero.length?Math.min(...nonZero):0;
  const total=Math.round(data.reduce((a,b)=>a+b,0));
  const allVals=Object.values(MONTHLY);
  const avg=(allVals.reduce((a,b)=>a+b,0)/allVals.length).toFixed(1);

  document.getElementById('wettestMonth').textContent=MONTHS[data.indexOf(max)];
  document.getElementById('wettestVal').textContent=max.toFixed(1)+'mm';
  document.getElementById('driestMonth').textContent=MONTHS[data.indexOf(min)];
  document.getElementById('driestVal').textContent=min.toFixed(1)+'mm';
  document.getElementById('annualTotal').textContent=total+'mm';
  document.getElementById('annualSub').textContent=label;
  document.getElementById('globalAvg').textContent=avg+'mm';

  // Month strip
  const strip=document.getElementById('monthStrip');
  strip.innerHTML='';
  MONTHS.forEach((m,i)=>{
    const div=document.createElement('div');
    div.className='month-cell'+(selMonth===i?' active':'');
    div.innerHTML=`<div class="mn">${m}</div><div class="mv">${data[i].toFixed(0)}</div>`;
    div.onclick=()=>{selMonth=i;renderHistorical()};
    strip.appendChild(div);
  });

  // Bar chart
  destroyChart('bar');
  charts.bar=new Chart(document.getElementById('barChart').getContext('2d'),{
    type:'bar',
    data:{
      labels:MONTHS,
      datasets:[{
        data,
        backgroundColor:data.map((_,i)=>selMonth===i?'#0284c7':'#bae6fd'),
        borderRadius:5,borderSkipped:false
      }]
    },
    options:{
      plugins:{legend:{display:false},tooltip:{callbacks:{label:ctx=>` ${ctx.raw.toFixed(1)}mm`}}},
      scales:{
        y:{beginAtZero:true,grid:{color:'rgba(0,0,0,0.05)'},ticks:{color:'#9ca3af',font:{family:'DM Mono',size:11}},title:{display:true,text:'mm',color:'#9ca3af'}},
        x:{grid:{display:false},ticks:{color:'#6b7280',font:{size:11}}}
      },
      onClick:(_,els)=>{if(els.length){selMonth=els[0].index;renderHistorical()}}
    }
  });
  document.getElementById('barChartTitle').textContent=`Monthly Rainfall — ${label}`;

  // Daily breakdown
  const dailySec=document.getElementById('dailySection');
  dailySec.style.display='block';
  document.getElementById('dailyTitle').textContent=`Daily rainfall — ${MONTHS[selMonth]} (25yr avg)`;
  const ddata=dailyAvgArr(selMonth);
  destroyChart('daily');
  charts.daily=new Chart(document.getElementById('dailyChart').getContext('2d'),{
    type:'bar',
    data:{
      labels:Array.from({length:ddata.length},(_,i)=>i+1),
      datasets:[{
        data:ddata,
        backgroundColor:'#bae6fd',
        hoverBackgroundColor:'#bae6fd',
        borderRadius:3,borderSkipped:false
      }]
    },
    options:{
      plugins:{legend:{display:false},tooltip:{callbacks:{label:ctx=>` ${ctx.raw.toFixed(1)}mm avg`}}},
      hover:{mode:null},
      scales:{
        y:{beginAtZero:true,grid:{color:'rgba(0,0,0,0.05)'},ticks:{color:'#9ca3af',font:{family:'DM Mono',size:10}}},
        x:{grid:{display:false},ticks:{color:'#6b7280',font:{size:10}},title:{display:true,text:'Day of month',color:'#9ca3af'}}
      }
    }
  });

  // Line chart - show last 10 years for readability
  const recentYears=YEARS.slice(-10);
  destroyChart('line');
  charts.line=new Chart(document.getElementById('lineChart').getContext('2d'),{
    type:'line',
    data:{
      labels:MONTHS,
      datasets:recentYears.map((y,i)=>({
        label:String(y),data:monthlyArr(y),
        borderColor:PALETTE[i],backgroundColor:'transparent',
        tension:0.35,pointRadius:2,pointHoverRadius:4,borderWidth:1.5
      }))
    },
    options:{
      plugins:{legend:{position:'bottom',labels:{color:'#6b7280',font:{family:'DM Mono',size:9},boxWidth:8,padding:8}}},
      scales:{
        y:{beginAtZero:true,grid:{color:'rgba(0,0,0,0.05)'},ticks:{color:'#9ca3af',font:{family:'DM Mono',size:10}}},
        x:{grid:{display:false},ticks:{color:'#6b7280',font:{size:10}}}
      }
    }
  });

  // Annual totals
  const at=annualTotals();
  destroyChart('annual');
  charts.annual=new Chart(document.getElementById('annualChart').getContext('2d'),{
    type:'bar',
    data:{
      labels:YEARS.map(String),
      datasets:[{data:at,backgroundColor:PALETTE,borderRadius:4,borderSkipped:false}]
    },
    options:{
      plugins:{legend:{display:false},tooltip:{callbacks:{label:ctx=>` ${ctx.raw}mm`}}},
      scales:{
        y:{beginAtZero:false,grid:{color:'rgba(0,0,0,0.05)'},ticks:{color:'#9ca3af',font:{family:'DM Mono',size:10}}},
        x:{grid:{display:false},ticks:{color:'#6b7280',font:{size:9},maxRotation:45}}
      }
    }
  });
}

function renderPredictions(){
  const ym=document.getElementById('predMonthSelect').value;
  const p=PREDS[ym];
  if(!p) return;

  document.getElementById('predHeroTitle').textContent=`${MONTHS_FULL[p.month_num-1]} 2026 Forecast — Chicago`;
  document.getElementById('predHeroMM').textContent=p.blended_mm.toFixed(1);

  // Source cards
  document.getElementById('predSources').innerHTML=`
    <div class="psc">
      <div class="psc-label">Weighted Average</div>
      <div class="psc-val">${p.weighted_avg_mm.toFixed(1)}mm</div>
      <div class="psc-note">Recent years weighted higher</div>
      <div class="psc-weight">40% weight</div>
    </div>
    <div class="psc">
      <div class="psc-label">Ridge Regression</div>
      <div class="psc-val">${p.linear_mm.toFixed(1)}mm</div>
      <div class="psc-note">Trend + ENSO index features</div>
      <div class="psc-weight">30% weight</div>
    </div>
    <div class="psc">
      <div class="psc-label">XGBoost</div>
      <div class="psc-val">${p.xgboost_mm!==null?p.xgboost_mm.toFixed(1)+'mm':'n/a'}</div>
      <div class="psc-note">20 weather features · daily model</div>
      <div class="psc-weight">30% weight</div>
    </div>
  `;

  // Probability rows
  const onlyMarch = ym==='2026-03';
  const container=document.getElementById('probRows');
  container.innerHTML='';
  THRESHOLDS.forEach(t=>{
    const mp=p.thresholds[t.label]??0;
    const kp=onlyMarch?(KALSHI[t.label]??null):null;
    container.innerHTML+=`
      <div class="prob-row">
        <div class="prob-row-header">
          <span class="prob-row-label">${t.label}</span>
          <span class="prob-row-mm">${t.mm.toFixed(1)}mm</span>
        </div>
        <div class="prob-bars">
          <div class="prob-bar-row">
            <span class="prob-bar-src">model</span>
            <div class="prob-bar-track"><div class="prob-bar-fill" style="width:${mp}%;background:#0284c7"></div></div>
            <span class="prob-bar-pct" style="color:#0284c7">${mp}%</span>
          </div>
          ${kp!==null?`
          <div class="prob-bar-row">
            <span class="prob-bar-src">kalshi</span>
            <div class="prob-bar-track"><div class="prob-bar-fill" style="width:${kp}%;background:#b45309"></div></div>
            <span class="prob-bar-pct" style="color:#b45309">${kp}%</span>
          </div>`:''}
        </div>
      </div>
    `;
  });

  // Historical context chart
  const monthNum=p.month_num;
  const histYears=YEARS;
  const histVals=histYears.map(y=>MONTHLY[`${y}-${String(monthNum).padStart(2,'0')}`]||0);
  destroyChart('predHist');
  charts.predHist=new Chart(document.getElementById('predHistChart').getContext('2d'),{
    type:'bar',
    data:{
      labels:[...histYears.map(String),'2026↗'],
      datasets:[{
        data:[...histVals, p.blended_mm],
        backgroundColor:[...histVals.map(_=>'#bae6fd'),'#0284c7'],
        borderRadius:4,borderSkipped:false
      },{
        type:'line',
        data:[...histVals.map(_=>p.hist_mean_mm), p.hist_mean_mm],
        borderColor:'#f59e0b',borderDash:[4,3],borderWidth:1.5,
        pointRadius:0,label:'25yr avg',tension:0
      }]
    },
    options:{
      plugins:{
        legend:{position:'bottom',labels:{color:'#6b7280',font:{family:'DM Mono',size:9},boxWidth:8,padding:8}},
        tooltip:{callbacks:{label:ctx=>` ${ctx.raw.toFixed?ctx.raw.toFixed(1):ctx.raw}mm`}}
      },
      scales:{
        y:{beginAtZero:true,grid:{color:'rgba(0,0,0,0.05)'},ticks:{color:'#9ca3af',font:{family:'DM Mono',size:10}},title:{display:true,text:'mm',color:'#9ca3af'}},
        x:{grid:{display:false},ticks:{color:'#6b7280',font:{size:9},maxRotation:45}}
      }
    }
  });
  document.getElementById('predChartTitle').textContent=`Historical ${MONTHS_FULL[monthNum-1]} totals + 2026 prediction`;
}

function renderEdge(){
  const p=PREDS['2026-03'];
  if(!p) return;

  const container=document.getElementById('edgeRows');
  container.innerHTML='';
  const edgeVals=[], edgeLabels=[];

  THRESHOLDS.forEach(t=>{
    const mp=p.thresholds[t.label]??0;
    const kp=KALSHI[t.label]??null;
    const edge=kp!==null?Math.round((mp-kp)*10)/10:null;

    let bHtml,bClass;
    if(kp===null){bHtml='no market';bClass='badge-neu'}
    else if(edge>5){bHtml=`+${edge}%<br>BUY YES`;bClass='badge-yes'}
    else if(edge<-5){bHtml=`${edge}%<br>BUY NO`;bClass='badge-no'}
    else{bHtml=`${edge>=0?'+':''}${edge}%<br>no edge`;bClass='badge-neu'}

    container.innerHTML+=`
      <div class="edge-row">
        <div class="edge-thresh">${t.label}<small>${t.mm.toFixed(1)}mm · ${(t.mm/25.4).toFixed(0)} in</small></div>
        <div class="edge-prob" style="color:#0284c7">${mp}%</div>
        <div class="edge-prob" style="color:#b45309">${kp!==null?kp+'%':'—'}</div>
        <div class="edge-badge ${bClass}">${bHtml}</div>
      </div>
    `;
    edgeLabels.push(t.label.replace('Above ',''));
    edgeVals.push(edge!==null?edge:0);
  });

  // Edge bar chart
  destroyChart('edge');
  charts.edge=new Chart(document.getElementById('edgeChart').getContext('2d'),{
    type:'bar',
    data:{
      labels:edgeLabels,
      datasets:[{
        data:edgeVals,
        backgroundColor:edgeVals.map(v=>v>5?'#047857':v<-5?'#b91c1c':'#9ca3af'),
        borderRadius:5,borderSkipped:false
      }]
    },
    options:{
      plugins:{legend:{display:false},tooltip:{callbacks:{label:ctx=>` ${ctx.raw>0?'+':''}${ctx.raw}%`}}},
      scales:{
        y:{grid:{color:'rgba(0,0,0,0.05)'},ticks:{color:'#9ca3af',font:{family:'DM Mono',size:11}},title:{display:true,text:'edge %',color:'#9ca3af'}},
        x:{grid:{display:false},ticks:{color:'#6b7280',font:{size:11}}}
      }
    }
  });
}

function renderSignals(){
  const grid    = document.getElementById('signalsGrid');
  const summary = document.getElementById('signalSummary');
  grid.innerHTML = '';

  const sigEmoji = {wet:'🌧', dry:'☀️', neutral:'🌤', unknown:'❓'};
  const sigLabel = {wet:'FAVORS RAIN', dry:'FAVORS DRY', neutral:'NEUTRAL', unknown:'NO DATA'};
  const gaugeColor = {wet:'#0284c7', dry:'#b45309', neutral:'#9ca3af', unknown:'#d1d5db'};

  // Ranges for gauge fill (normalized 0–100%)
  const ranges = {
    ao:        {min:-3,   max:3,    wet_dir:'negative'},
    nao:       {min:-3,   max:3,    wet_dir:'negative'},
    pdo:       {min:-3,   max:3,    wet_dir:'positive'},
    amo:       {min:-0.4, max:0.4,  wet_dir:'positive'},
    gulf_sst:  {min:22,   max:32,   wet_dir:'positive'},
    tpw:       {min:20,   max:100,  wet_dir:'positive'},
    z500:      {min:5300, max:5700, wet_dir:'negative'},
    mjo:       {min:0,    max:3,    wet_dir:'positive'},
  };

  let wetCount=0, dryCount=0, neutralCount=0;

  Object.entries(INDICES).forEach(([key, info]) => {
    const sig = info.signal || 'unknown';
    if(sig==='wet') wetCount++;
    else if(sig==='dry') dryCount++;
    else neutralCount++;

    const v = info.value;
    let valStr, gaugeW;
    const r = ranges[key];

    if(v===null||v===undefined){
      valStr='no data'; gaugeW=0;
    } else if(typeof v==='object'){
      // MJO
      valStr=`phase ${v.phase}`;
      gaugeW = r ? Math.min(100, Math.max(0, ((v.amplitude - r.min)/(r.max - r.min))*100)) : 50;
    } else if(typeof v==='number'){
      const abs = Math.abs(v);
      const decimals = abs > 100 ? 0 : abs > 10 ? 1 : 2;
      const prefix = (key==='ao'||key==='nao'||key==='pdo'||key==='amo') && v>0 ? '+' : '';
      valStr = `${prefix}${v.toFixed(decimals)}`;
      gaugeW = r ? Math.min(100, Math.max(0, ((v - r.min)/(r.max - r.min))*100)) : 50;
    } else {
      valStr = String(v); gaugeW = 50;
    }

    grid.innerHTML += `
      <div class="signal-card sig-${sig}">
        <div class="sc-top">
          <div class="sc-left">
            <div class="sc-label">${key.toUpperCase().replace('_',' ')}</div>
            <div class="sc-name">${info.label||key}</div>
          </div>
          <div class="sc-emoji">${sigEmoji[sig]||'❓'}</div>
        </div>
        <div class="sc-mid">
          <span class="sc-value">${valStr}</span>
          <span class="sc-unit">${typeof v==='object'?`· amp ${v.amplitude.toFixed(2)}`:(info.unit||'')}</span>
        </div>
        <div class="sc-date">as of ${info.date||'—'}</div>
        <div class="sc-gauge">
          <div class="sc-gauge-fill" style="width:${gaugeW}%;background:${gaugeColor[sig]||'#9ca3af'}"></div>
        </div>
        <div class="sc-bottom">
          <span class="sc-badge sig-${sig}">${sigLabel[sig]||sig}</span>
          <span class="sc-desc">${info.description||''}</span>
        </div>
      </div>
    `;
  });

  // Summary bar
  const total = wetCount + dryCount + neutralCount || 1;
  const wetPct  = Math.round(wetCount/total*100);
  const dryPct  = Math.round(dryCount/total*100);
  let overall, ovClass, ovColor;
  if(wetCount > dryCount+1){overall='Atmospheric pattern favors rain';ovClass='ov-wet';ovColor='var(--sky)'}
  else if(dryCount > wetCount+1){overall='Atmospheric pattern favors dry';ovClass='ov-dry';ovColor='var(--amber)'}
  else{overall='Mixed signals — no strong bias';ovClass='ov-neutral';ovColor='var(--muted)'}

  summary.innerHTML = `
    <div class="ss-top">
      <span class="ss-title">Current atmospheric state — Chicago</span>
      <span class="ss-date">updated ${new Date().toLocaleDateString('en-US',{month:'short',day:'numeric',year:'numeric'})}</span>
    </div>
    <div class="ss-counts">
      <div class="ss-item">
        <div class="ss-dot" style="background:#0284c7"></div>
        <div>
          <div class="ss-count" style="color:#0284c7">${wetCount}</div>
          <div class="ss-label">wet signals</div>
        </div>
      </div>
      <div class="ss-item">
        <div class="ss-dot" style="background:#9ca3af"></div>
        <div>
          <div class="ss-count" style="color:#9ca3af">${neutralCount}</div>
          <div class="ss-label">neutral</div>
        </div>
      </div>
      <div class="ss-item">
        <div class="ss-dot" style="background:#b45309"></div>
        <div>
          <div class="ss-count" style="color:#b45309">${dryCount}</div>
          <div class="ss-label">dry signals</div>
        </div>
      </div>
    </div>
    <div class="ss-bar-wrap">
      <div class="ss-bar-track">
        <div class="ss-bar-wet" style="width:${wetPct}%"></div>
        <div class="ss-bar-dry" style="width:${dryPct}%"></div>
      </div>
      <div class="ss-bar-labels">
        <span class="ss-bar-label" style="color:#0284c7">🌧 ${wetPct}% wet</span>
        <span class="ss-bar-label" style="color:#b45309">${dryPct}% dry ☀️</span>
      </div>
    </div>
    <div class="overall-verdict ${ovClass}">
      <span class="ov-label">verdict</span>
      <span class="ov-value" style="color:${ovColor}">${overall}</span>
    </div>
  `;
}

function showTab(name){
  document.querySelectorAll('.tab-content').forEach(el=>el.classList.remove('active'));
  document.querySelectorAll('.tab-btn').forEach(el=>el.classList.remove('active'));
  document.getElementById('tab-'+name).classList.add('active');
  document.querySelector('[data-tab="'+name+'"]').classList.add('active');
  if(name==='historical') renderHistorical();
  if(name==='predictions') renderPredictions();
  if(name==='edge') renderEdge();
  if(name==='signals') renderSignals();
}

showTab('historical');
</script>
</body>
</html>"""

result = (HTML
    .replace('__MONTHLY__', monthly_js)
    .replace('__DAILY__',   daily_js)
    .replace('__PREDS__',   pred_js)
    .replace('__KALSHI__',  kalshi_js)
    .replace('__INDICES__', indices_js))

for fname in ['index.html', 'dashboard.html']:
    with open(fname, 'w') as fh:
        fh.write(result)
    print(f"  ✓ {fname} written ({len(result):,} bytes)")

print("\nDone! Now run:")
print("  open index.html")
print("  git add -A && git commit -m 'v2 full redesign' && git push")
