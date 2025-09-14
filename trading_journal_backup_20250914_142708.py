"""
trading_journal.py  (Decisive fix)
- Hides Streamlit chrome (header/menu/footer) to remove the top gap.
- Persistent logo (left) in hero header — no status pill / no log.
- Deep navy sidebar with readable controls.
- Trading Journal: No. column, zebra stripes.
- Defensive fallbacks for missing data providers.
Author: Assistant
Date: 2025-09-14
"""

import base64
import os
import re
import math
from datetime import datetime, timedelta

import pandas as pd
import numpy as np

# Defensive imports
try:
    import streamlit as st
except Exception as e:
    raise RuntimeError("Streamlit required. Install: pip install streamlit") from e

try:
    import plotly.graph_objects as go
    from plotly.subplots import make_subplots
except Exception as e:
    raise RuntimeError("Plotly required. Install: pip install plotly") from e

# --------------------------
# Logo SVG (strong silhouettes, high contrast)
# --------------------------
SVG = r'''
<svg xmlns="http://www.w3.org/2000/svg" width="1600" height="160" viewBox="0 0 1600 160">
  <defs>
    <linearGradient id="g1" x1="0" x2="0" y1="0" y2="1">
      <stop offset="0%" stop-color="#072a3a"/>
      <stop offset="100%" stop-color="#0b3546"/>
    </linearGradient>
  </defs>
  <rect width="1600" height="160" fill="url(#g1)"/>
  <!-- subdued uptrend candles (muted) -->
  <g transform="translate(70,12)" opacity="0.10" fill="#46c78a">
    <rect x="0" y="92" width="10" height="42" rx="2"/><rect x="28" y="86" width="10" height="48" rx="2"/>
    <rect x="56" y="80" width="10" height="54" rx="2"/><rect x="84" y="74" width="10" height="60" rx="2"/>
    <rect x="112" y="68" width="10" height="66" rx="2"/><rect x="140" y="64" width="10" height="70" rx="2"/>
  </g>
  <!-- Bull silhouette - solid black -->
  <g transform="translate(280,18) scale(0.95)" fill="#000000">
    <path d="M10 120 L40 90 L80 80 L120 60 L150 50 L180 46 L220 44 L260 48 L300 66 L320 84 L300 98 L260 112 L220 122 L180 128 L140 130 L100 130 L60 128 Z"/>
  </g>
  <!-- Bear silhouette - solid black -->
  <g transform="translate(1020,18) scale(0.95)" fill="#000000">
    <path d="M10 120 L40 108 L80 96 L120 90 L160 88 L200 90 L240 100 L270 116 L260 124 L220 132 L180 136 L140 138 L100 138 L60 136 Z"/>
  </g>
  <text x="36" y="36" font-family="Helvetica, Arial, sans-serif" font-size="22" fill="#ffffff" font-weight="700">
    Trading - Momentum Surge Scalping
  </text>
  <text x="36" y="56" font-family="Helvetica, Arial, sans-serif" font-size="12" fill="#cfe9ff">
    Candles • EMA9/EMA21 • VWAP • RSI • Only BUY CE/PE
  </text>
</svg>
'''
SVG_B64 = base64.b64encode(SVG.encode("utf-8")).decode("ascii")
HEADER_IMAGE_B64 = "data:image/svg+xml;base64," + SVG_B64

# --------------------------
# Colors / constants
# --------------------------
DEEP_NAVY = "#071a2a"
ACCENT_ORANGE = "#ff7a18"
ACCENT_GREEN = "#0f8b4f"
ACCENT_RED = "#b72828"
WHITE = "#ffffff"
CANVAS_BG = "#ffffff"

