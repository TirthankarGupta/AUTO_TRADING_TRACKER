# trading_dashboard_fixed.py
# Single-file Streamlit app: left / center / right layout, ready-to-run.
import streamlit as st
import pandas as pd
import numpy as np
import requests
from datetime import datetime

# page config
st.set_page_config(page_title="Trading Journal", layout="wide", initial_sidebar_state="collapsed")

# basic constants
API_BASE = "http://127.0.0.1:5001"  # mock backend (can be down; use simulate)
NAVY = "#0B2545"
ORANGE = "#FF7A2D"
WHITE = "#FFFFFF"
GRAY = "#F4F6F8"

# small helper: simulate quotes
def fetch_quotes(symbol: str, count: int, simulate: bool=False):
    if simulate:
        now = pd.Timestamp.now()
        t = pd.date_range(end=now, periods=count, freq="T")
        noise = np.random.normal(0, 4, size=count).cumsum()
        base = 25000 if symbol.upper().startswith("NIFTY") else 20000
        close = base + noise
        df = pd.DataFrame({
            "datetime": t,
            "open": np.roll(close, 1),
            "high": close + np.abs(np.random.normal(0, 2, size=count)),
            "low": close - np.abs(np.random.normal(0, 2, size=count)),
            "close": close,
            "volume": np.random.randint(100, 1000, size=count)
        })
        df.loc[df.index[0], "open"] = df.loc[df.index[0], "close"]
        df = df.set_index("datetime")
        return df
    # try real backend
    try:
        r = requests.get(f"{API_BASE}/quote", params={"symbol": symbol, "count": count}, timeout=5)
        r.raise_for_status()
        payload = r.json()
        data = payload.get("data", [])
        df = pd.DataFrame(data)
        if "datetime" in df.columns:
            df["datetime"] = pd.to_datetime(df["datetime"], errors="coerce")
            df = df.set_index("datetime")
        return df
    except Exception as e:
        # return empty with columns on error
        return pd.DataFrame(columns=["open", "high", "low", "close", "volume"])

# --- CSS & layout skeleton (safe, with matching tags) ---
st.markdown(
    f"""
    <style>
    /* Remove Streamlit default top padding so header aligns */
    .block-container {{
      padding-top: 0rem !important;
    }}
    /* layout */
    .app-layout {{
      display:flex;
      flex-direction: row;
      gap: 20px;
      align-items: flex-start;
      padding: 12px;
      box-sizing: border-box;
    }}
    .side-panel {{
      width: 220px;
      min-height: calc(100vh - 40px);
      background: {NAVY};
      color: {WHITE};
      border-radius: 12px;
      padding: 18px;
      box-sizing: border-box;
      display:flex;
      flex-direction: column;
    }}
    .order-panel {{
      width: 260px;
      min-height: calc(100vh - 40px);
      background: {NAVY};
      color: {WHITE};
      border-radius: 12px;
      padding: 18px;
      box-sizing: border-box;
    }}
    .center-card {{
      flex: 1;
      background: {WHITE};
      border-radius: 10px;
      box-shadow: 0 6px 18px rgba(15,23,42,0.06);
      padding: 0;
      box-sizing: border-box;
      min-height: 120px;
    }}
    .center-header {{
      background: {NAVY};
      color: {WHITE};
      padding: 12px 16px;
      border-top-left-radius: 10px;
      border-top-right-radius: 10px;
      display:flex;
      align-items:center;
      gap:12px;
    }}
    .center-body {{
      padding: 18px;
      background: {WHITE};
      box-sizing: border-box;
    }}
    @media (max-width:1100px) {{
      .side-panel, .order-panel {{ display:none; }}
      .center-card {{ border-radius:0; padding-top:12px; }}
    }}
    </style>
    """,
    unsafe_allow_html=True,
)

# open main wrapper
st.markdown('<div class="app-layout">', unsafe_allow_html=True)

# ===== LEFT PANEL =====
st.markdown('<div class="side-panel">', unsafe_allow_html=True)
st.markdown('<div style="font-weight:700;font-size:18px;margin-bottom:10px;">Controls</div>', unsafe_allow_html=True)

symbol = st.text_input("Symbol (example: NIFTY)", value="NIFTY", key="left_symbol")
timeframe = st.selectbox("Timeframe", ["1m", "5m", "15m"], index=0, key="left_timeframe")
count = st.number_input("Candles (count)", min_value=20, max_value=2000, value=120, step=10, key="left_count")
simulate = st.checkbox("Simulate data (ignore backend)", value=True, key="left_sim")
refresh = st.button("Refresh now", key="left_refresh")

st.markdown("<hr style='border:none;border-top:1px solid rgba(255,255,255,0.06);margin-top:8px;margin-bottom:8px;'>", unsafe_allow_html=True)
st.markdown(f'<div style="font-size:12px;opacity:0.9">Mock backend:<br><a href="{API_BASE}" target="_blank" style="color:#B4C6D8;">{API_BASE}</a></div>', unsafe_allow_html=True)
st.markdown('</div>', unsafe_allow_html=True)  # close left panel

# ===== CENTER CARD =====
st.markdown('<div class="center-card">', unsafe_allow_html=True)
st.markdown('<div class="center-header"><div style="width:36px;height:36px;border-radius:8px;background:'+ORANGE+';display:inline-block;margin-right:8px;"></div><div style="font-weight:800;font-size:16px;">Trading Journal</div></div>', unsafe_allow_html=True)
st.markdown('<div class="center-body">', unsafe_allow_html=True)

# center content: price chart and ledger
st.subheader(f"Price Chart {symbol} — {timeframe}")
if refresh:
    st.experimental_rerun()

df = fetch_quotes(symbol, int(count), simulate=simulate)
if df.empty or "close" not in df.columns or df["close"].dropna().empty:
    st.info("No price data available. Try 'Simulate' or change symbol/count.")
else:
    # simple line chart (native streamlit)
    st.line_chart(df["close"])

st.markdown("### Ledger")
# example empty ledger
ledger_cols = ["time", "symbol", "type", "strike", "qty", "entry_price", "exit_price", "status", "pnl"]
ledger_df = pd.DataFrame(columns=ledger_cols)
st.dataframe(ledger_df, height=200)

# small toggle
if st.button("Show / Hide Trading Log"):
    st.write("Trading log toggle (placeholder).")

st.markdown('</div>', unsafe_allow_html=True)  # close center-body
st.markdown('</div>', unsafe_allow_html=True)  # close center-card

# ===== RIGHT / ORDER PANEL =====
st.markdown('<div class="order-panel">', unsafe_allow_html=True)
st.markdown('<div style="font-weight:700;font-size:18px;margin-bottom:10px;">Orders</div>', unsafe_allow_html=True)

opt_type = st.selectbox("Option Type", ["CE", "PE"], index=0, key="right_opt_type")
use_atm = st.checkbox("Use ATM strike (auto)", value=True, key="right_use_atm")
strike_price = st.number_input("Strike price", value=25000, step=50, key="right_strike")
qty = st.number_input("Qty / lots", min_value=1, max_value=1000, value=1, key="right_qty")
if st.button("Place BUY Order (Right)"):
    st.success(f"Simulated BUY order placed: {opt_type} strike {strike_price} qty {qty}")

st.markdown('</div>', unsafe_allow_html=True)  # close order-panel

# finally close the main layout
st.markdown('</div>', unsafe_allow_html=True)  # close app-layout

# footer note
st.markdown('<div style="padding:6px 12px 30px 12px;color:#666;font-size:12px">Note: this is a fixed-layout test build. Remove or adapt CSS for production.</div>', unsafe_allow_html=True)
