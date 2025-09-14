"""
trading_journal.py
Polished single-file Streamlit app:
- Header spans canvas (starts after sidebar; comfortable gap)
- Logo embedded (SVG data URI)
- Candle frequency selected text forced black
- Actions (Refresh) button text forced black
- Avoid fragile f-strings in CSS
"""

import base64
import os
import math
from datetime import datetime, timedelta

import pandas as pd
import numpy as np

try:
    import streamlit as st
except Exception as e:
    raise RuntimeError("Please install streamlit: pip install streamlit") from e

try:
    import plotly.graph_objects as go
    from plotly.subplots import make_subplots
except Exception as e:
    raise RuntimeError("Please install plotly: pip install plotly") from e

# -------------------------
# Constants
# -------------------------
DEEP_NAVY = "#071a2a"
ACCENT_ORANGE = "#ff7a18"
ACCENT_GREEN = "#0f8b4f"
ACCENT_RED = "#b72828"
CANVAS_BG = "#ffffff"
LOGO_HEIGHT = 96
SIDEBAR_WIDTH = 300  # px
COMFORT_GAP = 40     # px between sidebar and hero

# -------------------------
# Embedded SVG logo (base64) - crisp, scales well
# -------------------------
SVG = """
<svg xmlns='http://www.w3.org/2000/svg' width='300' height='300' viewBox='0 0 300 300' preserveAspectRatio='xMidYMid meet'>
  <defs>
    <linearGradient id='g1' x1='0' x2='1'>
      <stop offset='0' stop-color='#0b3b3b'/>
      <stop offset='1' stop-color='#06303a'/>
    </linearGradient>
  </defs>
  <rect width='100%' height='100%' rx='12' ry='12' fill='url(#g1)'/>
  <g transform='translate(22,24) scale(0.9)' fill='#041820' opacity='0.98'>
    <!-- stylized bull -->
    <path d='M40 160c8-20 28-40 48-44 22-4 44 8 66 14 20 6 42 2 62-6 12-5 24-12 36-15 10-2 22 2 30 10 6 6 10 14 10 22 0 18-14 34-30 44-20 12-44 18-68 16-26-2-48-12-74-18-28-6-54-6-78-13z'/>
    <!-- stylized bear -->
    <path d='M190 180c10-10 22-18 36-18 12 0 24 6 36 10 10 4 22 4 32 0 8-4 12-10 16-18 4-10 10-18 18-20 6-2 12 0 18 6 4 4 6 10 6 16 0 8-4 16-10 22-10 10-22 18-36 24-18 8-38 12-56 8-20-4-36-14-54-24z'/>
  </g>
  <g transform='translate(18,12)'>
    <g transform='translate(36,42)'>
      <!-- simplistic rising candles background -->
      <rect x='0' y='64' width='6' height='36' rx='1' fill='#13a37a' opacity='0.22' />
      <rect x='18' y='52' width='6' height='48' rx='1' fill='#13a37a' opacity='0.22' />
      <rect x='36' y='44' width='6' height='56' rx='1' fill='#13a37a' opacity='0.22' />
      <rect x='54' y='32' width='6' height='68' rx='1' fill='#13a37a' opacity='0.22' />
    </g>
  </g>
</svg>
"""
LOGO_DATA_URI = "data:image/svg+xml;base64," + base64.b64encode(SVG.encode("utf-8")).decode("ascii")

# -------------------------
# Demo data helpers (candles + trades)
# -------------------------
def demo_candles():
    now = datetime.now()
    periods = 80
    base = 25000.0
    rng = pd.date_range(now - timedelta(minutes=periods * 5), periods=periods, freq="5T")
    np.random.seed(42)
    moves = np.random.normal(loc=0.05, scale=0.8, size=periods).cumsum()
    close = base + moves
    open_ = np.concatenate(([base], close[:-1]))
    high = np.maximum(open_, close) + np.random.rand(periods) * 4
    low = np.minimum(open_, close) - np.random.rand(periods) * 4
    volume = np.random.randint(50, 1500, size=periods)
    df = pd.DataFrame({"datetime": rng, "open": open_, "high": high, "low": low, "close": close, "volume": volume})
    return df