# --------------------------
# Fallback data providers
# --------------------------
def try_get_candles():
    try:
        import trading_data
        if hasattr(trading_data, "get_recent_candles"):
            df = trading_data.get_recent_candles()
            if isinstance(df, pd.DataFrame) and "close" in df.columns:
                return df
    except Exception:
        pass
    now = datetime.now()
    periods = 60
    base = 25000.0
    rng = pd.date_range(now - timedelta(minutes=periods * 5), periods=periods, freq="5T")
    np.random.seed(42)
    moves = np.random.normal(loc=0.12, scale=0.6, size=periods).cumsum()
    close = base + moves
    open_ = np.concatenate(([base], close[:-1]))
    high = np.maximum(open_, close) + np.random.rand(periods) * 5
    low = np.minimum(open_, close) - np.random.rand(periods) * 5
    volume = np.random.randint(100, 1000, size=periods)
    return pd.DataFrame({"datetime": rng, "open": open_, "high": high, "low": low, "close": close, "volume": volume})

def try_get_trades():
    try:
        import trading_journal_backend as tjb
        if hasattr(tjb, "get_trades"):
            df = tjb.get_trades()
            if isinstance(df, pd.DataFrame):
                return df
    except Exception:
        pass
    now = datetime.now()
    syms = ["NIFTY23SEP17500CE", "NIFTY23SEP17600CE", "BANKNIFTY23SEP42000CE", "NIFTY23SEP17400PE"]
    rows = []
    for i, s in enumerate(syms):
        entry = now - timedelta(hours=6 - i)
        exit = entry + timedelta(minutes=12 + i * 6)
        ep = round(100 + i * 10 + np.random.rand() * 5, 2)
        xp = round(ep + np.random.normal(loc=20 + i * 3, scale=6), 2)
        pnl = round(xp - ep, 2)
        rows.append({
            "Symbol": s,
            "Side": "BUY",
            "Entry Time": entry.strftime("%Y-%m-%d %H:%M:%S"),
            "Entry Price": ep,
            "Exit Time": exit.strftime("%Y-%m-%d %H:%M:%S"),
            "Exit Price": xp,
            "Comments": "Momentum entry — rode the surge" if pnl > 0 else "Small loss",
            "Gross PnL": pnl
        })
    return pd.DataFrame(rows)

# --------------------------
# Indicators
# --------------------------
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

# --------------------------
# Page config + CSS
# - Hides Streamlit header/menu/footer to eliminate top gap and deliver a clean hero
# --------------------------
st.set_page_config(page_title="Trading - Momentum Surge Scalping", layout="wide", initial_sidebar_state="expanded")

css = f"""
<style>
/* Hide Streamlit chrome (menu/header/footer) so hero sits flush with browser top */
header, #MainMenu, .stApp > header, footer, .css-1rs6os.edgvbvh3 {{ display: none !important; }}
html, body, .stApp {{ margin:0; padding:0; background:{CANVAS_BG}; }}

/* Hero header block inside content (no fixed position) */
.hero {{
  margin: 0;
  border-radius: 6px;
  overflow:hidden;
  box-shadow: 0 2px 10px rgba(4,10,20,0.06);
}}
.hero-inner {{
  display:flex; align-items:center; gap:14px;
  padding: 12px 18px;
  background: linear-gradient(90deg, {DEEP_NAVY} 0%, #062033 100%);
  color: {WHITE};
}}

/* force logo size */
.hero-logo img {{ height:120px; width:auto; border-radius:6px; }}

/* Push the sidebar down a bit to avoid overlap on narrow screens */
.stSidebar {{ background: {DEEP_NAVY} !important; padding-top: 18px !important; }}

/* CONTROL header */
.control-header {{
  color: {WHITE};
  background: {DEEP_NAVY};
  padding: 12px 10px;
  font-weight:700;
  border-radius:6px;
  text-transform: uppercase;
  text-align:center;
  font-size:18px;
  letter-spacing:0.6px;
  border: 1px solid rgba(255,255,255,0.04);
}}

/* ensure sidebar elements readable */
.stSidebar * {{ color:#ffffff !important; }}
.stSidebar input, .stSidebar select, .stSidebar textarea, .stSidebar .stButton>button, .stSidebar .stDownloadButton>button {{
    background: #ffffff !important; color: #000000 !important; border-radius:6px !important;
}}

/* Journal styling */
.journal-title {{ margin-top:8px; margin-bottom:6px; font-size:16px; font-weight:700; }}
.journal-table th {{ text-transform: capitalize; background:#f7fafc; padding:8px; text-align:left; font-weight:600; }}
.journal-table tr:nth-child(even) {{ background:#fbfbfb; }}
</style>
"""
st.markdown(css, unsafe_allow_html=True)

