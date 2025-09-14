"""
trading_journal.py
Streamlit UI patch (single-file) — "Trading - Momentum Surge Scalping"
Self-contained: embedded header image (base64 SVG). Defensive, non-destructive,
and friendly fallback data if real data sources are not present.
Author: Assistant (patch for Tirthankar)
Date: 2025-09-14
"""

import base64
import io
import math
from datetime import datetime, timedelta
import sys

import pandas as pd
import numpy as np

# Defensive imports (plotly + streamlit). If missing, show clear error message in app.
try:
    import streamlit as st
except Exception as e:
    raise RuntimeError(
        "Streamlit is required. Install with: pip install streamlit"
    ) from e

try:
    import plotly.graph_objects as go
    from plotly.subplots import make_subplots
except Exception as e:
    raise RuntimeError(
        "Plotly is required. Install with: pip install plotly"
    ) from e

# --------------------------
# Inline base64 SVG header
# --------------------------
# This SVG is a clean silhouette bull & bear with a soft candlestick background.
# It's encoded here to make the script self-contained (no external files required).
SVG = r'''
<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="220" viewBox="0 0 1200 220">
  <defs>
    <linearGradient id="bggrad" x1="0" x2="0" y1="0" y2="1">
      <stop offset="0%" stop-color="#0b2540"/>
      <stop offset="100%" stop-color="#072233"/>
    </linearGradient>
  </defs>
  <rect width="1200" height="220" rx="4" ry="4" fill="url(#bggrad)"/>
  <!-- subtle upward candles background -->
  <g transform="translate(40,12)" opacity="0.12">
    <!-- draw several green candles trending up -->
    <!-- each group: wick (thin rect) + body (thicker rect) -->
    <!-- approx positions to create an upward trend -->
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

  <!-- Bull (left) deep green silhouette -->
  <g transform="translate(200,20) scale(0.82)" fill="#0f8b4f">
    <path d="M10 160 L40 130 L80 120 L120 100 L140 90 L170 80 L210 70 L250 62 L280 60 L300 70 L320 95 L310 110 L280 130 L240 145 L200 160 L160 168 L120 170 L80 170 L40 168 Z"/>
  </g>

  <!-- Bear (right) deep red silhouette -->
  <g transform="translate(760,30) scale(0.85)" fill="#b72828">
    <path d="M10 160 L40 140 L70 130 L100 120 L140 115 L180 112 L220 115 L250 125 L270 140 L260 150 L240 160 L200 168 L160 172 L120 172 L80 170 L40 168 Z"/>
  </g>

  <!-- Title text (white) -->
  <text x="40" y="44" font-family="Helvetica, Arial, sans-serif" font-size="28" fill="#ffffff" font-weight="700">
    Trading - Momentum Surge Scalping
  </text>
  <!-- small subtitle -->
  <text x="40" y="70" font-family="Helvetica, Arial, sans-serif" font-size="12" fill="#d1e7ff">
    Real-time journal • Indicators: EMA9, EMA21, VWAP, RSI
  </text>
</svg>
'''
SVG_B64 = base64.b64encode(SVG.encode("utf-8")).decode("ascii")
HEADER_IMAGE_B64 = "data:image/svg+xml;base64," + SVG_B64

# --------------------------
# UI Constants / Colors
# --------------------------
DEEP_NAVY = "#071a2a"   # header/navy
ACCENT_ORANGE = "#ff7a18"
ACCENT_GREEN = "#0f8b4f"
ACCENT_RED = "#b72828"
WHITE = "#ffffff"
CANVAS_BG = "#ffffff"

# --------------------------
# Helper: safe data loaders
# --------------------------

