"""
trading_journal.py
Single-file Streamlit UI for Trading Journal (polished header + sidebar fixes)

Fixes included:
- Header stretched to start after sidebar and extend to right canvas edge (comfortable gap)
- Embedded Base64 logo (no dependency)
- Candle frequency selectbox selected text forced black
- Actions (Refresh) button text forced black
- Avoid using f-strings for the large CSS block to prevent parsing issues
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

# -------------------------
# Embedded logo (Base64). If you prefer a different image, replace the PNG bytes below or put logo.png in repo.
# -------------------------
# (Small, attractive bull/bear image encoded to base64)
LOGO_PNG_BASE64 = (
    "iVBORw0KGgoAAAANSUhEUgAAAZAAAABkCAYAAAC4xq9vAAAACXBIWXMAAAsTAAALEwEAmpwYAAAg"
    "AElEQVR4nOy9B5Qb5XU/7f+9mZp2b3Z3b3Z2s7t3dnd7b3d2Z2d3d2d3d3d3e3d3Z3d3d3b3d3d3a"
    "..."  # truncated placeholder - you may replace with your actual base64 PNG data
)
# If you have a real base64 PNG string, put it above. For safety, we will fall back to an embedded SVG if it's not valid length.

def get_logo_data_uri():
    # Prefer real PNG base64 if valid small image present
    if LOGO_PNG_BASE64 and len(LOGO_PNG_BASE64) > 200:
        return "data:image/png;base64," + LOGO_PNG_BASE64
    # Fallback SVG (simple stylized bull/bear + candles feel)
    svg = """
    <svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 1200 120'>
      <defs><linearGradient id='g' x1='0' x2='1'><stop offset='0' stop-color='#062033'/><stop offset='1' stop-color='#071a2a'/></linearGradient></defs>
      <rect width='100%' height='100%' fill='url(#g)'/>
      <g transform='translate(18,14)' opacity='0.12' fill='#46c78a'>
        <rect x='0' y='64' width='7' height='36' rx='1'/><rect x='22' y='60' width='7' height='40' rx='1'/>
      </g>
      <g transform='translate(60,22) scale(0.9)' fill='#000000'>
        <path d='M4 70c6-7 20-12 36-12 16 0 30 6 40 14 6 5 12 5 20 6 9 1 24 6 38 4 9-1 18-6 25-11 5-4 10-7 16-7'/>
      </g>
      <g transform='translate(860,18) scale(0.85)' fill='#000000'>
        <ellipse cx='50' cy='50' rx='46' ry='28' />
      </g>
    </svg>
    """
    return "data:image/svg+xml;base64," + base64.b64encode(svg.encode("utf-8")).decode("ascii")

LOGO_DATA_URI = get_logo_data_uri()

# -------------------------
# Helper: demo data for candles and trades (if real backend not present)
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
    # Replaceable hook: if you have a trading_data.get_recent_candles() it will be used
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
# Streamlit config + CSS (no f-strings for big block)
# -------------------------
st.set_page_config(page_title="Trading - Momentum Surge Scalping", layout="wide", initial_sidebar_state="expanded")

css = """
<style>
html, body, .stApp { background: #ffffff; margin:0; padding:0; }

/* hide top chrome */
header[data-testid="stHeader"], #MainMenu, .css-1rs6os.edgvbvh3 { display: none !important; }
.block-container, .reportview-container .main .block-container, .main .block-container {
  padding-top: 0.5rem !important;
  padding-left: 0rem !important;
  padding-right: 0rem !important;
}

/* Sidebar width & layout */
.stSidebar { background: #071a2a !important; padding-top: 12px !important; width: 300px; }

/* CONTROL header */
.control-header {
  color:#ffffff;
  font-weight:900;
  font-size:22px;
  padding:14px;
  background:#071a2a;
  border-radius:8px;
  text-align:center;
  text-transform:uppercase;
  border:1px solid rgba(255,255,255,0.04);
  margin-bottom:10px;
}

/* HERO: stretch from after sidebar to right canvas edge, leave 40px comfortable gap */
.hero {
  width: calc(100% - 340px); /* sidebar (300) + 40px comfortable gap */
  margin-left: 300px;
  border-radius:10px;
  box-shadow: 0 6px 18px rgba(7,18,28,0.06);
  background: linear-gradient(90deg, #062033 0%, #071a2a 100%);
  color:#ffffff;
  display:flex; align-items:center; gap:18px;
  padding:14px 18px; margin-top: 6px; margin-bottom: 12px;
}

/* logo: blend with hero bg */
.hero-logo { flex: 0 0 120px; display:flex; align-items:center; justify-content:center; }
.hero-logo img { height: 96px; width:auto; border-radius:6px; display:block; background:transparent; padding:0; margin:0; box-shadow:none; }

/* title */
.hero-title { display:flex; flex-direction:column; }
.hero-title .main { font-size:22px; font-weight:800; line-height:1.05; }
.hero-title .sub { margin-top:6px; font-size:12px; color:#cfe9ff; }

/* make sidebar inputs white bg + black text */
.stSidebar * { color: #ffffff !important; }
.stSidebar input, .stSidebar select, .stSidebar textarea, .stSidebar .stButton>button, .stSidebar .stDownloadButton>button {
  background: #ffffff !important; color: #000000 !important; border-radius:6px !important;
}

/* force the selected text inside selectboxes to be black (catch-all) */
.stSidebar div[role="combobox"], .stSidebar select, .stSidebar .stSelectbox, .stSidebar button {
  color: #000000 !important;
}
.stSidebar div[role="combobox"] span, .stSidebar .stSelectbox span, .stSidebar .stSelectbox div {
  color: #000000 !important;
}

/* force buttons and nested spans to black so "Refresh" shows */
.stSidebar .stButton>button, .stSidebar .stButton>button span, .stSidebar button, .stSidebar button span {
  color: #000000 !important;
}

/* candle frequency / actions labels */
.sidebar-label-black { color:#000000 !important; font-weight:700 !important; margin-bottom:6px; display:block; }

/* journal table */
.journal-title { margin-top:8px; margin-bottom:6px; font-size:16px; font-weight:700; }
.journal-table th { text-transform: capitalize; background:#f7fafc; padding:8px; text-align:left; font-weight:700; }
.journal-table tr:nth-child(even) { background:#fbfbfb; }

/* responsive tweak */
@media (max-width: 1100px) {
  .hero { width: calc(100% - 300px); margin-left: 300px; }
}
</style>
"""
st.markdown(css, unsafe_allow_html=True)

# -------------------------
# Render header (logo left, title right)
# -------------------------
hero_html = """
<div class="hero" role="banner" aria-label="Trading hero header">
  <div class="hero-logo"><img src='""" + LOGO_DATA_URI + """' alt="logo" /></div>
  <div class="hero-title">
    <div class="main">Trading - Momentum Surge Scalping</div>
    <div class="sub">Candles • EMA9/EMA21 • VWAP • RSI • Only BUY CE/PE</div>
  </div>
  <div style="margin-left:auto;"></div>
</div>
"""
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

    st.markdown("<h3 style='color:#ffffff;'>Emas</h3>", unsafe_allow_html=True)
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
