"""
trading_journal.py  (REPLACEMENT)
- Fixed: removed deprecated use_column_width usage (uses use_container_width)
- Fixed: header pinned to top (no undesired gap) and safe layout
- Fixed: removed leftover gridlines, tightened chart styling
- New: Adds a "No." column (1-based index) to Trading Journal
- Defensive: falls back to mock data if project-specific providers are absent
- Self-contained: embedded header SVG as base64
Author: Assistant (patched for Tirthankar)
Date: 2025-09-14 (updated)
"""

import base64
from datetime import datetime, timedelta
import math
import sys

import pandas as pd
import numpy as np

# Defensive imports
try:
    import streamlit as st
except Exception as e:
    raise RuntimeError("Streamlit is required. Install with: pip install streamlit") from e

try:
    import plotly.graph_objects as go
    from plotly.subplots import make_subplots
except Exception as e:
    raise RuntimeError("Plotly is required. Install with: pip install plotly") from e

# --------------------------
# Embedded header SVG (base64) - self contained
# --------------------------
SVG = r'''
<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="220" viewBox="0 0 1200 220">
  <defs>
    <linearGradient id="bggrad" x1="0" x2="0" y1="0" y2="1">
      <stop offset="0%" stop-color="#0b2540"/>
      <stop offset="100%" stop-color="#072233"/>
    </linearGradient>
  </defs>
  <rect width="1200" height="220" rx="4" ry="4" fill="url(#bggrad)"/>
  <g transform="translate(40,12)" opacity="0.12">
    <g fill="#46c78a">
      <rect x="0" y="140" width="10" height="60" rx="1"/>
      <rect x="20" y="128" width="10" height="72" rx="1"/>
      <rect x="40" y="112" width="10" height="88" rx="1"/>
      <rect x="60" y="96" width="10" height="104" rx="1"/>
      <rect x="80" y="92" width="10" height="108" rx="1"/>
      <rect x="100" y="82" width="10" height="118" rx="1"/>
      <rect x="120" y="72" width="10" height="128" rx="1"/>
      <rect x="140" y="66" width="10" height="134" rx="1"/>
      <rect x="160" y="54" width="10" height="146" rx="1"/>
      <rect x="180" y="44" width="10" height="156" rx="1"/>
    </g>
  </g>
  <g transform="translate(200,20) scale(0.82)" fill="#0f8b4f">
    <path d="M10 160 L40 130 L80 120 L120 100 L140 90 L170 80 L210 70 L250 62 L280 60 L300 70 L320 95 L310 110 L280 130 L240 145 L200 160 L160 168 L120 170 L80 170 L40 168 Z"/>
  </g>
  <g transform="translate(760,30) scale(0.85)" fill="#b72828">
    <path d="M10 160 L40 140 L70 130 L100 120 L140 115 L180 112 L220 115 L250 125 L270 140 L260 150 L240 160 L200 168 L160 172 L120 172 L80 170 L40 168 Z"/>
  </g>
  <text x="40" y="44" font-family="Helvetica, Arial, sans-serif" font-size="28" fill="#ffffff" font-weight="700">
    Trading - Momentum Surge Scalping
  </text>
  <text x="40" y="70" font-family="Helvetica, Arial, sans-serif" font-size="12" fill="#d1e7ff">
    Real-time journal • Indicators: EMA9, EMA21, VWAP, RSI
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
# Data provider fallbacks
# --------------------------
def try_get_candles():
    """
    Tries to import project-specific provider for candles; otherwise provides mock upward trend candles.
    Returns: DataFrame with datetime, open, high, low, close, volume
    """
    # try project-specific provider (non-fatal)
    try:
        import trading_data  # optional module
        if hasattr(trading_data, "get_recent_candles"):
            df = trading_data.get_recent_candles()
            if isinstance(df, pd.DataFrame) and "close" in df.columns:
                return df
    except Exception:
        pass

    # fallback synthetic candles (5-minute candles for demo)
    now = datetime.now()
    periods = 60
    base = 25000.0
    rng = pd.date_range(now - timedelta(minutes=periods*5), periods=periods, freq="5T")
    np.random.seed(42)
    moves = np.random.normal(loc=0.12, scale=0.6, size=periods).cumsum()
    close = base + moves
    open_ = np.concatenate(([base], close[:-1]))
    high = np.maximum(open_, close) + np.random.rand(periods) * 5
    low = np.minimum(open_, close) - np.random.rand(periods) * 5
    volume = np.random.randint(100, 1000, size=periods)
    df = pd.DataFrame({"datetime": rng, "open": open_, "high": high, "low": low, "close": close, "volume": volume})
    return df

def try_get_trades():
    """
    Tries to import project-specific trades; otherwise returns mock BUY CE/PE trades.
    Returns a DataFrame with Symbol, Side, Entry Time, Entry Price, Exit Time, Exit Price, Comments, Gross PnL
    """
    try:
        import trading_journal_backend as tjb
        if hasattr(tjb, "get_trades"):
            trades = tjb.get_trades()
            if isinstance(trades, pd.DataFrame):
                return trades
    except Exception:
        pass

    now = datetime.now()
    symbols = ["NIFTY23SEP17500CE", "NIFTY23SEP17600CE", "BANKNIFTY23SEP42000CE", "NIFTY23SEP17400PE"]
    rows = []
    for i, sym in enumerate(symbols):
        entry = now - timedelta(hours=6 - i)
        exit = entry + timedelta(minutes=12 + i*6)
        ep = round(100 + i*10 + np.random.rand()*5, 2)
        xp = round(ep + np.random.normal(loc=20+i*3, scale=6), 2)
        pnl = round((xp - ep), 2)
        rows.append({
            "Symbol": sym,
            "Side": "BUY",
            "Entry Time": entry.strftime("%Y-%m-%d %H:%M:%S"),
            "Entry Price": ep,
            "Exit Time": exit.strftime("%Y-%m-%d %H:%M:%S"),
            "Exit Price": xp,
            "Comments": "Momentum entry — rode the surge" if pnl > 0 else "Reversal - small loss",
            "Gross PnL": pnl
        })
    return pd.DataFrame(rows)

# --------------------------
# Indicator helpers
# --------------------------
def ema(series, span):
    return series.ewm(span=span, adjust=False).mean()

def vwap(df):
    tp = (df["high"] + df["low"] + df["close"]) / 3.0
    cw = tp * df["volume"]
    return cw.cumsum() / df["volume"].cumsum()

def rsi(series, period=14):
    delta = series.diff()
    up = delta.clip(lower=0)
    down = -1 * delta.clip(upper=0)
    ma_up = up.ewm(alpha=1/period, min_periods=period).mean()
    ma_down = down.ewm(alpha=1/period, min_periods=period).mean()
    rs = ma_up / ma_down
    return 100 - (100 / (1 + rs))

# --------------------------
# Streamlit page config and CSS
# --------------------------
st.set_page_config(page_title="Trading - Momentum Surge Scalping", layout="wide", initial_sidebar_state="expanded")

st.markdown(
    f"""
    <style>
    /* White canvas */
    .stApp {{ background: {CANVAS_BG}; }}

    /* Tighten main container so header is flush with top */
    .reportview-container .main .block-container {{
        padding-top: 0rem;
        padding-left: 1rem;
        padding-right: 1rem;
    }}

    /* Main header - sticky to top, no gap */
    .main-header {{
        background: linear-gradient(90deg, {DEEP_NAVY} 0%, #062033 100%);
        color: {WHITE};
        padding: 10px 18px;
        border-radius: 6px;
        margin-top: 0px;
        margin-bottom: 8px;
        display: flex;
        align-items: center;
        gap: 16px;
        position: sticky;
        top: 0;
        z-index: 9999;
    }}
    .main-header h1 {{ margin: 0; font-size: 22px; line-height: 1; }}
    .main-header p {{ margin: 0; font-size: 12px; color: #cfe9ff; }}

    /* Ensure header image does not overflow */
    .main-header img {{ max-height: 64px; border-radius:6px; }}

    /* PnL cards */
    .pnl-row {{ display:flex; gap:12px; align-items:center; margin-bottom:8px; }}
    .pnl-card {{
        background: white;
        padding: 8px 12px;
        border-radius:8px;
        box-shadow: 0 1px 3px rgba(10,10,10,0.04);
        color: #0b2540;
    }}

    /* Sidebar control header stronger */
    .control-header {{
        color: {WHITE};
        background: {DEEP_NAVY};
        padding: 10px;
        font-weight:700;
        border-radius:6px;
        text-transform: uppercase;
        text-align:center;
        display:flex;
        justify-content:center;
        align-items:center;
        font-size:14px;
        letter-spacing:0.6px;
    }}
    .control-section h3 {{
        margin: 8px 0 4px 0;
        font-weight:600;
        text-transform: none;
    }}

    /* Journal table zebra stripes & header */
    .journal-table th {{
        text-transform: capitalize;
        background: #f7fafc;
        padding:8px;
        text-align:left;
        font-weight:600;
    }}
    .journal-table tr:nth-child(even) {{ background: #fbfbfb; }}
    .journal-title {{ margin-top:8px; margin-bottom:6px; font-size:16px; font-weight:700; }}

    /* small axis label style for plotly tooltip formatting */
    .plotly-subplot .xtitle, .plotly-subplot .ytitle {{ font-size:10px; }}
    </style>
    """, unsafe_allow_html=True
)

# --------------------------
# Header (image + text)
# --------------------------
header_col1, header_col2 = st.columns([0.18, 0.82], gap="small")
with header_col1:
    # use_container_width to avoid deprecation warning
    st.image(HEADER_IMAGE_B64, use_container_width=True)
with header_col2:
    st.markdown(
        f"""
        <div class="main-header" role="banner">
            <div>
                <h1 style="color:{WHITE}; margin:0;">Trading - Momentum Surge Scalping</h1>
                <p style="margin:2px 0 0 0; color:#d1e7ff;">Candles • EMA9/EMA21 • VWAP • RSI • Only BUY CE/PE</p>
            </div>
        </div>
        """, unsafe_allow_html=True
    )

# small spacer
st.markdown("<div style='height:6px'></div>", unsafe_allow_html=True)

# --------------------------
# PnL row immediately under header
# --------------------------
pnl_col1, pnl_col2, pnl_col3, pnl_col4 = st.columns([1,1,1,3])

trades_df = try_get_trades()

# Ensure required columns exist
for c in ["Symbol","Side","Entry Time","Entry Price","Exit Time","Exit Price","Comments","Gross PnL"]:
    if c not in trades_df.columns:
        trades_df[c] = ""

# Filter BUY CE/PE only
def is_buy_ce_pe(sym, side):
    try:
        side_ok = str(side).strip().upper() == "BUY"
        sym_up = str(sym).upper()
        return side_ok and (("CE" in sym_up) or ("PE" in sym_up))
    except Exception:
        return False

trades_df = trades_df[trades_df.apply(lambda r: is_buy_ce_pe(r.get("Symbol",""), r.get("Side","")), axis=1)].reset_index(drop=True)

# Compute metrics
gross_total = pd.to_numeric(trades_df.get("Gross PnL", 0), errors="coerce").fillna(0).sum()
win_rate = 0.0
if len(trades_df) > 0:
    wins = pd.to_numeric(trades_df.get("Gross PnL", 0), errors="coerce") > 0
    win_rate = float(wins.sum()) / max(1, len(trades_df)) * 100

# Show PnL cards
with pnl_col1:
    st.markdown(f"<div class='pnl-card'><strong>Gross PnL</strong><div style='font-size:20px; color:{ACCENT_GREEN if gross_total>=0 else ACCENT_RED}; font-weight:700;'>₹ {gross_total:.2f}</div></div>", unsafe_allow_html=True)
with pnl_col2:
    st.markdown(f"<div class='pnl-card'><strong>Total Earnings (Day)</strong><div style='font-size:20px; color:{ACCENT_ORANGE}; font-weight:700;'>₹ {gross_total:.2f}</div></div>", unsafe_allow_html=True)
with pnl_col3:
    st.markdown(f"<div class='pnl-card'><strong>Win Rate</strong><div style='font-size:20px; color:{DEEP_NAVY}; font-weight:700;'>{win_rate:.1f}%</div></div>", unsafe_allow_html=True)

# Progress bar - scaled safely
# Map gross_total to 0..1 range for visualization; clamp to [0,1]
# Use a soft scaling to avoid immediate 100% on small pnl values
progress_val = 0.0
try:
    scale = 1000.0  # small scale, tuneable
    progress_val = 1.0 / (1.0 + math.exp(-gross_total/scale))  # logistic mapping
    progress_val = max(0.0, min(1.0, progress_val))
except Exception:
    progress_val = 0.12

with pnl_col4:
    st.markdown(
        f"""
        <div style="padding:8px;">
          <div style="display:flex; justify-content:space-between; align-items:center; font-size:12px; color:#09212f;">
            <strong>Today's Progress</strong><span style="color:#577387">Goal indicator: {int(progress_val*100)}%</span>
          </div>
          <div style="height:12px; margin-top:6px; background:#e6eef5; border-radius:8px; overflow:hidden;">
            <div style="width:{int(progress_val*100)}%; height:100%; background: linear-gradient(90deg, {ACCENT_GREEN}, {ACCENT_ORANGE});"></div>
          </div>
        </div>
        """, unsafe_allow_html=True
    )

st.markdown("<hr style='margin-top:12px; margin-bottom:12px;'>", unsafe_allow_html=True)

# --------------------------
# Left sidebar: controls
# --------------------------
with st.sidebar:
    st.markdown(f"<div class='control-header'>CONTROL</div>", unsafe_allow_html=True)
    st.markdown("<div style='height:10px'></div>", unsafe_allow_html=True)
    st.markdown("<div class='control-section'>", unsafe_allow_html=True)

    st.markdown("<h3>Symbol</h3>", unsafe_allow_html=True)
    symbol = st.text_input("Symbol (eg. NIFTY23SEP17500CE)", value="NIFTY23SEP17500CE")

    st.markdown("<h3>Interval</h3>", unsafe_allow_html=True)
    interval = st.selectbox("Candle frequency", ["1m","3m","5m","15m","30m"], index=3)

    st.markdown("<h3>Emas</h3>", unsafe_allow_html=True)
    ema_short = st.number_input("EMA (short)", min_value=2, max_value=50, value=9)
    ema_long = st.number_input("EMA (long)", min_value=5, max_value=200, value=21)

    st.markdown("<h3>Show</h3>", unsafe_allow_html=True)
    show_rsi = st.checkbox("Show RSI", value=True)
    show_vwap = st.checkbox("Show VWAP", value=True)

    st.markdown("<h3>Actions</h3>", unsafe_allow_html=True)
    if st.button("Refresh Data"):
        st.experimental_rerun()
    st.markdown("</div>", unsafe_allow_html=True)

# --------------------------
# Main layout: Chart + Journal
# --------------------------
left_col, right_col = st.columns([3, 1], gap="small")

# Load candles and compute indicators
candles = try_get_candles().copy()
if "datetime" in candles.columns:
    candles["datetime"] = pd.to_datetime(candles["datetime"])
else:
    candles["datetime"] = pd.to_datetime(candles.index)
candles = candles.sort_values("datetime").reset_index(drop=True)

# Indicators
candles["EMA9"] = ema(candles["close"], ema_short)
candles["EMA21"] = ema(candles["close"], ema_long)
if "volume" not in candles.columns:
    candles["volume"] = 1
candles["VWAP"] = vwap(candles)
if show_rsi:
    candles["RSI"] = rsi(candles["close"])

# Plotly figure: candlesticks + indicators + optional RSI subplot
rows = 2 if show_rsi else 1
fig = make_subplots(rows=rows, cols=1, shared_xaxes=True, vertical_spacing=0.06,
                    row_heights=[0.75, 0.25] if show_rsi else [1.0])

# Candlesticks: solid fill, green up, red down
fig.add_trace(go.Candlestick(
    x=candles["datetime"], open=candles["open"], high=candles["high"], low=candles["low"], close=candles["close"],
    increasing=dict(fillcolor=ACCENT_GREEN, line=dict(color=ACCENT_GREEN)),
    decreasing=dict(fillcolor=ACCENT_RED, line=dict(color=ACCENT_RED)),
    showlegend=False, name="Price", whiskerwidth=0.5
), row=1, col=1)

# EMA lines
fig.add_trace(go.Scatter(x=candles["datetime"], y=candles["EMA9"], mode="lines", name="EMA9",
                         line=dict(color="#1f77b4", width=1.6)), row=1, col=1)
fig.add_trace(go.Scatter(x=candles["datetime"], y=candles["EMA21"], mode="lines", name="EMA21",
                         line=dict(color="#ff7f0e", width=1.6)), row=1, col=1)

# VWAP dashed
if show_vwap:
    fig.add_trace(go.Scatter(x=candles["datetime"], y=candles["VWAP"], mode="lines", name="VWAP",
                             line=dict(color="#9467bd", width=1.2, dash="dash")), row=1, col=1)

# RSI subplot
if show_rsi:
    fig.add_trace(go.Scatter(x=candles["datetime"], y=candles["RSI"], mode="lines", name="RSI",
                             line=dict(color="#2ca02c", width=1.4)), row=2, col=1)
    # Add 30/70 lines for RSI in subplot
    fig.add_hline(y=70, line_dash="dash", row=2, col=1, line_color="#999999", opacity=0.6)
    fig.add_hline(y=30, line_dash="dash", row=2, col=1, line_color="#999999", opacity=0.6)

# Layout styling: white canvas, no gridlines
fig.update_layout(
    plot_bgcolor=CANVAS_BG,
    paper_bgcolor=CANVAS_BG,
    margin=dict(l=30, r=10, t=10, b=30),
    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    hovermode="x unified"
)

# remove all grid lines on both axes for both rows
fig.update_xaxes(showgrid=False, row="all", col=1, title_text="Time (IST)", tickfont=dict(size=10))
fig.update_yaxes(showgrid=False, row="all", col=1, title_text="Price (INR)", tickfont=dict(size=10))
if show_rsi:
    fig.update_yaxes(showgrid=False, row=2, col=1, title_text="RSI", tickfont=dict(size=10))

# remove axis lines clutter
fig.update_xaxes(showline=False)
fig.update_yaxes(showline=False)

# Show chart in left column - remove interactive selection buttons for clarity
with left_col:
    st.plotly_chart(fig, use_container_width=True, config={'modeBarButtonsToRemove': ['lasso2d','select2d','zoom2d']})

    # Trading Journal title & table
    st.markdown("<div class='journal-title'>Trading Journal</div>", unsafe_allow_html=True)

    # If no trades, show a friendly message
    if trades_df.empty:
        st.info("No BUY CE/PE trades found. Use the Controls on the left to query a symbol or refresh.")
    else:
        # Build display table with "No." column
        trades_display = trades_df.copy()
        trades_display = trades_display.reset_index(drop=True)
        trades_display.insert(0, "No.", trades_display.index + 1)

        # Ensure desired order and present headers (Initial Caps)
        columns = ["No.", "Symbol", "Entry Time", "Entry Price", "Exit Time", "Exit Price", "Comments", "Gross PnL"]
        for c in columns:
            if c not in trades_display.columns:
                trades_display[c] = ""

        trades_display = trades_display[columns]

        # Format numbers (rupee sign) safely
        def fmt_price(x):
            try:
                x = float(x)
                return f"₹ {x:.2f}"
            except Exception:
                return x if x else ""

        trades_display["Entry Price"] = trades_display["Entry Price"].apply(fmt_price)
        trades_display["Exit Price"] = trades_display["Exit Price"].apply(fmt_price)
        trades_display["Gross PnL"] = trades_display["Gross PnL"].apply(fmt_price)

        # Render HTML table with zebra stripes for full control (keeps styling consistent)
        html = "<table class='journal-table' width='100%' style='border-collapse:collapse;'>"
        # header
        html += "<thead><tr>"
        for h in columns:
            html += f"<th>{h}</th>"
        html += "</tr></thead><tbody>"
        for idx, row in trades_display.iterrows():
            html += "<tr>"
            for h in columns:
                cell = row[h] if pd.notna(row[h]) else ""
                html += f"<td style='padding:8px; vertical-align:top; border-bottom:1px solid #f1f1f1;'>{cell}</td>"
            html += "</tr>"
        html += "</tbody></table>"
        st.markdown(html, unsafe_allow_html=True)

# Right column: quick stats
with right_col:
    st.markdown("<div style='padding:6px; border-radius:8px; background:#ffffff; box-shadow: 0 1px 3px rgba(10,10,10,0.04);'>", unsafe_allow_html=True)
    st.markdown("<h3 style='margin:0 0 6px 0;'>Quick stats</h3>", unsafe_allow_html=True)
    st.markdown(f"<div style='font-size:14px; margin-bottom:6px;'>Open Positions: <strong>{len(trades_df)}</strong></div>", unsafe_allow_html=True)
    st.markdown(f"<div style='font-size:14px; margin-bottom:6px;'>Realized (Gross): <strong>₹ {gross_total:.2f}</strong></div>", unsafe_allow_html=True)
    st.markdown(f"<div style='font-size:14px; margin-bottom:6px;'>Win Rate: <strong>{win_rate:.1f}%</strong></div>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

# final spacer
st.markdown("<div style='height:14px'></div>", unsafe_allow_html=True)