# --------------------------
# Hero header (no status pill, logo left)
# --------------------------
hero_html = f"""
<div class="hero" role="banner">
  <div class="hero-inner">
    <div class="hero-logo"><img src="{HEADER_IMAGE_B64}" alt="logo"/></div>
    <div style="display:flex; flex-direction:column;">
      <div style="font-size:20px; font-weight:700; color:{WHITE};">Trading - Momentum Surge Scalping</div>
      <div style="font-size:12px; color:#cfe9ff; margin-top:4px;">Candles • EMA9/EMA21 • VWAP • RSI • Only BUY CE/PE</div>
    </div>
    <div style="margin-left:auto;"></div>
  </div>
</div>
"""
st.markdown(hero_html, unsafe_allow_html=True)

# small spacer
st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)

# --------------------------
# PnL row
# --------------------------
pnl_col1, pnl_col2, pnl_col3, pnl_col4 = st.columns([1,1,1,3])

trades_df = try_get_trades()
for c in ["Symbol","Side","Entry Time","Entry Price","Exit Time","Exit Price","Comments","Gross PnL"]:
    if c not in trades_df.columns:
        trades_df[c] = ""

def is_buy_ce_pe(sym, side):
    try:
        return str(side).strip().upper() == "BUY" and (("CE" in str(sym).upper()) or ("PE" in str(sym).upper()))
    except Exception:
        return False

trades_df = trades_df[trades_df.apply(lambda r: is_buy_ce_pe(r.get("Symbol",""), r.get("Side","")), axis=1)].reset_index(drop=True)

gross_total = pd.to_numeric(trades_df.get("Gross PnL",0), errors="coerce").fillna(0).sum()
win_rate = 0.0
if len(trades_df)>0:
    wins = pd.to_numeric(trades_df.get("Gross PnL",0), errors="coerce")>0
    win_rate = float(wins.sum())/max(1,len(trades_df))*100

with pnl_col1:
    st.markdown(f"<div style='background:white; padding:8px; border-radius:8px;'><strong>Gross PnL</strong><div style='font-size:20px; color:{ACCENT_GREEN if gross_total>=0 else ACCENT_RED}; font-weight:700;'>₹ {gross_total:.2f}</div></div>", unsafe_allow_html=True)
with pnl_col2:
    st.markdown(f"<div style='background:white; padding:8px; border-radius:8px;'><strong>Total Earnings (Day)</strong><div style='font-size:20px; color:{ACCENT_ORANGE}; font-weight:700;'>₹ {gross_total:.2f}</div></div>", unsafe_allow_html=True)
with pnl_col3:
    st.markdown(f"<div style='background:white; padding:8px; border-radius:8px;'><strong>Win Rate</strong><div style='font-size:20px; color:{DEEP_NAVY}; font-weight:700;'>{win_rate:.1f}%</div></div>", unsafe_allow_html=True)

# progress bar
try:
    scale = 1000.0
    progress_val = 1.0/(1.0+math.exp(-gross_total/scale))
    progress_val = max(0.0, min(1.0, progress_val))
except Exception:
    progress_val = 0.12

