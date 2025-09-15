# trading_journal.py — FINAL single-file app (drop-in replacement)
# Features:
# - Gold UI: fixed hero, sticky PnL row, full-width journal table (zebra striped)
# - Uses local PNG logo if present (logo.png preferred)
# - Points column added to journal
# - Alerts via TELEGRAM_BOT_TOKEN & TELEGRAM_CHAT_ID env vars (per-trade + thresholds)
# - Daily target & loss banners with scrolling message
# - Defensive fallbacks for missing backends
# - No empty widget labels (labels collapsed where appropriate)
# - Safe defaults for number inputs (no min_value mismatch)
# - Tested for Python/Streamlit syntax (single-file)

import os
import base64
import glob
import math
from datetime import datetime, timedelta

import pandas as pd
import numpy as np
import streamlit as st
from plotly.subplots import make_subplots
import plotly.graph_objects as go
import requests

# -------------------------
# Page config
# -------------------------
st.set_page_config(page_title="Trading - Momentum Surge Scalping", layout="wide", initial_sidebar_state="expanded")

# -------------------------
# Constants
# -------------------------
DEEP_NAVY = "#071a2a"
ACCENT_ORANGE = "#ff7a18"
ACCENT_GREEN = "#0f8b4f"
ACCENT_RED = "#b72828"
CANVAS_BG = "#ffffff"
LOGO_HEIGHT = 96
SIDEBAR_WIDTH = 300
COMFORT_GAP = 24

# -------------------------
# Telegram env (silent if absent)
# -------------------------
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

def send_telegram_alert(message: str):
    if TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID:
        try:
            url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
            requests.post(url, data={"chat_id": TELEGRAM_CHAT_ID, "text": message})
        except Exception:
            # Don't crash UI for Telegram failures
            st.warning("Telegram alert failed (see console).")
    else:
        # intentionally silent if not configured
        pass

# -------------------------
# Demo data helpers
# -------------------------
def demo_candles():
    now = datetime.now()
    periods = 80
    base = 25000.0
    rng = pd.date_range(now - timedelta(minutes=periods * 5), periods=periods, freq="5min")
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
    try:
        return demo_trades()
    except Exception:
        # return empty schema if everything fails
        return pd.DataFrame(columns=["Symbol","Side","Entry Time","Entry Price","Exit Time","Exit Price","Comments","Gross PnL"])

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
# Session defaults (defensive)
# -------------------------
if "journal" not in st.session_state:
    st.session_state["journal"] = []
if "alerts_enabled" not in st.session_state:
    st.session_state["alerts_enabled"] = False
if "daily_target" not in st.session_state:
    st.session_state["daily_target"] = 500.0
if "daily_loss_threshold" not in st.session_state:
    st.session_state["daily_loss_threshold"] = -500.0
if "banner_shown" not in st.session_state:
    st.session_state["banner_shown"] = {"target": False, "loss": False}
if "alerted_trades" not in st.session_state:
    st.session_state["alerted_trades"] = set()