def demo_trades():
    now = datetime.now()
    syms = ["NIFTY23SEP17500CE", "NIFTY23SEP17600CE", "BANKNIFTY23SEP42000CE", "NIFTY23SEP17400PE"]
    rows = []
    for i, s in enumerate(syms):
        entry = now - timedelta(hours=6 - i)
        exit = entry + timedelta(minutes=12 + i * 6)
        ep = round(100 + i * 9 + np.random.rand() * 6, 2)
        xp = round(ep + np.random.normal(loc=20 + i * 3, scale=6), 2)
        pnl = round(xp - ep, 2)
        rows.append({
            "Symbol": s,
            "Side": "BUY",
            "Entry Time": entry.strftime("%Y-%m-%d %H:%M:%S"),
            "Entry Price": ep,
            "Exit Time": exit.strftime("%Y-%m-%d %H:%M:%S"),
            "Exit Price": xp,
            "Comments": "Momentum entry — rode the surge" if pnl > 0 else "Measured loss",
            "Gross PnL": pnl,
        })
    return pd.DataFrame(rows)

def try_get_candles():
    try:
        import trading_data
        if hasattr(trading_data, "get_recent_candles"):
            df = trading_data.get_recent_candles()
            if isinstance(df, pd.DataFrame) and "close" in df.columns:
                return df
    except Exception:
        pass
    return demo_candles()

def try_get_trades():
    try:
        import trading_journal_backend as tjb
        if hasattr(tjb, "get_trades"):
            df = tjb.get_trades()
            if isinstance(df, pd.DataFrame):
                return df
    except Exception:
        pass
    return demo_trades()

# -------------------------
# Indicators
# -------------------------
def ema(series, span):
    return series.ewm(span=span, adjust=False).mean()

def vwap(df):
    tp = (df["high"] + df["low"] + df["close"]) / 3.0
    return (tp * df["volume"]).cumsum() / df["volume"].cumsum()

def rsi(series, period=14):
    delta = series.diff()
    up = delta.clip(lower=0)
    down = -delta.clip(upper=0)
    ma_up = up.ewm(alpha=1 / period, min_periods=period).mean()
    ma_down = down.ewm(alpha=1 / period, min_periods=period).mean()
    rs = ma_up / ma_down
    return 100 - (100 / (1 + rs))

# -------------------------
# Streamlit config + CSS (non-f-string block)
# -------------------------
st.set_page_config(page_title="Trading - Momentum Surge Scalping", layout="wide", initial_sidebar_state="expanded")