def try_get_candles():
    """
    Attempt to get real candle data:
      - If the repo has a 'get_recent_candles' function defined in a backing module, call it.
      - Fallback: synthetic upward-trending mock candles (for demo).
    Returns a DataFrame with columns: datetime, open, high, low, close, volume
    """
    # Try to import a project-specific data provider (non-fatal)
    try:
        import trading_data  # hypothetical helper (won't crash app if missing)
        if hasattr(trading_data, "get_recent_candles"):
            df = trading_data.get_recent_candles()
            if isinstance(df, pd.DataFrame) and "close" in df.columns:
                return df
    except Exception:
        pass

    # Fallback: synthetic dataset for the current day (intraday minutes)
    now = datetime.now()
    periods = 60
    base = 25000.0
    rng = pd.date_range(now - timedelta(minutes=periods*5), periods=periods, freq="5T")  # 5-min candles
    np.random.seed(42)
    moves = np.random.normal(loc=0.12, scale=0.6, size=periods).cumsum()
    close = base + moves
    open_ = np.concatenate(([base], close[:-1]))
    high = np.maximum(open_, close) + np.random.rand(periods) * 5
    low = np.minimum(open_, close) - np.random.rand(periods) * 5
    volume = np.random.randint(100, 1000, size=periods)
    df = pd.DataFrame({
        "datetime": rng,
        "open": open_,
        "high": high,
        "low": low,
        "close": close,
        "volume": volume
    })
    return df

def try_get_trades():
    """
    Attempt to get real trades:
      - Try to import a function from existing codebase that returns trades
      - Fallback: synthetic trades (BUY CE/PE only).
    Returns DataFrame with columns: Symbol, Side, Entry Time, Entry Price, Exit Time, Exit Price, Comments, Gross PnL
    """
    try:
        import trading_journal_backend as tjb
        if hasattr(tjb, "get_trades"):
            trades = tjb.get_trades()
            if isinstance(trades, pd.DataFrame):
                return trades
    except Exception:
        pass

    # Fallback synthetic trades (BUY CE/PE only)
    now = datetime.now()
    trades = []
    symbols = ["NIFTY23SEP17500CE", "NIFTY23SEP17600CE", "BANKNIFTY23SEP42000CE", "NIFTY23SEP17400PE"]
    for i, sym in enumerate(symbols):
        entry_time = now - timedelta(hours=6 - i)
        exit_time = entry_time + timedelta(minutes=14 + i*5)
        entry_price = round(100 + i*12 + np.random.rand()*5, 2)
        exit_price = round(entry_price + np.random.normal(loc=20+i*5, scale=8), 2)
        gross_pnl = round((exit_price - entry_price), 2)
        trades.append({
            "Symbol": sym,
            "Side": "BUY",
            "Entry Time": entry_time.strftime("%Y-%m-%d %H:%M:%S"),
            "Entry Price": entry_price,
            "Exit Time": exit_time.strftime("%Y-%m-%d %H:%M:%S"),
            "Exit Price": exit_price,
            "Comments": "Momentum entry — rode the surge" if gross_pnl > 0 else "Reversal - exit small loss",
            "Gross PnL": gross_pnl
        })
    df = pd.DataFrame(trades)
    return df

# --------------------------
# Indicator helpers
# --------------------------
def ema(series, span):
    return series.ewm(span=span, adjust=False).mean()

def vwap(df):
    # standard VWAP for given data
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
# Streamlit UI
# --------------------------
st.set_page_config(page_title="Trading - Momentum Surge Scalping", layout="wide", initial_sidebar_state="expanded")