# -------------------------
# CSS / Styling
# -------------------------
css = f"""
<style>
/* hide top chrome */
header[data-testid="stHeader"], #MainMenu {{ display:none !important; }}

/* hero fixed */
.hero {{
  position: fixed !important;
  top: 16px !important;
  left: calc({SIDEBAR_WIDTH}px + {COMFORT_GAP}px) !important;
  right: {COMFORT_GAP}px !important;
  height: 96px !important;
  z-index: 1600 !important;
  border-radius:10px !important;
  box-shadow: 0 8px 22px rgba(7,18,28,0.10) !important;
  background: linear-gradient(90deg, #062033 0%, #071a2a 100%) !important;
  color:#ffffff !important;
  display:flex !important;
  align-items:center !important;
  gap:18px !important;
  padding:12px 18px !important;
  overflow:hidden !important;
}}

/* hero logo */
.hero-logo {{ flex: 0 0 {LOGO_HEIGHT}px !important; display:flex !important; align-items:center; justify-content:center; }}
.hero-logo img {{ height:72px !important; width:auto !important; max-width:100% !important; object-fit:contain !important; border-radius:8px !important; }}

/* main container aligned with hero */
.block-container, .reportview-container .main .block-container, .main .block-container {{
  margin-left: calc({SIDEBAR_WIDTH}px + {COMFORT_GAP}px) !important;
  margin-right: {COMFORT_GAP}px !important;
  padding-top: calc(16px + 96px + 12px) !important;
  max-width: calc(100% - ({SIDEBAR_WIDTH}px + {COMFORT_GAP}px * 2)) !important;
  box-sizing: border-box !important;
}}

/* freeze sidebar */
.stSidebar {{
  position: fixed !important;
  top: 0 !important;
  left: 0 !important;
  height: 100vh !important;
  overflow-y: auto !important;
  width: {SIDEBAR_WIDTH}px !important;
  z-index: 2000 !important;
  background: {DEEP_NAVY} !important;
  padding-top: 16px !important;
}}

/* sidebar inputs readable */
.stSidebar * {{ color: #ffffff !important; }}
.stSidebar input, .stSidebar select, .stSidebar textarea, .stSidebar .stButton>button, .stSidebar .stNumberInput input {{
  background: #ffffff !important;
  color: #000000 !important;
  -webkit-text-fill-color: #000000 !important;
  border-radius: 6px !important;
}}

/* number input steppers visible */
button[aria-label="Decrease value"], button[aria-label="Increase value"], .stNumberInput button {{
  background: #ffffff !important;
  color: #000000 !important;
  border: 1px solid rgba(0,0,0,0.08) !important;
  box-shadow: none !important;
}}

/* journal table full width + zebra */
.journal-table {{ width: 100% !important; border-collapse: collapse !important; table-layout: auto !important; }}
.journal-table th, .journal-table td {{ padding: 12px 14px !important; border-bottom:1px solid #f1f1f1 !important; vertical-align:top !important; }}
.journal-table tr:nth-child(even) {{ background: #eaf6ff !important; }}
.journal-table tr:nth-child(odd) {{ background: #ffffff !important; }}

/* sticky PnL row */
.block-container > div:first-child {{
  position: -webkit-sticky !important;
  position: sticky !important;
  top: calc(16px + 96px + 8px) !important;
  z-index: 1550 !important;
  background: transparent !important;
  padding-top: 6px !important;
  padding-bottom: 6px !important;
}}

/* bottom banners */
@keyframes slide-left-right {{
  0% {{ transform: translateX(-100%); }}
  100% {{ transform: translateX(100%); }}
}}
.alert-banner {{
  position: fixed;
  bottom: 12px;
  left: 0;
  right: 0;
  pointer-events: none;
  z-index: 9999;
  display:flex;
  justify-content:center;
}}
.alert-banner .msg {{
  display:inline-block;
  padding:10px 20px;
  border-radius:6px;
  font-weight:700;
  animation: slide-left-right 10s linear infinite;
  pointer-events:auto;
}}
.alert-blue {{ background:#157efb; color:#fff; }}
.alert-red  {{ background:#d93025; color:#fff; }}
</style>
"""
st.markdown(css, unsafe_allow_html=True)

# -------------------------
# Logo loader (PNG preferred)
# -------------------------
_png_candidates = ["logo.png", "header_logo.png", "logo-header.png"] + sorted(glob.glob("*.png"))
_LOGO_PATH = None
for _p in _png_candidates:
    if _p and os.path.exists(_p):
        _LOGO_PATH = _p
        break

LOGO_DATA_URI = None
if _LOGO_PATH:
    try:
        with open(_LOGO_PATH, "rb") as _f:
            _b = base64.b64encode(_f.read()).decode("ascii")
        LOGO_DATA_URI = "data:image/png;base64," + _b
    except Exception:
        LOGO_DATA_URI = None