css = """
<style>
/* Canvas + remove Streamlit top chrome */
html, body, .stApp { background: #ffffff; margin:0; padding:0; }
header[data-testid="stHeader"], #MainMenu, .css-1rs6os.edgvbvh3 { display: none !important; }

/* Reserve space for the fixed hero header (hero height 96px + top margin) */
.block-container, .reportview-container .main .block-container, .main .block-container {
  padding-top: 140px !important; /* keep hero space */
  padding-left: 20px !important;
  padding-right: 20px !important;
  max-width: none !important;
}

/* Sidebar appearance */
.stSidebar { background: #071a2a !important; padding-top: 12px !important; width: 300px !important; z-index: 2000 !important; }

/* CONTROL header */
.control-header {
  color:#ffffff; font-weight:900; font-size:22px; padding:14px;
  background:#071a2a; border-radius:8px; text-align:center; text-transform:uppercase;
  border:1px solid rgba(255,255,255,0.04); margin-bottom:10px;
}

/* HERO - fixed and stretched (unchanged) */
.hero {
  position: fixed !important;
  top: 16px !important;
  left: calc(300px + 24px) !important; /* hero starts after sidebar + small gap */
  right: 24px !important;
  height: 96px !important;
  z-index: 1500 !important;
  border-radius:10px !important;
  box-shadow: 0 8px 22px rgba(7,18,28,0.10) !important;
  background: linear-gradient(90deg, #062033 0%, #071a2a 100%) !important;
  color:#ffffff !important;
  display:flex !important;
  align-items:center !important;
  gap:18px !important;
  padding:14px 18px !important;
  overflow:hidden !important;
}

/* Make main content align with hero left edge (chart + PnL row) */
.reportview-container .main, .main {
  margin-left: calc(300px + 24px) !important; /* align content with hero left */
  max-width: calc(100% - (300px + 48px)) !important;
}

/* Sidebar input readability */
.stSidebar * { color: #ffffff !important; }
.stSidebar input, .stSidebar select, .stSidebar textarea, .stSidebar .stButton>button, .stSidebar .stDownloadButton>button {
  background: #ffffff !important; color: #000000 !important; border-radius:6px !important;
}

/* Force selectbox + dropdown text to black broadly */
.stSidebar div[role="combobox"], .stSidebar .stSelectbox, .stSidebar .stSelectbox *, .stSidebar select, .stSidebar select * {
  color: #000000 !important;
  -webkit-text-fill-color: #000000 !important;
}

/* Increase Trading Journal width and make Comments column roomier */
.journal-table { width: 100% !important; table-layout: auto !important; }
.journal-table th, .journal-table td { padding: 10px 14px !important; vertical-align: middle !important; }
.journal-table td:nth-child(1) { width: 40px !important; }  /* No. */
.journal-table td:nth-child(2) { width: 180px !important; } /* Symbol */
.journal-table td:nth-child(3) { width: 160px !important; } /* Entry Time */
.journal-table td:nth-child(4) { width: 110px !important; } /* Entry Price */
.journal-table td:nth-child(5) { width: 160px !important; } /* Exit Time */
.journal-table td:nth-child(6) { width: 110px !important; } /* Exit Price */
.journal-table td:nth-child(7) { width: 32% !important; }   /* Comments larger area */
.journal-table td:nth-child(8) { width: 110px !important; } /* Gross PnL */

/* ensure plotly uses full width */
.stPlotlyChart > div, .element-container > .stPlotlyChart, .stPlotlyChart { width: 100% !important; }

/* small responsive fallback */
@media (max-width: 1200px) {
  .reportview-container .main, .main { margin-left: calc(300px + 16px) !important; }
  .journal-table td:nth-child(7) { width: auto !important; }
}

/* ==== HERO / LOGO FIX (injected override) ==== */
/* Ensure hero is a left-aligned flex container and logo is clamped */
.hero {
  position: fixed !important;
  top: 16px !important;
  left: calc(300px + 24px) !important;
  right: 24px !important;
  height: 96px !important;
  display: flex !important;
  align-items: center !important;
  justify-content: flex-start !important; /* keep content left */
  gap: 18px !important;
  padding: 12px 18px !important;
  overflow: visible !important;
  z-index: 1600 !important;
}

/* Logo container keeps fixed width and centers the image */
.hero-logo {
  flex: 0 0 96px !important;
  display: flex !important;
  align-items: center !important;
  justify-content: center !important;
  margin-right: 12px !important;
  background: transparent !important;
}

/* Clamp image size and ensure it won't expand the hero */
.hero-logo img {
  height: 72px !important;
  width: auto !important;
  max-width: 100% !important;
  object-fit: contain !important;
  border-radius: 8px !important;
  box-shadow: none !important;
  display: block !important;
}

/* Keep title left-aligned and vertically centered */
.hero-title { display:flex !important; flex-direction:column !important; align-items:flex-start !important; }
.hero-title .main { font-size:22px !important; font-weight:800 !important; line-height:1.05 !important; text-align:left !important; }
.hero-title .sub { font-size:12px !important; color:#cfe9ff !important; text-align:left !important; margin-top:6px !important; }

/* small defensive rule: prevent hero internal elements from wrapping badly */
.hero > * { min-width: 0 !important; }

/* end hero override */
</style>
"""
st.markdown(css, unsafe_allow_html=True)