# Custom CSS: pin header to top, remove default padding, zebra table styles, etc.
st.markdown(
    f"""
    <style>
    /* Page canvas */
    .stApp {{
        background: {CANVAS_BG};
    }}

    /* Remove Streamlit top padding to keep header tight to top */
    .reportview-container .main .block-container {{
        padding-top: 0rem;
        padding-left: 1rem;
        padding-right: 1rem;
    }}

    /* Header styling */
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
    }}
    .main-header h1 {{
        margin: 0;
        font-size: 22px;
        line-height: 1;
    }}
    .main-header p {{
        margin: 0;
        font-size: 12px;
        color: #cfe9ff;
    }}

    /* PnL row */
    .pnl-row {{
        display:flex;
        gap: 12px;
        align-items:center;
        margin-bottom:8px;
    }}
    .pnl-card {{
        background: white;
        padding: 8px 12px;
        border-radius:8px;
        box-shadow: 0 1px 3px rgba(10,10,10,0.04);
        color: #0b2540;
    }}

    /* Left sidebar headers */
    .control-header {{
        color: {WHITE};
        background: {DEEP_NAVY};
        padding: 8px;
        font-weight:700;
        border-radius:6px;
        text-transform: uppercase;
        text-align:center;
    }}
    .control-section h3 {{
        margin: 8px 0 4px 0;
        font-weight:600;
    }}
    .control-section label {{
        font-weight: 500;
    }}

    /* Trading Journal table styles (zebra) */
    .journal-table th {{
        text-transform: capitalize;
        background: #f7fafc;
        padding:8px;
    }}
    .journal-table tr:nth-child(even) {{
        background: #fbfbfb;
    }}
    .journal-title {{
        margin-top: 8px;
        margin-bottom: 6px;
        font-size: 16px;
        font-weight: 700;
    }}
    </style>
    """, unsafe_allow_html=True
)

# Header container: image (base64) + title + subtitle
header_col1, header_col2 = st.columns([0.18, 0.82], gap="small")
with header_col1:
    st.image(HEADER_IMAGE_B64, use_column_width=True)
with header_col2:
    st.markdown(
        f"""
        <div style="display:flex; flex-direction:column; justify-content:center; height:100%;">
            <h1 style="margin:0; font-size:24px; color:{WHITE};">Trading - Momentum Surge Scalping</h1>
            <div style="height:6px"></div>
            <div style="color:#d1e7ff; font-size:12px;">Candles + EMA9/21 • VWAP • RSI • Only BUY CE/PE</div>
        </div>
        """, unsafe_allow_html=True
    )

# PnL row just below header (small gap)
st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
pnl_col1, pnl_col2, pnl_col3, pnl_col4 = st.columns([1,1,1,3])

# compute small PnL metrics from trades (or mock)
trades_df = try_get_trades()
# Ensure columns align
for c in ["Symbol","Side","Entry Time","Entry Price","Exit Time","Exit Price","Comments","Gross PnL"]:
    if c not in trades_df.columns:
        trades_df[c] = ""

# Filter to BUY CE/PE only
def is_buy_ce_pe(sym, side):
    try:
        side_ok = (str(side).strip().upper() == "BUY")
        sym_upper = str(sym).upper()
        type_ok = ("CE" in sym_upper) or ("PE" in sym_upper)
        return side_ok and type_ok
    except Exception:
        return False

trades_df = trades_df[trades_df.apply(lambda r: is_buy_ce_pe(r.get("Symbol",""), r.get("Side","")), axis=1)].reset_index(drop=True)

gross_total = trades_df["Gross PnL"].apply(pd.to_numeric, errors="coerce").fillna(0).sum()
win_rate = 0.0
if len(trades_df) > 0:
    wins = trades_df["Gross PnL"].apply(pd.to_numeric, errors="coerce") > 0
    win_rate = float(wins.sum()) / len(trades_df) * 100

# Display PnL metrics
with pnl_col1:
    st.markdown(f"<div class='pnl-card'><strong>Gross PnL</strong><div style='font-size:20px; color:{ACCENT_GREEN if gross_total>=0 else ACCENT_RED}; font-weight:700;'>₹ {gross_total:.2f}</div></div>", unsafe_allow_html=True)
with pnl_col2:
    st.markdown(f"<div class='pnl-card'><strong>Total Earnings (Day)</strong><div style='font-size:20px; color:{ACCENT_ORANGE}; font-weight:700;'>₹ {gross_total:.2f}</div></div>", unsafe_allow_html=True)
with pnl_col3:
    st.markdown(f"<div class='pnl-card'><strong>Win Rate</strong><div style='font-size:20px; color:{DEEP_NAVY}; font-weight:700;'>{win_rate:.1f}%</div></div>", unsafe_allow_html=True)

