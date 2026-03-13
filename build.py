import json

with open("data_daily.json") as f:
    daily_data = json.load(f)

with open("data.json") as f:
    monthly_data = json.load(f)

daily_js = json.dumps(daily_data, separators=(',',':'))
monthly_js = json.dumps(monthly_data, separators=(',',':'))

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
  --bg: #f7f4ef;
  --surface: #ffffff;
  --surface2: #f0ece4;
  --border: #e2ddd4;
  --border2: #cfc9be;
  --navy: #1a1f2e;
  --navy2: #374151;
  --sky: #0ea5e9;
  --sky-light: #e0f2fe;
  --sky-mid: #7dd3fc;
  --amber: #d97706;
  --amber-light: #fef3c7;
  --green: #059669;
  --green-light: #d1fae5;
  --red: #dc2626;
  --red-light: #fee2e2;
  --muted: #6b7280;
  --muted2: #9ca3af;
}
* { box-sizing: border-box; margin: 0; padding: 0; }
body { font-family: 'Inter', sans-serif; background: var(--bg); color: var(--navy); min-height: 100vh; }

header {
  background: var(--surface);
  border-bottom: 1px solid var(--border);
  padding: 0 2rem;
  display: flex;
  align-items: stretch;
  position: sticky;
  top: 0;
  z-index: 100;
  box-shadow: 0 1px 3px rgba(0,0,0,0.06);
}
.logo-area {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 0.9rem 1.5rem 0.9rem 0;
  border-right: 1px solid var(--border);
  margin-right: 0.5rem;
}
.logo-icon {
  width: 30px; height: 30px;
  background: linear-gradient(135deg, #0ea5e9, #38bdf8);
  border-radius: 7px;
  display: flex; align-items: center; justify-content: center;
  font-size: 15px;
}
.logo-text h1 { font-size: 0.9rem; font-weight: 700; color: var(--navy); }
.logo-text p { font-size: 0.62rem; color: var(--muted); font-family: 'DM Mono', monospace; margin-top: 1px; }

nav { display: flex; align-items: stretch; flex: 1; }
.tab-btn {
  display: flex; align-items: center; gap: 7px;
  padding: 0 1.1rem;
  font-size: 0.8rem; font-weight: 500;
  color: var(--muted);
  background: none; border: none;
  border-bottom: 2px solid transparent;
  cursor: pointer;
  transition: color 0.15s, border-color 0.15s;
  white-space: nowrap;
}
.tab-btn:hover { color: var(--navy); }
.tab-btn.active { color: var(--navy); border-bottom-color: var(--sky); font-weight: 600; }

.live-badge {
  display: flex; align-items: center; gap: 5px;
  margin-left: auto;
  font-family: 'DM Mono', monospace;
  font-size: 0.62rem; color: var(--green);
  padding: 0 0.5rem;
}
.live-dot { width: 5px; height: 5px; border-radius: 50%; background: var(--green); animation: blink 2s infinite; }
@keyframes blink { 0%,100%{opacity:1} 50%{opacity:0.3} }

.container { max-width: 1140px; margin: 0 auto; padding: 1.5rem; }
.tab-content { display: none; }
.tab-content.active { display: block; }

.page-title { font-size: 1.1rem; font-weight: 700; color: var(--navy); margin-bottom: 0.3rem; }
.page-sub { font-size: 0.72rem; color: var(--muted); font-family: 'DM Mono', monospace; margin-bottom: 1.5rem; }

.controls { display: flex; gap: 10px; align-items: center; margin-bottom: 1.3rem; }
.control-label { font-size: 0.68rem; font-weight: 600; color: var(--muted); text-transform: uppercase; letter-spacing: 0.08em; }
select {
  background: var(--surface); border: 1px solid var(--border);
  color: var(--navy); font-family: 'Inter', sans-serif;
  font-size: 0.8rem; font-weight: 500;
  padding: 7px 12px; border-radius: 8px;
  cursor: pointer; outline: none;
  box-shadow: 0 1px 2px rgba(0,0,0,0.04);
}
select:hover { border-color: var(--sky); }
select:focus { border-color: var(--sky); box-shadow: 0 0 0 3px rgba(14,165,233,0.12); }

.stats-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 10px; margin-bottom: 1.3rem; }
.stat-card {
  background: var(--surface); border: 1px solid var(--border);
  border-radius: 12px; padding: 1rem 1.15rem;
  box-shadow: 0 1px 3px rgba(0,0,0,0.05);
}
.stat-label { font-size: 0.58rem; font-weight: 600; color: var(--muted); text-transform: uppercase; letter-spacing: 0.1em; margin-bottom: 8px; }
.stat-value { font-size: 1.7rem; font-weight: 800; letter-spacing: -0.04em; line-height: 1; }
.stat-sub { font-family: 'DM Mono', monospace; font-size: 0.62rem; color: var(--muted); margin-top: 5px; }
.c-sky .stat-value { color: var(--sky); }
.c-green .stat-value { color: var(--green); }
.c-amber .stat-value { color: var(--amber); }
.c-purple .stat-value { color: #7c3aed; }

.month-strip { display: grid; grid-template-columns: repeat(12, 1fr); gap: 5px; margin-bottom: 1.3rem; }
.month-cell {
  background: var(--surface); border: 1px solid var(--border);
  border-radius: 8px; padding: 7px 3px;
  text-align: center; cursor: pointer;
  transition: all 0.12s;
  box-shadow: 0 1px 2px rgba(0,0,0,0.03);
}
.month-cell:hover { border-color: var(--sky); background: var(--sky-light); }
.month-cell.active { border-color: var(--sky); background: var(--sky-light); }
.month-cell .mn { font-size: 0.58rem; font-weight: 600; color: var(--muted); text-transform: uppercase; letter-spacing: 0.05em; }
.month-cell .mv { font-family: 'DM Mono', monospace; font-size: 0.78rem; font-weight: 700; margin-top: 3px; color: var(--navy); }
.month-cell.active .mv { color: var(--sky); }

.card {
  background: var(--surface); border: 1px solid var(--border);
  border-radius: 14px; padding: 1.3rem; margin-bottom: 1.2rem;
  box-shadow: 0 1px 3px rgba(0,0,0,0.06);
}
.card-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 1rem; }
.card-header h2 { font-size: 0.85rem; font-weight: 600; color: var(--navy); }
.tag {
  font-family: 'DM Mono', monospace; font-size: 0.58rem;
  padding: 3px 8px; border-radius: 5px;
  background: var(--surface2); color: var(--muted); border: 1px solid var(--border);
}