if not LOGO_DATA_URI:
    placeholder_svg = "<svg xmlns='http://www.w3.org/2000/svg' width='96' height='96'><rect width='100%' height='100%' fill='#06303a'/></svg>"
    LOGO_DATA_URI = "data:image/svg+xml;base64," + base64.b64encode(placeholder_svg.encode("utf-8")).decode("ascii")

hero_html = (
    "<div class='hero' role='banner' aria-label='Trading hero header'>"
    "<div class='hero-logo'><img src='" + LOGO_DATA_URI + "' alt='logo' /></div>"
    "<div class='hero-title'>"
    "<div class='main' style='font-size:20px;font-weight:800;color:#ffffff;'>Trading - Momentum Surge Scalping</div>"
    "<div class='sub' style='font-size:12px;color:#cfe9ff;margin-top:6px;'>Candles • EMA9/EMA21 • VWAP • RSI • Only BUY CE/PE</div>"
    "</div>"
    "<div style='margin-left:auto;'></div>"
    "</div>"
)
st.markdown(hero_html, unsafe_allow_html=True)

# -------------------------
# Top PnL row
# -------------------------
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

gross_total = pd.to_numeric(trades_df.get("Gross PnL", 0), errors="coerce").fillna(0).sum()
win_rate = 0.0
if len(trades_df) > 0:
    wins = pd.to_numeric(trades_df.get("Gross PnL", 0), errors="coerce") > 0
    win_rate = float(wins.sum()) / max(1, len(trades_df)) * 100

with pnl_col1:
    st.markdown(f"<div style='background:white;padding:8px;border-radius:8px;'><strong>Gross PnL</strong><div style='font-size:20px;color:{ACCENT_GREEN if gross_total>=0 else ACCENT_RED};font-weight:700;'>₹ {gross_total:.2f}</div></div>", unsafe_allow_html=True)
with pnl_col2:
    st.markdown(f"<div style='background:white;padding:8px;border-radius:8px;'><strong>Total Earnings (Day)</strong><div style='font-size:20px;color:{ACCENT_ORANGE};font-weight:700;'>₹ {gross_total:.2f}</div></div>", unsafe_allow_html=True)
with pnl_col3:
    st.markdown(f"<div style='background:white;padding:8px;border-radius:8px;'><strong>Win Rate</strong><div style='font-size:20px;color:{DEEP_NAVY};font-weight:700;'>{win_rate:.1f}%</div></div>", unsafe_allow_html=True)

try:
    scale = 1000.0
    progress_val = 1.0 / (1.0 + math.exp(-gross_total / scale))
    progress_val = max(0.0, min(1.0, progress_val))
except Exception:
    progress_val = 0.12

with pnl_col4:
    st.markdown(f"<div style='padding:8px;'><div style='display:flex;justify-content:space-between;align-items:center;font-size:12px;color:#09212f;'><strong>Today's Progress</strong><span style='color:#577387'>Goal indicator: {int(progress_val*100)}%</span></div><div style='height:12px;margin-top:6px;background:#e6eef5;border-radius:8px;overflow:hidden;'><div style='width:{int(progress_val*100)}%;height:100%;background:linear-gradient(90deg,{ACCENT_GREEN} , {ACCENT_ORANGE});'></div></div></div>", unsafe_allow_html=True)

st.markdown("<hr style='margin-top:12px;margin-bottom:12px;'/>", unsafe_allow_html=True)