# -------------------------
# Render header
# -------------------------

# --- PNG logo loader (auto): tries common names then any PNG in repo root ---
import os, base64, glob
_png_candidates = ["header_logo.png", "logo.png", "logo-header.png"] + sorted(glob.glob("*.png"))
_LOGO_PATH = None
for _p in _png_candidates:
    if _p and os.path.exists(_p):
        _LOGO_PATH = _p
        break
if _LOGO_PATH:
    try:
        with open(_LOGO_PATH, "rb") as _f:
            _b = base64.b64encode(_f.read()).decode("ascii")
        LOGO_DATA_URI = "data:image/png;base64," + _b
        print(f"INFO: Using PNG logo: {_LOGO_PATH}")
    except Exception as _e:
        print("WARNING: failed to load PNG logo:", _e)
# --- end PNG logo loader ---
hero_html = (
    "<div class='hero' role='banner' aria-label='Trading hero header'>"
    "<div class='hero-logo'><img src='" + LOGO_DATA_URI + "' alt='logo' /></div>"
    "<div class='hero-title'>"
    "<div class='main'>Trading - Momentum Surge Scalping</div>"
    "<div class='sub'>Candles • EMA9/EMA21 • VWAP • RSI • Only BUY CE/PE</div>"
    "</div>"
    "<div style='margin-left:auto;'></div>"
    "</div>"
)
st.markdown(hero_html, unsafe_allow_html=True)

# -------------------------
# Top PnL row / progress
# -------------------------
pnl_col1, pnl_col2, pnl_col3, pnl_col4 = st.columns([1, 1, 1, 3])

trades_df = try_get_trades()
for c in ["Symbol", "Side", "Entry Time", "Entry Price", "Exit Time", "Exit Price", "Comments", "Gross PnL"]:
    if c not in trades_df.columns:
        trades_df[c] = ""

def is_buy_ce_pe(sym, side):
    try:
        return str(side).strip().upper() == "BUY" and (("CE" in str(sym).upper()) or ("PE" in str(sym).upper()))
    except Exception:
        return False

trades_df = trades_df[trades_df.apply(lambda r: is_buy_ce_pe(r.get("Symbol", ""), r.get("Side", "")), axis=1)].reset_index(drop=True)

gross_total = pd.to_numeric(trades_df.get("Gross PnL", 0), errors="coerce").fillna(0).sum()
win_rate = 0.0
if len(trades_df) > 0:
    wins = pd.to_numeric(trades_df.get("Gross PnL", 0), errors="coerce") > 0
    win_rate = float(wins.sum()) / max(1, len(trades_df)) * 100

with pnl_col1:
    st.markdown("<div style='background:white;padding:8px;border-radius:8px;'><strong>Gross PnL</strong><div style='font-size:20px;color:{};font-weight:700;'>₹ {:.2f}</div></div>".format(ACCENT_GREEN if gross_total>=0 else ACCENT_RED, gross_total), unsafe_allow_html=True)
with pnl_col2:
    st.markdown("<div style='background:white;padding:8px;border-radius:8px;'><strong>Total Earnings (Day)</strong><div style='font-size:20px;color:{};font-weight:700;'>₹ {:.2f}</div></div>".format(ACCENT_ORANGE, gross_total), unsafe_allow_html=True)
with pnl_col3:
    st.markdown("<div style='background:white;padding:8px;border-radius:8px;'><strong>Win Rate</strong><div style='font-size:20px;color:{};font-weight:700;'>{:.1f}%</div></div>".format(DEEP_NAVY, win_rate), unsafe_allow_html=True)