# PnL progress bar custom (reflecting day's progress, mapped to 0..1)
progress_val = max(0.0, min(1.0, (gross_total / (abs(gross_total) + 1000)) if gross_total != 0 else 0.12))
with pnl_col4:
    st.markdown("<div style='padding:8px;'></div>", unsafe_allow_html=True)
    # custom progress bar using HTML/CSS
    st.markdown(
        f"""
        <div style="background:#eef6fb; border-radius:10px; padding:6px;">
          <div style="width:100%; display:flex; justify-content:space-between; align-items:center;">
            <div style="font-size:12px; color:#09212f"><strong>Today's Progress</strong></div>
            <div style="font-size:11px; color:#577387">Goal reached: {int(progress_val*100)}%</div>
          </div>
          <div style="height:12px; margin-top:6px; background:#e6eef5; border-radius:8px; overflow:hidden;">
            <div style="width:{int(progress_val*100)}%; height:100%; background: linear-gradient(90deg, {ACCENT_GREEN}, {ACCENT_ORANGE});"></div>
          </div>
        </div>
        """, unsafe_allow_html=True
    )

st.markdown("<hr style='margin-top:12px;margin-bottom:12px;'>", unsafe_allow_html=True)

# --------------------------
# Left control panel (sidebar)
# --------------------------
with st.sidebar:
    st.markdown(f"<div class='control-header'>CONTROL</div>", unsafe_allow_html=True)
    st.markdown("<div style='height:10px'></div>", unsafe_allow_html=True)
    st.markdown("<div class='control-section'>", unsafe_allow_html=True)

    st.markdown("<h3>Symbol</h3>", unsafe_allow_html=True)
    symbol = st.text_input("Symbol (eg. NIFTY23SEP17500CE)", value="NIFTY23SEP17500CE")

    st.markdown("<h3>Interval</h3>", unsafe_allow_html=True)
    interval = st.selectbox("Candle frequency", ["1m", "3m", "5m", "15m", "30m"], index=3)

    st.markdown("<h3>EMAs</h3>", unsafe_allow_html=True)
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
# Main content: Chart + RSI + Journal
# --------------------------
left_col, right_col = st.columns([3, 1], gap="small")

# Candles: load data
candles = try_get_candles().copy()
# Ensure datetime column
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

# Build plotly figure with secondary subplot for RSI
rows = 2 if show_rsi else 1
fig = make_subplots(rows=rows, cols=1, shared_xaxes=True,
                    vertical_spacing=0.06,
                    row_heights=[0.75, 0.25] if show_rsi else [1.0])

# Candlestick trace with solid body colors
fig.add_trace(go.Candlestick(
    x=candles["datetime"],
    open=candles["open"],
    high=candles["high"],
    low=candles["low"],
    close=candles["close"],
    increasing=dict(fillcolor=ACCENT_GREEN, line=dict(color=ACCENT_GREEN)),
    decreasing=dict(fillcolor=ACCENT_RED, line=dict(color=ACCENT_RED)),
    showlegend=False,
    name="Price",
    whiskerwidth=0.5
), row=1, col=1)

# EMAs
fig.add_trace(go.Scatter(x=candles["datetime"], y=candles["EMA9"], mode="lines", name="EMA9",
                         line=dict(color="#1f77b4", width=1.6)), row=1, col=1)
fig.add_trace(go.Scatter(x=candles["datetime"], y=candles["EMA21"], mode="lines", name="EMA21",
                         line=dict(color="#ff7f0e", width=1.6)), row=1, col=1)
# VWAP
if show_vwap:
    fig.add_trace(go.Scatter(x=candles["datetime"], y=candles["VWAP"], mode="lines", name="VWAP",
                             line=dict(color="#9467bd", width=1.2, dash="dash")), row=1, col=1)

