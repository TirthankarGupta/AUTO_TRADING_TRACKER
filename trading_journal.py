# trading_journal.py — consolidated, tz-safe, mock-candles + EMA indicators, styled header + side panel
"""
Trading Journal — consolidated baseline (mock candles + indicators)

Run:
    streamlit run trading_journal.py
"""
import os, io
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
import streamlit as st
import pytz
import plotly.graph_objects as go

# Page config
st.set_page_config(page_title="Trading Journal", layout="wide", initial_sidebar_state="expanded")

# --- Styling patch (in-line fallback if external CSS missing) ---
def _inject_basic_style():
    css = """
    /* flush header and main, deep navy header, left navy sidebar */
    body { margin:0; padding:0; background:#ffffff; }
    .stApp { padding-top:0px !important; }
    .header-block { background:#0b1d3a; color:#ffffff; padding:10px 18px; border-radius:6px; }
    .at-badge { background:#f6a623; color:#0b1d3a; font-weight:700; padding:6px 8px; border-radius:6px; display:inline-block; margin-right:12px; }
    /* left sidebar background override */
    section[data-testid="stSidebar"] { background:#0b1d3a; color:#ffffff; }
    section[data-testid="stSidebar"] .css-1d391kg { color:#ffffff; } /* label fallback */
    /* progress bar */
    .pn-progress { height:12px; background:#e9f6ee; border-radius:8px; display:block; margin-top:6px; }
    .pn-progress > .bar { height:12px; background: #2ca02c; width:0%; border-radius:8px; }
    /* PnL badge */
    .pnl-badge { background:#f6a623; color:#0b1730; padding:8px 12px; border-radius:8px; box-shadow: 0 2px 6px rgba(0,0,0,0.12); display:inline-block; margin-bottom:6px; font-weight:600; }
    /* make table header cleaner */
    table { border-collapse: collapse; }
    .no-grid .plotly .cartesianlayer .gridlayer { display:none !important; } /* hide plotly grid fallback */
    """
    st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)

# Try external CSS first if exists, else inject fallback
if os.path.exists("journal_style.css"):
    try:
        with open("journal_style.css", "r", encoding="utf-8") as __f:
            st.markdown(f"<style>{__f.read()}</style>", unsafe_allow_html=True)
    except Exception:
        _inject_basic_style()
else:
    _inject_basic_style()

KOLKATA = pytz.timezone("Asia/Kolkata")

# ------------------------
# Helpers
# ------------------------
def parse_datetime(val):
    """Return tz-aware pandas.Timestamp in Kolkata timezone or NaT."""
    if pd.isna(val) or (isinstance(val, str) and val.strip() == ""):
        return pd.NaT
    try:
        ts = pd.to_datetime(val, errors="coerce")
        if pd.isna(ts):
            return pd.NaT
        # if naive, localize to IST
        if ts.tzinfo is None:
            try:
                return ts.tz_localize(KOLKATA)
            except Exception:
                try:
                    return KOLKATA.localize(ts.to_pydatetime())
                except Exception:
                    return pd.NaT
        else:
            try:
                return ts.tz_convert(KOLKATA)
            except Exception:
                return ts
    except Exception:
        return pd.NaT

def ensure_columns(df):
    required = ["trade_id","symbol","quantity","lot_size","entry_price","exit_price","entry_time","exit_time","fees","notes","open","high","low","close"]
    for c in required:
        if c not in df.columns:
            df[c] = np.nan
    return df

def compute_pnl_units(row, default_lot_size):
    try:
        lots = float(row.get("quantity", 0.0))
        lot_size = float(row.get("lot_size", default_lot_size)) if not pd.isna(row.get("lot_size", np.nan)) else float(default_lot_size)
        units = lots * lot_size
        ep = float(row.get("entry_price", np.nan))
        xp = float(row.get("exit_price", np.nan))
        fees = float(row.get("fees", 0.0)) if not pd.isna(row.get("fees", np.nan)) else 0.0
        if np.isnan(ep) or np.isnan(xp) or units == 0:
            return np.nan
        return (xp - ep) * units - fees
    except Exception:
        return np.nan

# Indicators
def ema(series: pd.Series, span: int):
    return series.ewm(span=span, adjust=False).mean()

def rsi(series: pd.Series, length: int = 14):
    delta = series.diff()
    up = delta.clip(lower=0).fillna(0)
    down = -1 * delta.clip(upper=0).fillna(0)
    ma_up = up.ewm(span=length, adjust=False).mean()
    ma_down = down.ewm(span=length, adjust=False).mean()
    rs = ma_up / (ma_down.replace(0, np.nan))
    rsi = 100 - (100 / (1 + rs))
    return rsi.fillna(50)