# progress mapping
try:
    scale = 1000.0
    progress_val = 1.0 / (1.0 + math.exp(-gross_total / scale))
    progress_val = max(0.0, min(1.0, progress_val))
except Exception:
    progress_val = 0.12

with pnl_col4:
    st.markdown("<div style='padding:8px;'><div style='display:flex;justify-content:space-between;align-items:center;font-size:12px;color:#09212f;'><strong>Today's Progress</strong><span style='color:#577387'>Goal indicator: {}%</span></div><div style='height:12px;margin-top:6px;background:#e6eef5;border-radius:8px;overflow:hidden;'><div style='width:{}%;height:100%;background:linear-gradient(90deg,{} , {});'></div></div></div>".format(int(progress_val*100), int(progress_val*100), ACCENT_GREEN, ACCENT_ORANGE), unsafe_allow_html=True)

st.markdown("<hr style='margin-top:12px;margin-bottom:12px;'/>", unsafe_allow_html=True)

# -------------------------
# Sidebar controls
# -------------------------
with st.sidebar:
    st.markdown("<div class='control-header'>CONTROL</div>", unsafe_allow_html=True)
    st.markdown("<div style='height:6px'></div>", unsafe_allow_html=True)

    st.markdown("<h3 style='color:#ffffff;'>Symbol</h3>", unsafe_allow_html=True)
    symbol = st.text_input("Symbol (eg. NIFTY23SEP17500CE)", value="NIFTY23SEP17500CE")

    st.markdown('<div class="sidebar-label-black">Candle frequency</div>', unsafe_allow_html=True)
    interval = st.selectbox("", ["1m", "3m", "5m", "15m", "30m"], index=3)

    st.markdown("<h3 style='color:#ffffff;'>EMAs</h3>", unsafe_allow_html=True)
    ema_short = st.number_input("EMA (short)", min_value=2, max_value=50, value=9)
    ema_long = st.number_input("EMA (long)", min_value=5, max_value=200, value=21)

    st.markdown("<h3 style='color:#ffffff;'>Show</h3>", unsafe_allow_html=True)
    show_rsi = st.checkbox("Show RSI", value=True)
    show_vwap = st.checkbox("Show VWAP", value=True)

    st.markdown('<div class="sidebar-label-black">Actions</div>', unsafe_allow_html=True)
    if st.button("Refresh Data"):
        st.experimental_rerun()

# -------------------------
# Chart + Journal
# -------------------------
left_col, right_col = st.columns([3, 1], gap="small")

candles = try_get_candles().copy()
if "datetime" in candles.columns:
    candles["datetime"] = pd.to_datetime(candles["datetime"])
else:
    candles["datetime"] = pd.to_datetime(candles.index)
candles = candles.sort_values("datetime").reset_index(drop=True)

candles["EMA9"] = ema(candles["close"], 9)
candles["EMA21"] = ema(candles["close"], 21)
if "volume" not in candles.columns:
    candles["volume"] = 1
candles["VWAP"] = vwap(candles)
candles["RSI"] = rsi(candles["close"])

fig = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.06, row_heights=[0.75, 0.25])

fig.add_trace(go.Candlestick(
    x=candles["datetime"], open=candles["open"], high=candles["high"], low=candles["low"], close=candles["close"],
    increasing=dict(fillcolor=ACCENT_GREEN, line=dict(color=ACCENT_GREEN)),
    decreasing=dict(fillcolor=ACCENT_RED, line=dict(color=ACCENT_RED)),
    showlegend=False, name="Price"
), row=1, col=1)

fig.add_trace(go.Scatter(x=candles["datetime"], y=candles["EMA9"], mode="lines", name="EMA9", line=dict(color="#1f77b4", width=1.4)), row=1, col=1)
fig.add_trace(go.Scatter(x=candles["datetime"], y=candles["EMA21"], mode="lines", name="EMA21", line=dict(color="#ff7f0e", width=1.4)), row=1, col=1)
fig.add_trace(go.Scatter(x=candles["datetime"], y=candles["VWAP"], mode="lines", name="VWAP", line=dict(color="#9467bd", width=1.2, dash="dash")), row=1, col=1)