# RSI subplot
if show_rsi:
    fig.add_trace(go.Scatter(x=candles["datetime"], y=candles["RSI"], mode="lines", name="RSI",
                             line=dict(color="#2ca02c", width=1.4)), row=2, col=1)
    # horizontal lines 30 / 70
    fig.add_hline(y=70, line_dash="dash", row=2, col=1, line_color="#999999", opacity=0.6)
    fig.add_hline(y=30, line_dash="dash", row=2, col=1, line_color="#999999", opacity=0.6)

# Layout polishing: white canvas, no grid, axis labels
fig.update_layout(
    plot_bgcolor=CANVAS_BG,
    paper_bgcolor=CANVAS_BG,
    margin=dict(l=30, r=10, t=10, b=30),
    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    hovermode="x unified",
    modebar_remove=['lasso2d','select2d']
)

# Remove gridlines on primary chart
fig.update_xaxes(showgrid=False, row=1, col=1, title_text="Time (IST)", tickfont=dict(size=10))
fig.update_yaxes(showgrid=False, row=1, col=1, title_text="Price (INR)", tickfont=dict(size=10))

if show_rsi:
    fig.update_xaxes(showgrid=False, row=2, col=1, title_text="Time (IST)", tickfont=dict(size=10))
    fig.update_yaxes(showgrid=False, row=2, col=1, title_text="RSI", tickfont=dict(size=10))

# No axis lines extra clutter
fig.update_xaxes(showline=False)
fig.update_yaxes(showline=False)

# Show chart in left column
with left_col:
    st.plotly_chart(fig, use_container_width=True)

    # Title for table
    st.markdown("<div class='journal-title'>Trading Journal</div>", unsafe_allow_html=True)

    # Show journal as zebra-striped HTML fallback (better control)
    if len(trades_df) == 0:
        st.info("No trades found for the current filter (only BUY CE/PE shown).")
    else:
        # Normalize headers: initial caps, no underscores
        trades_display = trades_df.copy()
        # Ensure column order and names
        columns = ["Symbol", "Entry Time", "Entry Price", "Exit Time", "Exit Price", "Comments", "Gross PnL"]
        for c in columns:
            if c not in trades_display.columns:
                trades_display[c] = ""

        trades_display = trades_display[columns]

        # Format numeric
        trades_display["Entry Price"] = pd.to_numeric(trades_display["Entry Price"], errors="coerce").map(lambda x: f"₹ {x:.2f}" if not pd.isna(x) else "")
        trades_display["Exit Price"] = pd.to_numeric(trades_display["Exit Price"], errors="coerce").map(lambda x: f"₹ {x:.2f}" if not pd.isna(x) else "")
        trades_display["Gross PnL"] = pd.to_numeric(trades_display["Gross PnL"], errors="coerce").map(lambda x: f"₹ {x:.2f}" if not pd.isna(x) else "")

        # Render as HTML table for zebra stripes
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
                html += f"<td style='padding:8px; vertical-align:top;'>{cell}</td>"
            html += "</tr>"
        html += "</tbody></table>"
        st.markdown(html, unsafe_allow_html=True)

# Right column: quick stats / holdings
with right_col:
    st.markdown("<div style='padding:6px; border-radius:8px; background:#ffffff; box-shadow: 0 1px 3px rgba(10,10,10,0.04);'>", unsafe_allow_html=True)
    st.markdown("<h3 style='margin:0 0 6px 0;'>Quick stats</h3>", unsafe_allow_html=True)
    st.markdown(f"<div style='font-size:14px; margin-bottom:6px;'>Open Positions: <strong>{len(trades_df)}</strong></div>", unsafe_allow_html=True)
    st.markdown(f"<div style='font-size:14px; margin-bottom:6px;'>Realized (Gross): <strong>₹ {gross_total:.2f}</strong></div>", unsafe_allow_html=True)
    st.markdown(f"<div style='font-size:14px; margin-bottom:6px;'>Win Rate: <strong>{win_rate:.1f}%</strong></div>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

# Footer spacing
st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)

# --------------------------
# End of UI
# --------------------------