with pnl_col4:
    st.markdown(f"""
    <div style="padding:8px;">
      <div style="display:flex; justify-content:space-between; align-items:center; font-size:12px; color:#09212f;">
        <strong>Today's Progress</strong><span style="color:#577387">Goal indicator: {int(progress_val*100)}%</span>
      </div>
      <div style="height:12px; margin-top:6px; background:#e6eef5; border-radius:8px; overflow:hidden;">
        <div style="width:{int(progress_val*100)}%; height:100%; background: linear-gradient(90deg, {ACCENT_GREEN}, {ACCENT_ORANGE});"></div>
      </div>
    </div>
    """, unsafe_allow_html=True)

st.markdown("<hr style='margin-top:12px; margin-bottom:12px;'/>", unsafe_allow_html=True)

# --------------------------
# Sidebar
# --------------------------
with st.sidebar:
    st.markdown(f"<div class='control-header'>CONTROL</div>", unsafe_allow_html=True)
    st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)

    st.markdown("<h3 style='color:#ffffff;'>Symbol</h3>", unsafe_allow_html=True)
    symbol = st.text_input("Symbol (eg. NIFTY23SEP17500CE)", value="NIFTY23SEP17500CE")

    st.markdown("<h3 style='color:#ffffff;'>Interval</h3>", unsafe_allow_html=True)
    interval = st.selectbox("Candle frequency", ["1m","3m","5m","15m","30m"], index=3)

    st.markdown("<h3 style='color:#ffffff;'>Emas</h3>", unsafe_allow_html=True)
    ema_short = st.number_input("EMA (short)", min_value=2, max_value=50, value=9)
    ema_long = st.number_input("EMA (long)", min_value=5, max_value=200, value=21)

    st.markdown("<h3 style='color:#ffffff;'>Show</h3>", unsafe_allow_html=True)
    show_rsi = st.checkbox("Show RSI", value=True)
    show_vwap = st.checkbox("Show VWAP", value=True)

    st.markdown("<h3 style='color:#ffffff;'>Actions</h3>", unsafe_allow_html=True)
    if st.button("Refresh Data"):
        st.experimental_rerun()

# --------------------------
# Chart + Journal
# --------------------------
left_col, right_col = st.columns([3,1], gap="small")

candles = try_get_candles().copy()
if "datetime" in candles.columns:
    candles["datetime"] = pd.to_datetime(candles["datetime"])
else:
    candles["datetime"] = pd.to_datetime(candles.index)
candles = candles.sort_values("datetime").reset_index(drop=True)

candles["EMA9"] = ema(candles["close"], ema_short)
candles["EMA21"] = ema(candles["close"], ema_long)
if "volume" not in candles.columns:
    candles["volume"] = 1
candles["VWAP"] = vwap(candles)
if show_rsi:
    candles["RSI"] = rsi(candles["close"])

rows = 2 if show_rsi else 1
fig = make_subplots(rows=rows, cols=1, shared_xaxes=True, vertical_spacing=0.06,
                    row_heights=[0.75,0.25] if show_rsi else [1.0])

fig.add_trace(go.Candlestick(
    x=candles["datetime"], open=candles["open"], high=candles["high"], low=candles["low"], close=candles["close"],
    increasing=dict(fillcolor=ACCENT_GREEN, line=dict(color=ACCENT_GREEN)),
    decreasing=dict(fillcolor=ACCENT_RED, line=dict(color=ACCENT_RED)),
    showlegend=False, name="Price", whiskerwidth=0.5
), row=1, col=1)

fig.add_trace(go.Scatter(x=candles["datetime"], y=candles["EMA9"], mode="lines", name="EMA9", line=dict(color="#1f77b4", width=1.4)), row=1, col=1)
fig.add_trace(go.Scatter(x=candles["datetime"], y=candles["EMA21"], mode="lines", name="EMA21", line=dict(color="#ff7f0e", width=1.4)), row=1, col=1)
if show_vwap:
    fig.add_trace(go.Scatter(x=candles["datetime"], y=candles["VWAP"], mode="lines", name="VWAP", line=dict(color="#9467bd", width=1.2, dash="dash")), row=1, col=1)