fig.add_trace(go.Scatter(x=candles["datetime"], y=candles["RSI"], mode="lines", name="RSI", line=dict(color="#2ca02c", width=1.4)), row=2, col=1)
fig.add_hline(y=70, line_dash="dash", row=2, col=1, line_color="#999999", opacity=0.6)
fig.add_hline(y=30, line_dash="dash", row=2, col=1, line_color="#999999", opacity=0.6)

fig.update_layout(plot_bgcolor=CANVAS_BG, paper_bgcolor=CANVAS_BG, margin=dict(l=30, r=10, t=10, b=30), legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1), hovermode="x unified")
fig.update_xaxes(showgrid=False, row="all", col=1, title_text="Time (IST)", tickfont=dict(size=10))
fig.update_yaxes(showgrid=False, row="all", col=1, title_text="Price (INR)", tickfont=dict(size=10))
fig.update_yaxes(showgrid=False, row=2, col=1, title_text="RSI", tickfont=dict(size=10))
fig.update_xaxes(showline=False)
fig.update_yaxes(showline=False)

with left_col:
    st.plotly_chart(fig, use_container_width=True, config={"modeBarButtonsToRemove": ["lasso2d", "select2d", "zoom2d"]})

    st.markdown("<div class='journal-title'>Trading Journal</div>", unsafe_allow_html=True)
    trades_display = trades_df.copy().reset_index(drop=True)
    trades_display.insert(0, "No.", trades_display.index + 1)
    cols = ["No.", "Symbol", "Entry Time", "Entry Price", "Exit Time", "Exit Price", "Comments", "Gross PnL"]
    for c in cols:
        if c not in trades_display.columns:
            trades_display[c] = ""
    trades_display = trades_display[cols]

    def fmt_price(x):
        try:
            x = float(x)
            return "₹ {:.2f}".format(x)
        except Exception:
            return x if x else ""

    trades_display["Entry Price"] = trades_display["Entry Price"].apply(fmt_price)
    trades_display["Exit Price"] = trades_display["Exit Price"].apply(fmt_price)
    trades_display["Gross PnL"] = trades_display["Gross PnL"].apply(fmt_price)

    html = "<table class='journal-table' width='100%' style='border-collapse:collapse;'>"
    html += "<thead><tr>"
    for h in cols:
        html += "<th>{}</th>".format(h)
    html += "</tr></thead><tbody>"
    for idx, row in trades_display.iterrows():
        html += "<tr>"
        for h in cols:
            cell = row[h] if pd.notna(row[h]) else ""
            html += "<td style='padding:8px; vertical-align:top; border-bottom:1px solid #f1f1f1;'>{}</td>".format(cell)
        html += "</tr>"
    html += "</tbody></table>"
    st.markdown(html, unsafe_allow_html=True)

with right_col:
    st.markdown("<div style='padding:6px;border-radius:8px;background:#ffffff;box-shadow:0 1px 3px rgba(10,10,10,0.04);'>", unsafe_allow_html=True)
    st.markdown("<h3 style='margin:0 0 6px 0;'>Quick stats</h3>", unsafe_allow_html=True)
    st.markdown("<div style='font-size:14px;margin-bottom:6px;'>Open Positions: <strong>{}</strong></div>".format(len(trades_df)), unsafe_allow_html=True)
    st.markdown("<div style='font-size:14px;margin-bottom:6px;'>Realized (Gross): <strong>₹ {:.2f}</strong></div>".format(gross_total), unsafe_allow_html=True)
    st.markdown("<div style='font-size:14px;margin-bottom:6px;'>Win Rate: <strong>{:.1f}%</strong></div>".format(win_rate), unsafe_allow_html=True)

st.markdown("<div style='height:28px'></div>", unsafe_allow_html=True)