# ------------------------
# Sample OHLC generator (mock data)
# ------------------------
def make_mock_ohlc(start_dt=None, periods=28, freq_minutes=15, start_price=25000):
    if start_dt is None:
        start_dt = datetime.now().replace(hour=9, minute=15, second=0, microsecond=0)
    times = [start_dt + pd.Timedelta(minutes=freq_minutes*i) for i in range(periods)]
    # small random walk
    rng = np.random.default_rng(42)
    closes = np.round(start_price + np.cumsum(rng.normal(0, 7, size=periods)), 2)
    opens = np.concatenate([[start_price], closes[:-1]])
    highs = np.maximum(opens, closes) + np.abs(rng.normal(1.5, 1.0, size=periods))
    lows = np.minimum(opens, closes) - np.abs(rng.normal(1.5, 1.0, size=periods))
    df = pd.DataFrame({
        "time": pd.to_datetime(times),
        "open": np.round(opens,2),
        "high": np.round(highs,2),
        "low": np.round(lows,2),
        "close": np.round(closes,2)
    })
    df["time"] = df["time"].dt.tz_localize(KOLKATA)
    return df

# ------------------------
# Streamlit UI (sidebar)
# ------------------------
with st.sidebar:
    st.markdown("### Controls", unsafe_allow_html=True)
    initial_balance = st.number_input("Initial starting balance (₹)", value=100000.0, step=1000.0, format="%.2f")
    default_fees = st.number_input("Default per-trade fees (₹) if missing", value=0.0, step=1.0, format="%.2f")
    global_lot_size = st.number_input("Default lot size (units per lot)", value=75, step=1)
    show_candles = st.checkbox("Show candles (mock OHLC)", value=True)
    st.markdown("---")
    st.markdown("**Force Signal (testing)**")
    force_mode = st.radio("", options=["Auto","BUY_CE","BUY_PE"], index=0)
    st.markdown("---")
    max_trades_day = st.number_input("Discipline: Max trades/day", value=10, step=1)
    profit_target = st.number_input("Daily profit target (₹)", value=5000.0, step=100.0)
    stop_loss = st.number_input("Daily stop-loss (₹)", value=-5000.0, step=100.0)
    st.markdown("<div style='height:18px'></div>", unsafe_allow_html=True)
    if st.button("Force day-end export"):
        # simple export
        try:
            os.makedirs("exports", exist_ok=True)
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            out = os.path.join("exports", f"dayend_export_{ts}.csv")
            # attempt to export trades.csv if exists else nothing
            if os.path.exists("trades.csv"):
                df2 = pd.read_csv("trades.csv")
                df2.to_csv(out, index=False)
                st.success(f"Exported {out}")
            else:
                st.info("No trades.csv to export.")
        except Exception as e:
            st.error(f"Export failed: {e}")

# ------------------------
# Load trades.csv (auto) or sample
# ------------------------
df_raw = None
if os.path.exists("trades.csv"):
    try:
        df_raw = pd.read_csv("trades.csv")
        st.success(f"Loaded {len(df_raw)} rows from trades.csv")
    except Exception as e:
        st.error(f"Failed to read trades.csv: {e}")
        df_raw = None

uploaded = st.file_uploader("Upload trades CSV (optional)", type=["csv","txt"], accept_multiple_files=False)
use_sample = st.checkbox("Use sample dataset if no upload", value=False)

if df_raw is None and uploaded:
    try:
        df_raw = pd.read_csv(uploaded)
        st.success(f"Loaded {len(df_raw)} rows from uploaded CSV.")
    except Exception as e:
        st.error(f"Failed to read uploaded CSV: {e}")
        df_raw = None

if df_raw is None:
    if use_sample or df_raw is None:
        # create small trades sample (not OHLC)
        df_raw = pd.DataFrame([
            {"trade_id":"1","symbol":"NIFTY24SEP24700CE","quantity":1,"lot_size":75,"entry_price":20,"exit_price":45,"entry_time":"2025-09-01 09:17:00","exit_time":"2025-09-01 09:43:00","fees":15,"notes":"Breakout"},
            {"trade_id":"2","symbol":"NIFTY24SEP24800CE","quantity":2,"lot_size":75,"entry_price":12,"exit_price":7,"entry_time":"2025-09-01 10:05:00","exit_time":"2025-09-01 10:45:00","fees":10,"notes":"Volatile"},
        ])
        st.info("Using sample dataset. Upload your CSV to use real trades.")

if df_raw is None or df_raw.empty:
    st.warning("No trades loaded. Please upload trades.csv or use sample.")
    st.stop()

# Normalize headers
df = df_raw.copy()
df.columns = [str(c).strip().lower() for c in df.columns]
df = ensure_columns(df)