if show_rsi:
    fig.add_trace(go.Scatter(x=candles["datetime"], y=candles["RSI"], mode="lines", name="RSI", line=dict(color="#2ca02c", width=1.4)), row=2, col=1)
    fig.add_hline(y=70, line_dash="dash", row=2, col=1, line_color="#999999", opacity=0.6)
    fig.add_hline(y=30, line_dash="dash", row=2, col=1, line_color="#999999", opacity=0.6)

fig.update_layout(plot_bgcolor=CANVAS_BG, paper_bgcolor=CANVAS_BG, margin=dict(l=30,r=10,t=10,b=30), legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1), hovermode="x unified")
fig.update_xaxes(showgrid=False, row="all", col=1, title_text="Time (IST)", tickfont=dict(size=10))
fig.update_yaxes(showgrid=False, row="all", col=1, title_text="Price (INR)", tickfont=dict(size=10))
if show_rsi:
    fig.update_yaxes(showgrid=False, row=2, col=1, title_text="RSI", tickfont=dict(size=10))
fig.update_xaxes(showline=False)
fig.update_yaxes(showline=False)

with left_col:
    st.plotly_chart(fig, use_container_width=True, config={"modeBarButtonsToRemove":["lasso2d","select2d","zoom2d"]})

    st.markdown("<div class='journal-title'>Trading Journal</div>", unsafe_allow_html=True)

    if trades_df.empty:
        st.info("No BUY CE/PE trades found. Use the Controls on the left to query a symbol or refresh.")
    else:
        trades_display = trades_df.copy().reset_index(drop=True)
        trades_display.insert(0, "No.", trades_display.index + 1)
        cols = ["No.","Symbol","Entry Time","Entry Price","Exit Time","Exit Price","Comments","Gross PnL"]
        for c in cols:
            if c not in trades_display.columns:
                trades_display[c]=""
        trades_display = trades_display[cols]

        def fmt_price(x):
            try:
                x=float(x); return f"₹ {x:.2f}"
            except Exception:
                return x if x else ""

        trades_display["Entry Price"] = trades_display["Entry Price"].apply(fmt_price)
        trades_display["Exit Price"] = trades_display["Exit Price"].apply(fmt_price)
        trades_display["Gross PnL"] = trades_display["Gross PnL"].apply(fmt_price)

        html = "<table class='journal-table' width='100%' style='border-collapse:collapse;'>"
        html += "<thead><tr>"
        for h in cols:
            html += f"<th>{h}</th>"
        html += "</tr></thead><tbody>"
        for idx, row in trades_display.iterrows():
            html += "<tr>"
            for h in cols:
                cell = row[h] if pd.notna(row[h]) else ""
                html += f"<td style='padding:8px; vertical-align:top; border-bottom:1px solid #f1f1f1;'>{cell}</td>"
            html += "</tr>"
        html += "</tbody></table>"
        st.markdown(html, unsafe_allow_html=True)

with right_col:
    st.markdown("<div style='padding:6px; border-radius:8px; background:#ffffff; box-shadow: 0 1px 3px rgba(10,10,10,0.04);'>", unsafe_allow_html=True)
    st.markdown("<h3 style='margin:0 0 6px 0;'>Quick stats</h3>", unsafe_allow_html=True)
    st.markdown(f"<div style='font-size:14px; margin-bottom:6px;'>Open Positions: <strong>{len(trades_df)}</strong></div>", unsafe_allow_html=True)
    st.markdown(f"<div style='font-size:14px; margin-bottom:6px;'>Realized (Gross): <strong>₹ {gross_total:.2f}</strong></div>", unsafe_allow_html=True)
    st.markdown(f"<div style='font-size:14px; margin-bottom:6px;'>Win Rate: <strong>{win_rate:.1f}%</strong></div>", unsafe_allow_html=True)

st.markdown("<div style='height:24px'></div>", unsafe_allow_html=True)