.two-col { display: grid; grid-template-columns: 1fr 1fr; gap: 1.2rem; margin-bottom: 1.2rem; }

.daily-section { margin-bottom: 1.2rem; animation: fadeIn 0.2s ease; }
@keyframes fadeIn { from{opacity:0;transform:translateY(4px)} to{opacity:1;transform:translateY(0)} }

.pred-hero {
  background: linear-gradient(135deg, #f0f9ff 0%, #fefce8 100%);
  border: 1px solid var(--border); border-radius: 16px;
  padding: 1.8rem; margin-bottom: 1.2rem;
  display: flex; justify-content: space-between; align-items: flex-start;
}
.pred-hero-left h2 { font-size: 1.05rem; font-weight: 700; color: var(--navy); margin-bottom: 4px; }
.pred-hero-left p { font-size: 0.7rem; color: var(--muted); font-family: 'DM Mono', monospace; }
.pred-mm { font-size: 3rem; font-weight: 800; letter-spacing: -0.06em; color: var(--sky); line-height: 1; }
.pred-mm-sub { font-family: 'DM Mono', monospace; font-size: 0.65rem; color: var(--muted); margin-top: 5px; text-align: right; }

.pred-sources { display: grid; grid-template-columns: repeat(3, 1fr); gap: 10px; margin-bottom: 1.2rem; }
.pred-source-card {
  background: var(--surface); border: 1px solid var(--border);
  border-radius: 12px; padding: 1rem 1.1rem;
  box-shadow: 0 1px 3px rgba(0,0,0,0.05);
}
.psc-label { font-size: 0.58rem; font-weight: 600; color: var(--muted); text-transform: uppercase; letter-spacing: 0.1em; margin-bottom: 6px; }
.psc-val { font-family: 'DM Mono', monospace; font-size: 1.35rem; font-weight: 700; color: var(--navy); }
.psc-note { font-size: 0.62rem; color: var(--muted); margin-top: 3px; }
.psc-weight {
  display: inline-block; margin-top: 4px;
  background: var(--sky-light); color: var(--sky);
  border-radius: 4px; padding: 2px 6px;
  font-family: 'DM Mono', monospace; font-size: 0.58rem; font-weight: 600;
}

.prob-card {
  background: var(--surface); border: 1px solid var(--border);
  border-radius: 14px; padding: 1.3rem; margin-bottom: 1.2rem;
  box-shadow: 0 1px 3px rgba(0,0,0,0.06);
}
.prob-card-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 1.2rem; }
.prob-card-header h2 { font-size: 0.85rem; font-weight: 600; color: var(--navy); }
.prob-legend { display: flex; gap: 14px; }
.prob-legend-item { display: flex; align-items: center; gap: 5px; font-size: 0.62rem; color: var(--muted); font-family: 'DM Mono', monospace; }
.prob-legend-dot { width: 8px; height: 8px; border-radius: 2px; }