# numeric coercion
df["quantity"] = pd.to_numeric(df.get("quantity", np.nan), errors="coerce").fillna(0)
df["lot_size"] = pd.to_numeric(df.get("lot_size", np.nan), errors="coerce").fillna(global_lot_size)
df["entry_price"] = pd.to_numeric(df.get("entry_price", np.nan), errors="coerce")
df["exit_price"] = pd.to_numeric(df.get("exit_price", np.nan), errors="coerce")
df["fees"] = pd.to_numeric(df.get("fees", np.nan), errors="coerce").fillna(default_fees)
df["notes"] = df.get("notes", "").astype(str)

# parse datetimes tz-safe
df["entry_time_parsed"] = df["entry_time"].apply(parse_datetime)
df["exit_time_parsed"] = df["exit_time"].apply(parse_datetime)

# PnL
df["pnl"] = df.apply(lambda r: compute_pnl_units(r, global_lot_size), axis=1)

# running balance
running = float(initial_balance)
cumul = []
for _, r in df.iterrows():
    if pd.notna(r.get("pnl")):
        running += 0.0 if pd.isna(r.get("pnl")) else float(r.get("pnl"))
    cumul.append(running)
df["cumulative_balance"] = cumul

# rename for display: initial caps, remove underscores
display_map = {
    "symbol":"Symbol", "quantity":"Quantity", "lot_size":"Lot Size",
    "entry_price":"Entry Price","exit_price":"Exit Price",
    "entry_time":"Entry Time","exit_time":"Exit Time",
    "fees":"Fees","notes":"Notes","pnl":"PnL","cumulative_balance":"Cumulative Balance",
    "open":"Open","high":"High","low":"Low","close":"Close"
}

# ------------------------
# Header area
# ------------------------
st.markdown('<div class="header-block"><span class="at-badge">⚙️</span><span style="font-size:22px;font-weight:700">Trading Journal</span></div>', unsafe_allow_html=True)
# progress and badge
st.markdown('<div style="display:flex;align-items:center;margin-top:8px"><div class="pnl-badge">PnL Progress: ₹0.00</div><div class="pn-progress" style="flex:1;margin-left:12px"><div class="bar" style="width:8%"></div></div></div>', unsafe_allow_html=True)
st.markdown("<div style='margin-top:8px;font-weight:600'>Latest signal: <span style='color:#0b3d91'>"+("BUY_CE" if force_mode=="BUY_CE" else ("BUY_PE" if force_mode=="BUY_PE" else "AUTO"))+"</span></div>", unsafe_allow_html=True)

# ------------------------
# Candles + Indicators (plotly)
# ------------------------
if show_candles:
    # mock OHLC for now
    candles_df = make_mock_ohlc(periods=30, freq_minutes=15, start_price=25000)
    candles_df["time_str"] = candles_df["time"].dt.strftime("%H:%M\n%b %d, %Y")
    # indicators
    candles_df["ema9"] = ema(candles_df["close"], 9)
    candles_df["ema21"] = ema(candles_df["close"], 21)
    # build figure
    fig = go.Figure(data=[
        go.Candlestick(x=candles_df["time"], open=candles_df["open"], high=candles_df["high"], low=candles_df["low"], close=candles_df["close"], name="Price",
                       increasing_line_color='green', decreasing_line_color='red', increasing_fillcolor='green', decreasing_fillcolor='red', showlegend=True),
        go.Scatter(x=candles_df["time"], y=candles_df["ema9"], mode="lines", name="EMA9", line=dict(color="#f6a623", width=2)),
        go.Scatter(x=candles_df["time"], y=candles_df["ema21"], mode="lines", name="EMA21", line=dict(color="#1f77b4", width=2, dash="dot"))
    ])
    fig.update_layout(xaxis_title="Time (IST)", yaxis_title="Premium", showlegend=True, plot_bgcolor='white', margin=dict(l=40,r=40,t=20,b=40))
    # remove gridlines
    fig.update_xaxes(showgrid=False)
    fig.update_yaxes(showgrid=False)
    st.plotly_chart(fig, use_container_width=True, theme="streamlit")

# ------------------------
# Trade Ledger (table)
# ------------------------
st.markdown("## Trade Ledger")
disp_cols = [c for c in ["symbol","quantity","lot_size","entry_price","exit_price","entry_time","exit_time","fees","notes","open","high","low","close","pnl","cumulative_balance"] if c in df.columns]
display_df = df[disp_cols].copy()
display_df.rename(columns={k:v for k,v in display_map.items() if k in display_df.columns}, inplace=True)
# hide trade_id column if present
if "trade_id" in display_df.columns:
    display_df.drop(columns=["trade_id"], inplace=True, errors='ignore')
# show stretch width
st.dataframe(display_df, width='stretch')

# Export visible table
if st.button("Export visible table to CSV"):
    try:
        os.makedirs("exports", exist_ok=True)
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        p = os.path.join("exports", f"trading_journal_export_{ts}.csv")
        display_df.to_csv(p, index=False)
        st.success(f"Exported to {p}")
    except Exception as e:
        st.error(f"Export failed: {e}")