# -------------------------
# Sidebar controls & alerts
# -------------------------
with st.sidebar:
    st.markdown("<div style='text-align:center;color:#fff;font-weight:800;font-size:18px;padding:8px 6px;'>CONTROL</div>", unsafe_allow_html=True)
    st.markdown("<div style='height:6px'></div>", unsafe_allow_html=True)

    st.markdown("<h4 style='color:#ffffff;'>Symbol</h4>", unsafe_allow_html=True)
    symbol = st.text_input("Symbol", value="NIFTY23SEP17500CE", label_visibility="collapsed")

    st.markdown('<div style="color:#ffffff;margin-top:8px;">Candle frequency</div>', unsafe_allow_html=True)
    interval = st.selectbox("Candle frequency", ["1m", "3m", "5m", "15m", "30m"], index=3, label_visibility="collapsed")

    st.markdown("<h4 style='color:#ffffff;'>EMAs</h4>", unsafe_allow_html=True)
    ema_short = st.number_input("EMA (short)", min_value=2, max_value=50, value=9)
    ema_long = st.number_input("EMA (long)", min_value=5, max_value=200, value=21)

    st.markdown("<h4 style='color:#ffffff;'>Show</h4>", unsafe_allow_html=True)
    show_rsi = st.checkbox("Show RSI", value=True)
    show_vwap = st.checkbox("Show VWAP", value=True)

    st.markdown("<h4 style='color:#ffffff;'>Alerts</h4>", unsafe_allow_html=True)
    alerts_enabled = st.checkbox("Enable Alerts (Telegram)", value=st.session_state.get("alerts_enabled", False))

    daily_target = st.number_input("Daily Target (₹)", value=float(st.session_state.get("daily_target", 500.0)), step=100.0, format="%.2f")
    daily_loss_threshold = st.number_input("Daily Loss Threshold (₹)", value=float(st.session_state.get("daily_loss_threshold", -500.0)), step=100.0, format="%.2f")

    if st.button("Send Test Alert"):
        send_telegram_alert("AUTO_TRADING_TRACKER test alert - this is a test message from your app.")

    st.markdown('<div style="height:8px"></div>', unsafe_allow_html=True)
    if st.button("Refresh Data"):
        st.experimental_rerun()

st.session_state["alerts_enabled"] = bool(alerts_enabled)
st.session_state["daily_target"] = float(daily_target)
st.session_state["daily_loss_threshold"] = float(daily_loss_threshold)

# -------------------------
# Chart + Journal
# -------------------------
left_col, right_col = st.columns([3,1], gap="small")

candles = try_get_candles().copy()
if "datetime" in candles.columns:
    candles["datetime"] = pd.to_datetime(candles["datetime"])
else:
    candles["datetime"] = pd.to_datetime(candles.index)
candles = candles.sort_values("datetime").reset_index(drop=True)

candles["EMA9"] = ema(candles["close"], ema_short if ema_short else 9)
candles["EMA21"] = ema(candles["close"], ema_long if ema_long else 21)
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
if show_vwap:
    fig.add_trace(go.Scatter(x=candles["datetime"], y=candles["VWAP"], mode="lines", name="VWAP", line=dict(color="#9467bd", width=1.2, dash="dash")), row=1, col=1)

if show_rsi:
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
    # use 'width' param (Streamlit deprecation of use_container_width)
    st.plotly_chart(fig, width="stretch", config={"modeBarButtonsToRemove": ["lasso2d", "select2d", "zoom2d"]})

    st.markdown("<div style='font-size:18px;font-weight:700;margin-top:8px;margin-bottom:8px;'>Trading Journal</div>", unsafe_allow_html=True)
    trades_display = trades_df.copy().reset_index(drop=True)
    trades_display.insert(0, "No.", trades_display.index + 1)

    # ensure required cols (add Points)
    cols = ["No.", "Symbol", "Entry Time", "Entry Price", "Exit Time", "Exit Price", "Points", "Comments", "Gross PnL"]
    for c in cols:
        if c not in trades_display.columns:
            trades_display[c] = ""

    def calc_points(row):
        try:
            ep = float(row.get("Entry Price", 0) or 0)
            xp = float(row.get("Exit Price", 0) or 0)
            return round(xp - ep, 2)
        except Exception:
            return ""

    trades_display["Points"] = trades_display.apply(calc_points, axis=1)

    def fmt_price(x):
        try:
            x = float(x)
            return f"₹ {x:,.2f}"
        except Exception:
            return x if x else ""

    trades_display["Entry Price"] = trades_display["Entry Price"].apply(fmt_price)
    trades_display["Exit Price"] = trades_display["Exit Price"].apply(fmt_price)
    trades_display["Gross PnL"] = trades_display["Gross PnL"].apply(fmt_price)
    trades_display["Points"] = trades_display["Points"].apply(lambda v: f"{v:.2f}" if isinstance(v, (int,float)) else "")

    html = "<table class='journal-table' width='100%' style='border-collapse:collapse;'>"
    html += "<thead><tr>"
    for h in cols:
        html += f"<th style='text-align:left;padding:10px 14px;border-bottom:1px solid #e6eef5;'>{h}</th>"
    html += "</tr></thead><tbody>"
    for idx, row in trades_display.iterrows():
        html += "<tr>"
        for h in cols:
            cell = row[h] if pd.notna(row[h]) else ""
            html += f"<td style='padding:10px 14px; vertical-align:top; border-bottom:1px solid #f1f1f1;'>{cell}</td>"
        html += "</tr>"
    html += "</tbody></table>"

    st.markdown(html, unsafe_allow_html=True)

