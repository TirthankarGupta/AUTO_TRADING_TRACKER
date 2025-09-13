# trading_dashboard_fixed2.py
# Minimal robust Streamlit trading dashboard (self-contained, mock-data friendly)
# Save as UTF-8 without BOM!

import streamlit as st
import pandas as pd
import numpy as np
import requests
from datetime import datetime, timedelta

st.set_page_config(page_title="Trading Journal (Fixed)", layout="wide", initial_sidebar_state="collapsed")

# --- small CSS tweak for header so it looks neat ---
st.markdown(
    """
    <style>
      .header-pill {
        display:inline-block;
        width:36px;height:36px;border-radius:8px;background:#FF7A2D;margin-right:10px;
      }
      .center-card {
        border-radius:8px;
        box-shadow: 0 4px 10px rgba(2,6,23,0.06);
        padding: 4px 8px;
        background:white;
      }
    </style>
    """,
    unsafe_allow_html=True,
)

# ---- Config ----
API_BASE = "http://127.0.0.1:5001"   # backend (if available)
SIMULATE_DEFAULT = True             # change to False to prefer backend if running
LOT_MULTIPLIER = 1

# --- UI layout using columns (stable across Streamlit versions) ---
left_col, center_col, right_col = st.columns([0.22, 1.0, 0.26])

with left_col:
    st.markdown("**Controls**")
    symbol = st.text_input("Symbol (example: NIFTY)", value="NIFTY", key="left_symbol")
    timeframe = st.selectbox("Timeframe", ["1m", "5m", "15m"], index=0, key="left_timeframe")
    count = st.number_input("Candles (count)", min_value=20, max_value=2000, value=120, step=10, key="left_count")
    simulate = st.checkbox("Simulate data (ignore backend)", value=SIMULATE_DEFAULT, key="left_sim")
    refresh = st.button("Refresh now", key="left_refresh")
    st.markdown("---")
    st.markdown(f"<small>Mock backend: <a href='{API_BASE}' target='_blank'>{API_BASE}</a></small>", unsafe_allow_html=True)

with center_col:
    # header
    st.markdown('<div class="center-card"><div style="display:flex;align-items:center;padding:10px 12px;"><div class="header-pill"></div><div style="font-weight:700;">Trading Journal</div></div></div>', unsafe_allow_html=True)

    # area for chart + ledger
    st.markdown("### Price Chart {sym} â€” {tf}".format(sym=symbol, tf=timeframe))
    chart_placeholder = st.empty()
    message_placeholder = st.empty()

    st.markdown("### Ledger")
    ledger_placeholder = st.empty()

with right_col:
    st.markdown("**Orders**")
    opt_type = st.selectbox("Option Type", ["CE", "PE"], index=0, key="right_opt")
    use_atm = st.checkbox("Use ATM strike (auto)", value=True, key="right_atm")
    strike_price = st.text_input("Strike price", value="25000", key="right_strike")
    qty = st.number_input("Qty / lots", min_value=1, value=1, key="right_qty")
    place_buy = st.button("Place BUY Order (Right)", key="right_buy")
    st.markdown("---")
    st.markdown("<small>Note: this is a fixed-layout test. Toggle 'Simulate data' to run without backend.</small>", unsafe_allow_html=True)

# --- helpers: fetch or simulate quotes ---
def simulate_quotes(symbol: str, count: int):
    now = pd.Timestamp.now().floor("T")
    # frequency depends on timeframe: simple mapping
    freq = {"1m":"T", "5m":"5T", "15m":"15T"}.get(timeframe, "T")
    idx = pd.date_range(end=now, periods=count, freq=freq)
    base = 25000 if symbol.upper().startswith("NIFTY") else 20000
    noise = np.random.normal(loc=0.0, scale=4.0, size=count).cumsum()
    close = base + noise
    df = pd.DataFrame({
        "datetime": idx,
        "open": np.roll(close, 1),
        "high": close + np.abs(np.random.normal(0, 2, size=count)),
        "low": close - np.abs(np.random.normal(0, 2, size=count)),
        "close": close,
        "volume": np.random.randint(100, 1500, size=count)
    }).set_index("datetime")
    df.iloc[0, df.columns.get_indexer(["open"])] = df.iloc[0]["close"]
    return df

def fetch_quotes_from_api(symbol: str, count: int):
    try:
        r = requests.get(f"{API_BASE}/quote", params={"symbol": symbol, "count": count}, timeout=5)
        r.raise_for_status()
        payload = r.json()
        data = payload.get("data", [])
        df = pd.DataFrame(data)
        if df.empty:
            return pd.DataFrame()
        if "datetime" in df.columns:
            df["datetime"] = pd.to_datetime(df["datetime"], errors="coerce")
            df = df.set_index("datetime")
        # ensure open/high/low/close exist
        if "close" in df.columns:
            df["open"] = df.get("open", df["close"].shift(1).fillna(df["close"]))
            df["high"] = df.get("high", df[["open","close"]].max(axis=1) + (df["close"] * 0.001).abs())
            df["low"]  = df.get("low", df[["open","close"]].min(axis=1) - (df["close"] * 0.001).abs())
        if "volume" not in df.columns:
            df["volume"] = (df["close"].pct_change().fillna(0).abs() * 1000 + 200).round().astype(int)
        return df.sort_index()
    except Exception as e:
        # bubble up error to caller to show message and fallback
        raise

# --- main logic: fetch data & plot safely ---
def get_data_safe(symbol, count, simulate_flag):
    if simulate_flag:
        return simulate_quotes(symbol, count), None
    try:
        df = fetch_quotes_from_api(symbol, count)
        if df.empty:
            return simulate_quotes(symbol, count), "Backend returned empty data, using simulated data."
        return df, None
    except Exception as e:
        # return simulated data + error message
        return simulate_quotes(symbol, count), f"Quote fetch error: {e}"

# on refresh or on first load
if refresh or True:
    df, err = get_data_safe(symbol, int(count), simulate)
    if err:
        message_placeholder.error(err)
    else:
        message_placeholder.empty()

    # Plot - try plotly, else fall back to Streamlit's built-in chart
    try:
        import plotly.graph_objects as go
        fig = go.Figure(data=[go.Scatter(x=df.index, y=df["close"], mode="lines", name="close")])
        fig.update_layout(margin=dict(l=20, r=20, t=10, b=30), height=320, showlegend=False)
        chart_placeholder.plotly_chart(fig, use_container_width=True)
    except Exception:
        # fallback simple chart
        chart_placeholder.line_chart(df["close"])

    # fill ledger with an empty DataFrame for now
    ledger_df = pd.DataFrame(columns=["time","symbol","type","strike","qty","entry_price","exit_price","status","pnl"])
    ledger_placeholder.dataframe(ledger_df, height=200)

# --- orders handling (simple local mock) ---
if place_buy:
    st.success(f"Placed BUY order (mock): {symbol} {opt_type} qty={qty} strike={strike_price}")

# small footer / status
if simulate:
    st.info("Running in SIMULATE mode â€” backend calls are disabled.")
else:
    st.write("Running against backend: ", API_BASE)