.prob-row { margin-bottom: 1.1rem; }
.prob-row:last-child { margin-bottom: 0; }
.prob-row-header { display: flex; justify-content: space-between; align-items: baseline; margin-bottom: 7px; }
.prob-row-label { font-size: 0.82rem; font-weight: 600; color: var(--navy); }
.prob-row-mm { font-family: 'DM Mono', monospace; font-size: 0.62rem; color: var(--muted2); }
.prob-bars { display: flex; flex-direction: column; gap: 5px; }
.prob-bar-row { display: flex; align-items: center; gap: 10px; }
.prob-bar-src { font-family: 'DM Mono', monospace; font-size: 0.58rem; color: var(--muted); width: 36px; text-align: right; }
.prob-bar-track { flex: 1; height: 9px; background: var(--surface2); border-radius: 5px; overflow: hidden; border: 1px solid var(--border); }
.prob-bar-fill { height: 100%; border-radius: 4px; transition: width 0.6s cubic-bezier(0.4,0,0.2,1); }
.prob-bar-pct { font-family: 'DM Mono', monospace; font-size: 0.65rem; font-weight: 700; width: 34px; }

.kalshi-link-card {
  background: linear-gradient(135deg, #fffbeb, #fef3c7);
  border: 1px solid #fde68a; border-radius: 14px;
  padding: 1.2rem 1.5rem; margin-bottom: 1.2rem;
  display: flex; justify-content: space-between; align-items: center;
}
.klc-left h3 { font-size: 0.88rem; font-weight: 600; color: var(--navy); margin-bottom: 3px; }
.klc-left p { font-size: 0.68rem; color: var(--muted); font-family: 'DM Mono', monospace; }
.klc-btn {
  background: var(--amber); color: white;
  border: none; border-radius: 8px;
  padding: 9px 18px; font-size: 0.8rem; font-weight: 600;
  cursor: pointer; text-decoration: none; display: inline-block;
  transition: background 0.15s; white-space: nowrap;
}
.klc-btn:hover { background: #b45309; }

.edge-card {
  background: var(--surface); border: 1px solid var(--border);
  border-radius: 14px; overflow: hidden; margin-bottom: 1.2rem;
  box-shadow: 0 1px 3px rgba(0,0,0,0.06);
}
.edge-card-header { padding: 1.1rem 1.3rem; border-bottom: 1px solid var(--border); display: flex; justify-content: space-between; align-items: center; }
.edge-card-header h2 { font-size: 0.85rem; font-weight: 600; }
.edge-col-headers {
  display: grid; grid-template-columns: 1fr 80px 80px 130px;
  gap: 10px; padding: 9px 1.3rem;
  background: var(--surface2); border-bottom: 1px solid var(--border);
}
.edge-col-headers span { font-size: 0.58rem; font-weight: 600; color: var(--muted); text-transform: uppercase; letter-spacing: 0.1em; text-align: center; }
.edge-col-headers span:first-child { text-align: left; }

.edge-row {
  display: grid; grid-template-columns: 1fr 80px 80px 130px;
  gap: 10px; align-items: center;
  padding: 12px 1.3rem; border-bottom: 1px solid var(--border);
  transition: background 0.1s;
}
.edge-row:last-child { border-bottom: none; }
.edge-row:hover { background: var(--surface2); }
.edge-thresh { font-size: 0.82rem; font-weight: 600; color: var(--navy); }
.edge-thresh small { display: block; font-family: 'DM Mono', monospace; font-size: 0.58rem; color: var(--muted); margin-top: 2px; font-weight: 400; }
.edge-prob { font-family: 'DM Mono', monospace; font-size: 0.95rem; font-weight: 700; text-align: center; }
.edge-badge {
  font-family: 'DM Mono', monospace; font-size: 0.68rem; font-weight: 700;
  padding: 7px 10px; border-radius: 8px; text-align: center; line-height: 1.4;
}
.badge-yes { background: var(--green-light); color: var(--green); border: 1px solid #6ee7b7; }
.badge-no { background: var(--red-light); color: var(--red); border: 1px solid #fca5a5; }
.badge-neu { background: var(--surface2); color: var(--muted); border: 1px solid var(--border); }

.empty-state { text-align: center; padding: 2.5rem; color: var(--muted2); font-size: 0.78rem; font-family: 'DM Mono', monospace; }

.info-note {
  font-family: 'DM Mono', monospace; font-size: 0.62rem; color: var(--muted);
  background: var(--surface2); border: 1px solid var(--border);
  border-radius: 8px; padding: 8px 12px; margin-bottom: 1.2rem;
  line-height: 1.6;
}

canvas { max-width: 100%; }
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
    <button class="tab-btn active" data-tab="historical" onclick="showTab('historical')">
      Historical
    </button>
    <button class="tab-btn" data-tab="predictions" onclick="showTab('predictions')">
      Predictions
    </button>
    <button class="tab-btn" data-tab="edge" onclick="showTab('edge')">
      Kalshi Edge
    </button>
  </nav>
  <div class="live-badge"><div class="live-dot"></div>live</div>
</header>

<div class="container">

  <!-- TAB 1: HISTORICAL -->
  <div id="tab-historical" class="tab-content active">
    <p class="page-title">Historical Rainfall</p>
    <p class="page-sub">Chicago, IL · 2020–2024 · NOAA GHCND stations</p>

    <div class="controls">
      <span class="control-label">Year</span>
      <select id="yearSelect">
        <option value="2024">2024</option>
        <option value="2023">2023</option>
        <option value="2022">2022</option>
        <option value="2021">2021</option>
        <option value="2020">2020</option>
        <option value="all">5-yr average</option>
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
        <div class="stat-sub" id="annualYear">—</div>
      </div>
      <div class="stat-card c-purple">
        <div class="stat-label">5yr Monthly Avg</div>
        <div class="stat-value" id="fiveYrAvg">—</div>
        <div class="stat-sub">all months 2020–2024</div>
      </div>
    </div>

    <div class="month-strip" id="monthStrip"></div>

    <div class="card">
      <div class="card-header">
        <h2 id="barChartTitle">Monthly Rainfall</h2>
        <span class="tag">click a bar to see daily breakdown</span>
      </div>
      <canvas id="barChart" height="75"></canvas>
    </div>

    <div id="dailySection" class="daily-section" style="display:none;">
      <div class="card">
        <div class="card-header">
          <h2 id="dailyTitle">Daily Rainfall</h2>
          <span class="tag">5yr average by day</span>
        </div>
        <canvas id="dailyChart" height="75"></canvas>
      </div>
    </div>

    <div class="two-col">
      <div class="card">
        <div class="card-header">
          <h2>Year-over-year comparison</h2>
          <span class="tag">2020–2024</span>
        </div>
        <canvas id="lineChart" height="155"></canvas>
      </div>
      <div class="card">
        <div class="card-header">
          <h2>Annual totals</h2>
          <span class="tag">mm per year</span>
        </div>
        <canvas id="annualChart" height="155"></canvas>
      </div>
    </div>
  </div>

  <!-- TAB 2: PREDICTIONS -->
  <div id="tab-predictions" class="tab-content">
    <p class="page-title">Model Predictions</p>
    <p class="page-sub">Blended forecast · weighted avg + linear regression + XGBoost · March 2026</p>

    <div class="pred-hero">
      <div class="pred-hero-left">
        <h2>March 2026 Forecast — Chicago</h2>
        <p>3-model blend · trained on 2020–2024 NOAA data</p>
      </div>
      <div>
        <div class="pred-mm">87.5</div>
        <div class="pred-mm-sub">mm predicted total</div>
      </div>
    </div>

    <div class="pred-sources">
      <div class="pred-source-card">
        <div class="psc-label">Weighted Average</div>
        <div class="psc-val">91.4mm</div>
        <div class="psc-note">Recent years weighted higher</div>
        <div class="psc-weight">40% weight</div>
      </div>
      <div class="pred-source-card">
        <div class="psc-label">Linear Regression</div>
        <div class="psc-val">76.1mm</div>
        <div class="psc-note">Captures long-term trend</div>
        <div class="psc-weight">30% weight</div>
      </div>
      <div class="pred-source-card">
        <div class="psc-label">XGBoost</div>
        <div class="psc-val">93.6mm</div>
        <div class="psc-note">Non-linear seasonal patterns</div>
        <div class="psc-weight">30% weight</div>
      </div>
    </div>

    <div class="prob-card">
      <div class="prob-card-header">
        <h2>Threshold probabilities — March 2026</h2>
        <div class="prob-legend">
          <div class="prob-legend-item"><div class="prob-legend-dot" style="background:#0ea5e9;"></div>Our model</div>
          <div class="prob-legend-item"><div class="prob-legend-dot" style="background:#d97706;"></div>Kalshi market</div>
        </div>
      </div>
      <div id="probRows"></div>
    </div>

    <div class="kalshi-link-card">
      <div class="klc-left">
        <h3>View live Chicago rain market on Kalshi</h3>
        <p>kxrainchim-26mar · March 2026 · Above 1–7 inches</p>
      </div>
      <a href="https://kalshi.com/markets/kxrainchim/rain-chicago/kxrainchim-26mar" target="_blank" class="klc-btn">Open Kalshi →</a>
    </div>

    <div class="info-note">
      Model trained on 5 years of daily NOAA precipitation data for Chicago. Probabilities estimated using a normal distribution centered on the blended prediction with historical March variance. Kalshi prices fetched via API and may be up to 24h stale — run kalshi.py to refresh.
    </div>
  </div>

  <!-- TAB 3: EDGE -->
  <div id="tab-edge" class="tab-content">
    <p class="page-title">Kalshi Edge</p>
    <p class="page-sub">Our model vs live Kalshi market prices · positive edge = we think it's more likely</p>

    <div class="controls">
      <span class="control-label">Month</span>
      <select id="edgeMonthSelect" onchange="selMonth=parseInt(this.value); renderEdge();">
        <option value="-1">— select —</option>
        <option value="0">January</option>
        <option value="1">February</option>
        <option value="2" selected>March</option>
        <option value="3">April</option>
        <option value="4">May</option>
        <option value="5">June</option>
        <option value="6">July</option>
        <option value="7">August</option>
        <option value="8">September</option>
        <option value="9">October</option>
        <option value="10">November</option>
        <option value="11">December</option>
      </select>
    </div>

    <div class="info-note">
      Kalshi data shown is for <strong>March 2026</strong> only — the active market. Model probabilities for other months are based on historical data only and do not reflect a trained prediction. Run kalshi.py each month to update prices.
    </div>

    <div class="edge-card">
      <div class="edge-card-header">
        <h2>Edge calculator — <span id="edgeMonthLabel" style="color:var(--sky)">March</span></h2>
        <div style="display:flex;gap:8px;">
          <span class="tag" style="background:#d1fae5;color:#059669;border-color:#6ee7b7;">+ edge → BUY YES</span>
          <span class="tag" style="background:#fee2e2;color:#dc2626;border-color:#fca5a5;">− edge → BUY NO</span>
        </div>
      </div>
      <div class="edge-col-headers">
        <span>Threshold</span>
        <span>Model</span>
        <span>Kalshi</span>
        <span>Signal</span>
      </div>
      <div id="edgeRows"></div>
    </div>
  </div>

</div>

<script>
const DAILY_DATA = __DAILY__;
const RAIN_DATA = __MONTHLY__;
const KALSHI_DATA = {"Above 1 inch":100,"Above 2 inches":99,"Above 3 inches":90,"Above 4 inches":58,"Above 5 inches":18};
const MODEL_DATA = {"Above 1 inch":95,"Above 2 inches":84,"Above 3 inches":62,"Above 4 inches":35,"Above 5 inches":14};
const MONTHS = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"];
const MONTHS_FULL = ["January","February","March","April","May","June","July","August","September","October","November","December"];
const YEARS = [2020,2021,2022,2023,2024];
const YEAR_COLORS = ["#f87171","#fb923c","#f59e0b","#34d399","#60a5fa"];
const THRESHOLDS = [
  {label:"Above 1 inch",mm:25.4},
  {label:"Above 2 inches",mm:50.8},
  {label:"Above 3 inches",mm:76.2},
  {label:"Above 4 inches",mm:101.6},
  {label:"Above 5 inches",mm:127.0}
];

const charts = {};
let selMonth = 2;

function destroyChart(id) {
  if (charts[id]) { charts[id].destroy(); charts[id] = null; }
}

function monthlyArr(year) {
  return Array.from({length:12}, (_,i) => RAIN_DATA[`${year}-${String(i+1).padStart(2,'0')}`] ?? 0);
}

function avgMonthlyArr() {
  return Array.from({length:12}, (_,i) => {
    const v = YEARS.map(y => RAIN_DATA[`${y}-${String(i+1).padStart(2,'0')}`] ?? 0);
    return Math.round(v.reduce((a,b)=>a+b,0)/v.length*10)/10;
  });
}

function dailyAvgArr(monthIdx) {
  const ms = String(monthIdx+1).padStart(2,'0');
  const byDay = {};
  YEARS.forEach(y => {
    Object.keys(DAILY_DATA).filter(k => k.startsWith(`${y}-${ms}-`)).forEach(k => {
      const d = parseInt(k.slice(-2));
      if (!byDay[d]) byDay[d] = [];
      byDay[d].push(DAILY_DATA[k]);
    });
  });
  const maxD = Math.max(...Object.keys(byDay).map(Number));
  return Array.from({length:maxD}, (_,i) => {
    const d = i+1;
    return byDay[d] ? Math.round(byDay[d].reduce((a,b)=>a+b,0)/byDay[d].length*10)/10 : 0;
  });
}

function annualTotals() {
  return YEARS.map(y => {
    const vals = Array.from({length:12}, (_,i) => RAIN_DATA[`${y}-${String(i+1).padStart(2,'0')}`] ?? 0);
    return Math.round(vals.reduce((a,b)=>a+b,0));
  });
}

function renderHistorical() {
  const yv = document.getElementById('yearSelect').value;
  const isAll = yv === 'all';
  const data = isAll ? avgMonthlyArr() : monthlyArr(parseInt(yv));
  const label = isAll ? '5-Year Avg' : yv;

  const max = Math.max(...data);
  const nonZero = data.filter(v=>v>0);
  const min = nonZero.length ? Math.min(...nonZero) : 0;
  const total = data.reduce((a,b)=>a+b,0);
  const allVals = Object.values(RAIN_DATA);
  const avg = allVals.reduce((a,b)=>a+b,0)/allVals.length;

  document.getElementById('wettestMonth').textContent = MONTHS[data.indexOf(max)];
  document.getElementById('wettestVal').textContent = max.toFixed(1)+'mm';
  document.getElementById('driestMonth').textContent = MONTHS[data.indexOf(min)];
  document.getElementById('driestVal').textContent = min.toFixed(1)+'mm';
  document.getElementById('annualTotal').textContent = total.toFixed(0)+'mm';
  document.getElementById('annualYear').textContent = label;
  document.getElementById('fiveYrAvg').textContent = avg.toFixed(1)+'mm';

  const strip = document.getElementById('monthStrip');
  strip.innerHTML = '';
  MONTHS.forEach((m,i) => {
    const div = document.createElement('div');
    div.className = 'month-cell' + (selMonth===i?' active':'');
    div.innerHTML = `<div class="mn">${m}</div><div class="mv">${data[i].toFixed(0)}</div>`;
    div.onclick = () => { selMonth = i; renderHistorical(); };
    strip.appendChild(div);
  });

  destroyChart('bar');
  charts.bar = new Chart(document.getElementById('barChart').getContext('2d'), {
    type: 'bar',
    data: {
      labels: MONTHS,
      datasets: [{
        data,
        backgroundColor: data.map((_,i) => selMonth===i ? '#0ea5e9' : '#bfdbfe'),
        borderRadius: 5, borderSkipped: false
      }]
    },
    options: {
      plugins: {legend:{display:false}, tooltip:{callbacks:{label:ctx=>` ${ctx.raw.toFixed(1)}mm`}}},
      scales: {
        y: {beginAtZero:true, grid:{color:'rgba(0,0,0,0.05)'}, ticks:{color:'#9ca3af',font:{family:'DM Mono',size:11}}, title:{display:true,text:'mm',color:'#9ca3af'}},
        x: {grid:{display:false}, ticks:{color:'#6b7280',font:{size:11}}}
      },
      onClick: (_,els) => { if(els.length){ selMonth=els[0].index; renderHistorical(); }}
    }
  });

  document.getElementById('barChartTitle').textContent = `Monthly Rainfall — ${label}`;

  const dailySec = document.getElementById('dailySection');
  if (selMonth !== null) {
    dailySec.style.display = 'block';
    document.getElementById('dailyTitle').textContent = `Daily rainfall — ${MONTHS[selMonth]} (5yr avg)`;
    const ddata = dailyAvgArr(selMonth);
    const dlabels = Array.from({length:ddata.length}, (_,i) => i+1);
    destroyChart('daily');
    charts.daily = new Chart(document.getElementById('dailyChart').getContext('2d'), {
      type: 'bar',
      data: {
        labels: dlabels,
        datasets: [{
          data: ddata,
          backgroundColor: ddata.map(v => v>8?'#0ea5e9':v>4?'#7dd3fc':'#bfdbfe'),
          borderRadius: 3, borderSkipped: false
        }]
      },
      options: {
        plugins: {legend:{display:false}, tooltip:{callbacks:{label:ctx=>` ${ctx.raw.toFixed(1)}mm avg`}}},
        scales: {
          y: {beginAtZero:true, grid:{color:'rgba(0,0,0,0.05)'}, ticks:{color:'#9ca3af',font:{family:'DM Mono',size:10}}},
          x: {grid:{display:false}, ticks:{color:'#6b7280',font:{size:10}}, title:{display:true,text:'Day of month',color:'#9ca3af'}}
        }
      }
    });
  } else {
    dailySec.style.display = 'none';
    destroyChart('daily');
  }

  destroyChart('line');
  charts.line = new Chart(document.getElementById('lineChart').getContext('2d'), {
    type: 'line',
    data: {
      labels: MONTHS,
      datasets: YEARS.map((y,i) => ({
        label: String(y), data: monthlyArr(y),
        borderColor: YEAR_COLORS[i], backgroundColor: 'transparent',
        tension: 0.35, pointRadius: 3, pointHoverRadius: 5, borderWidth: 2
      }))
    },
    options: {
      plugins: {legend:{position:'bottom',labels:{color:'#6b7280',font:{family:'DM Mono',size:10},boxWidth:10,padding:10}}},
      scales: {
        y: {beginAtZero:true, grid:{color:'rgba(0,0,0,0.05)'}, ticks:{color:'#9ca3af',font:{family:'DM Mono',size:11}}},
        x: {grid:{display:false}, ticks:{color:'#6b7280',font:{size:11}}}
      }
    }
  });

  destroyChart('annual');
  charts.annual = new Chart(document.getElementById('annualChart').getContext('2d'), {
    type: 'bar',
    data: {
      labels: YEARS.map(String),
      datasets: [{
        data: annualTotals(),
        backgroundColor: YEAR_COLORS,
        borderRadius: 6, borderSkipped: false
      }]
    },
    options: {
      plugins: {legend:{display:false}, tooltip:{callbacks:{label:ctx=>` ${ctx.raw}mm`}}},
      scales: {
        y: {beginAtZero:false, grid:{color:'rgba(0,0,0,0.05)'}, ticks:{color:'#9ca3af',font:{family:'DM Mono',size:11}}},
        x: {grid:{display:false}, ticks:{color:'#6b7280',font:{size:11}}}
      }
    }
  });
}

function renderPredictions() {
  const container = document.getElementById('probRows');
  container.innerHTML = '';
  THRESHOLDS.forEach(t => {
    const mp = MODEL_DATA[t.label] ?? 0;
    const kp = KALSHI_DATA[t.label] ?? 0;
    const row = document.createElement('div');
    row.className = 'prob-row';
    row.innerHTML = `
      <div class="prob-row-header">
        <span class="prob-row-label">${t.label}</span>
        <span class="prob-row-mm">${t.mm}mm · ${(t.mm/25.4).toFixed(0)} inches</span>
      </div>
      <div class="prob-bars">
        <div class="prob-bar-row">
          <span class="prob-bar-src">model</span>
          <div class="prob-bar-track"><div class="prob-bar-fill" style="width:${mp}%;background:#0ea5e9;"></div></div>
          <span class="prob-bar-pct" style="color:#0ea5e9">${mp}%</span>
        </div>
        <div class="prob-bar-row">
          <span class="prob-bar-src">kalshi</span>
          <div class="prob-bar-track"><div class="prob-bar-fill" style="width:${kp}%;background:#d97706;"></div></div>
          <span class="prob-bar-pct" style="color:#d97706">${kp}%</span>
        </div>
      </div>
    `;
    container.appendChild(row);
  });
}

function renderEdge() {
  const container = document.getElementById('edgeRows');
  const labelEl = document.getElementById('edgeMonthLabel');

  if (selMonth === null || selMonth === -1) {
    labelEl.textContent = '—';
    container.innerHTML = '<div class="empty-state">Select a month above to see edge calculations.</div>';
    return;
  }

  labelEl.textContent = MONTHS_FULL[selMonth];

  container.innerHTML = '';
  THRESHOLDS.forEach(t => {
    const mp = MODEL_DATA[t.label] ?? null;
    const kp = selMonth === 2 ? (KALSHI_DATA[t.label] ?? null) : null;
    const edge = (mp!==null && kp!==null) ? mp - kp : null;

    let bHtml, bClass;
    if (kp === null) {
      bHtml = 'no market data'; bClass = 'badge-neu';
    } else if (edge === null) {
      bHtml = 'no data'; bClass = 'badge-neu';
    } else if (edge > 5) {
      bHtml = `+${edge}%<br>BUY YES`; bClass = 'badge-yes';
    } else if (edge < -5) {
      bHtml = `${edge}%<br>BUY NO`; bClass = 'badge-no';
    } else {
      bHtml = `${edge>=0?'+':''}${edge}%<br>no edge`; bClass = 'badge-neu';
    }

    const row = document.createElement('div');
    row.className = 'edge-row';
    row.innerHTML = `
      <div class="edge-thresh">${t.label}<small>${t.mm}mm · ${(t.mm/25.4).toFixed(0)} in</small></div>
      <div class="edge-prob" style="color:#0ea5e9">${mp!==null?mp+'%':'—'}</div>
      <div class="edge-prob" style="color:#d97706">${kp!==null?kp+'%':'—'}</div>
      <div class="edge-badge ${bClass}">${bHtml}</div>
    `;
    container.appendChild(row);
  });
}

function showTab(name) {
  document.querySelectorAll('.tab-content').forEach(el => el.classList.remove('active'));
  document.querySelectorAll('.tab-btn').forEach(el => el.classList.remove('active'));
  document.getElementById('tab-' + name).classList.add('active');
  document.querySelector('[data-tab="' + name + '"]').classList.add('active');
  if (name === 'historical') renderHistorical();
  if (name === 'predictions') renderPredictions();
  if (name === 'edge') renderEdge();
}

document.getElementById('yearSelect').addEventListener('change', renderHistorical);
showTab('historical');
</script>
</body>
</html>"""

result = HTML.replace('__DAILY__', daily_js).replace('__MONTHLY__', monthly_js)

for fname in ['index.html', 'dashboard.html']:
    with open(fname, 'w') as fh:
        fh.write(result)

print("Done! Generated index.html and dashboard.html")
print("Next: git add -A && git commit -m 'new design' && git push")