with right_col:
    st.markdown("<div style='padding:6px;border-radius:8px;background:#ffffff;box-shadow:0 1px 3px rgba(10,10,10,0.04);'>", unsafe_allow_html=True)
    st.markdown("<h3 style='margin:0 0 6px 0;'>Quick stats</h3>", unsafe_allow_html=True)
    st.markdown(f"<div style='font-size:14px;margin-bottom:6px;'>Open Positions: <strong>{len(trades_df)}</strong></div>", unsafe_allow_html=True)
    st.markdown(f"<div style='font-size:14px;margin-bottom:6px;'>Realized (Gross): <strong>₹ {gross_total:.2f}</strong></div>", unsafe_allow_html=True)
    st.markdown(f"<div style='font-size:14px;margin-bottom:6px;'>Win Rate: <strong>{win_rate:.1f}%</strong></div>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

st.markdown("<div style='height:28px'></div>", unsafe_allow_html=True)

# -------------------------
# ALERTS and BANNER logic
# -------------------------
daily_realized = pd.to_numeric(trades_df.get("Gross PnL", 0), errors="coerce").fillna(0).sum()
daily_target_val = float(st.session_state.get("daily_target", 500.0))
daily_loss_val = float(st.session_state.get("daily_loss_threshold", -500.0))

target_reached = daily_realized >= daily_target_val
loss_reached = daily_realized <= daily_loss_val

if target_reached and not st.session_state["banner_shown"].get("target", False):
    if st.session_state.get("alerts_enabled", False):
        send_telegram_alert(f"Daily target reached: ₹{daily_realized:.2f}. Congratulations!")
    st.session_state["banner_shown"]["target"] = True

if loss_reached and not st.session_state["banner_shown"].get("loss", False):
    if st.session_state.get("alerts_enabled", False):
        send_telegram_alert(f"Loss threshold reached: ₹{daily_realized:.2f}. Stop trading for the day.")
    st.session_state["banner_shown"]["loss"] = True

if target_reached:
    banner_html = "<div class='alert-banner'><div class='msg alert-blue'>Daily met. Congratulations! Enjoy the rest of the day.</div></div>"
    st.markdown(banner_html, unsafe_allow_html=True)
elif loss_reached:
    banner_html = "<div class='alert-banner'><div class='msg alert-red'>Loss threshold reached. Stop trading for the day. Analyze your strategy.</div></div>"
    st.markdown(banner_html, unsafe_allow_html=True)

# per-trade alerts (once-per-session)
for i, row in trades_df.iterrows():
    key = f"trade_alert_{i}"
    if st.session_state.get("alerts_enabled", False) and key not in st.session_state["alerted_trades"]:
        try:
            sym = row.get("Symbol", "")
            buy = row.get("Entry Price", "")
            sell = row.get("Exit Price", "")
            pnl = row.get("Gross PnL", "")
            msg = f"Trade: {sym} | Buy: {buy} | Sell: {sell} | PnL: {pnl}"
            send_telegram_alert(msg)
            st.session_state["alerted_trades"].add(key)
        except Exception:
            pass

# EOF
