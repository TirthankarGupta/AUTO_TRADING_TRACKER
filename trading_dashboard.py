# trading_dashboard.py
# Single-file Streamlit dashboard:
# - Top dark header with logo & title
# - Trading Journal header at the very top
# - Candlestick chart with EMA9, EMA21, VWAP overlays
# - RSI subplot
# - Trade ledger table + CSV export
# - Mock data used for candles and ledger (swap with real API later)

import streamlit as st
import pandas as pd
import numpy as np
import datetime
from plotly.subplots import make_subplots
import plotly.graph_objects as go

# --------- Page config ----------
st.set_page_config(page_title="AUTO TRADING TRACKER", layout="wide", initial_sidebar_state="expanded")

# --------- Top header with logo (exact placement) ----------
header_html = """
<div style="background:#07122a; padding:10px 16px; border-radius:6px; display:flex; align-items:center; gap:12px;">
  <div style="display:flex; align-items:center; gap:12px;">
    <img src="./assets/logo.png" alt="logo" style="height:36px; width:36px; object-fit:contain; border-radius:6px;" onerror="this.style.display='none'"/>
    <div style="color:#ffffff; font-weight:700; font-size:18px;">AUTO TRADING TRACKER</div>
    <div style="color:#9fb7d8; font-size:12px; margin-left:8px;">Demo</div>
  </div>
  <div style="flex:1"></div>
  <div>
    <button disabled style="background:#0b1220; color:#fff; border:1px solid rgba(255,255,255,0.06); padding:6px 10px; border-radius:6px; cursor:not-allowed;">Login</button>
  </div>
</div>
"""
st.markdown(header_html, unsafe_allow_html=True)

# --------- Very top Trading Journal bar (prominent) ----------
st.markdown(
    """
    <div style="background:#0b2140; padding:8px 12px; border-radius:6px; margin-top:10px; margin-bottom:8px; box-shadow: 0 1px 0 rgba(0,0,0,0.2);">
      <div style="display:flex; align-items:center; gap:12px;">
        <div style="background:#ffdb4d; color:#08203a; padding:6px 8px; border-radius:6px; font-weight:700;">⚠️</div>
        <div style="color:#fff; font-weight:700; font-size:16px;">TRADING JOURNAL</div>
        <div style="flex:1"></div>
        <div style='color:#c6f6d5; background:#166534; padding:4px 8px; border-radius:6px; font-weight:600;'>PnL Progress: ₹0.00</div>
      </div>
    </div>
    """,
    unsafe_allow_html=True
)

# --------- Sidebar controls ----------
st.sidebar.header("Controls")
symbol = st.sidebar.text_input("Symbol (e.g. NIFTY)", value="NIFTY")
timeframe = st.sidebar.selectbox("Timeframe", ["1m","5m","15m","1h"], index=0)
st.sidebar.markdown("**Project folder**")
st.sidebar.text("C:\\AUTO_TRADING_TRACKER")

st.sidebar.markdown("---")
st.sidebar.header("Trade Actions")
# placeholders
if st.sidebar.button("Run backtest (mock)"):
    st.sidebar.info("Backtest started (mock).")

st.sidebar.markdown("---")
st.sidebar.header("Quick Actions")
st.sidebar.button("Create sample trade")
st.sidebar.markdown("---")
st.sidebar.header("Indicators")
show_ema9 = st.sidebar.checkbox("EMA (9)", value=True)
show_ema21 = st.sidebar.checkbox("EMA (21)", value=True)
show_vwap = st.sidebar.checkbox("VWAP", value=True)
show_rsi = st.sidebar.checkbox("RSI", value=True)
rsi_period = st.sidebar.number_input("RSI period", value=14, min_value=2, max_value=50)

# --------- Generate mock OHLC data (replace with real API feed later) ----------
def make_mock_ohlc(n=120, start_price=25000):
    rng = pd.date_range(end=pd.Timestamp.now(), periods=n, freq="1T")
    close = (pd.Series(np.sin(np.linspace(0, 6.28, n))) * 30).cumsum() / 10 + start_price
    open_ = close.shift(1).fillna(close.iloc[0])
    high = pd.concat([open_, close], axis=1).max(axis=1) + np.random.uniform(1, 8, size=n)
    low = pd.concat([open_, close], axis=1).min(axis=1) - np.random.uniform(1, 8, size=n)
    volume = np.random.randint(100, 2000, size=n)
    df = pd.DataFrame({"time": rng, "open": open_.round(2), "high": high.round(2), "low": low.round(2), "close": close.round(2), "volume": volume})
    df.reset_index(drop=True, inplace=True)
    return df

df = make_mock_ohlc(180, start_price=25000)

# --------- Indicators: EMA9, EMA21, VWAP, RSI ----------
def add_indicators(df):
    df = df.copy()
    df["ema9"] = df["close"].ewm(span=9, adjust=False).mean()
    df["ema21"] = df["close"].ewm(span=21, adjust=False).mean()
    # VWAP per row: cumulative typical*vol / cumulative vol
    tp = (df["high"] + df["low"] + df["close"]) / 3
    cum_vtp = (tp * df["volume"]).cumsum()
    cum_vol = df["volume"].cumsum().replace(0, np.nan)
    df["vwap"] = (cum_vtp / cum_vol).fillna(method="bfill")
    # RSI (classic)
    delta = df["close"].diff()
    up = delta.clip(lower=0)
    down = -1 * delta.clip(upper=0)
    ma_up = up.rolling(window=rsi_period, min_periods=1).mean()
    ma_down = down.rolling(window=rsi_period, min_periods=1).mean()
    rs = ma_up / (ma_down.replace(0, np.nan))
    df["rsi"] = 100 - (100 / (1 + rs))
    df["rsi"] = df["rsi"].fillna(50)
    return df

df = add_indicators(df)

# --------- Plot: Candlestick + EMA + VWAP + RSI (Plotly) ----------
st.markdown("### Price / Candlestick")
fig = make_subplots(rows=2, cols=1, shared_xaxes=True, row_heights=[0.76, 0.24], vertical_spacing=0.02, specs=[[{"type":"candlestick"}],[{"type":"xy"}]])

# Candles
fig.add_trace(go.Candlestick(x=df["time"],
                             open=df["open"], high=df["high"], low=df["low"], close=df["close"],
                             name="Price", increasing_line_color='green', decreasing_line_color='red',
                             showlegend=True), row=1, col=1)

# EMA overlays
if show_ema9:
    fig.add_trace(go.Scatter(x=df["time"], y=df["ema9"], mode="lines", line=dict(width=1.6, color="orange"), name="EMA9"), row=1, col=1)
if show_ema21:
    fig.add_trace(go.Scatter(x=df["time"], y=df["ema21"], mode="lines", line=dict(width=1.6, dash="dot", color="royalblue"), name="EMA21"), row=1, col=1)
if show_vwap:
    fig.add_trace(go.Scatter(x=df["time"], y=df["vwap"], mode="lines", line=dict(width=1.5, color="mediumseagreen"), name="VWAP"), row=1, col=1)

# RSI subplot
if show_rsi:
    fig.add_trace(go.Scatter(x=df["time"], y=df["rsi"], mode="lines", name="RSI", line=dict(color="purple")), row=2, col=1)
    fig.add_hline(y=70, row=2, col=1, line=dict(color="red", dash="dash"), annotation_text="70", annotation_position="top left")
    fig.add_hline(y=30, row=2, col=1, line=dict(color="green", dash="dash"), annotation_text="30", annotation_position="bottom left")

fig.update_layout(
    margin=dict(l=50, r=20, t=10, b=40),
    template="plotly_white",
    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    height=520,
)

fig.update_xaxes(showgrid=False)
fig.update_yaxes(title_text="Price", row=1, col=1)
fig.update_yaxes(title_text="RSI", row=2, col=1)

st.plotly_chart(fig, use_container_width=True)

# --------- Trade Ledger (mock) ----------
st.markdown("### Trade Ledger")
# Provide sample trade data similar to the screenshot
now = datetime.datetime.now()
sample_trades = pd.DataFrame([
    {"Date": (now - datetime.timedelta(minutes=90)).strftime("%Y-%m-%d"), "Symbol": "NIFTY", "Quantity": 1, "Lot Size": 1, "Entry Price": 25040, "Exit Price": None, "Entry Time": (now - datetime.timedelta(minutes=90)).strftime("%Y-%m-%d %H:%M:%S"), "Exit Time": None, "Fees": 0.0, "Notes": "auto-recorded [success]", "Open": 25040, "High": 25060, "Low": 25030, "Close": 25050, "Pnl": None, "Cumulative Balance": 100000},
    {"Date": (now - datetime.timedelta(minutes=60)).strftime("%Y-%m-%d"), "Symbol": "NIFTY", "Quantity": 1, "Lot Size": 1, "Entry Price": 25060, "Exit Price": None, "Entry Time": (now - datetime.timedelta(minutes=60)).strftime("%Y-%m-%d %H:%M:%S"), "Exit Time": None, "Fees": 0.0, "Notes": "auto-recorded [success]", "Open": 25060, "High": 25080, "Low": 25040, "Close": 25070, "Pnl": None, "Cumulative Balance": 100000},
    {"Date": (now - datetime.timedelta(minutes=30)).strftime("%Y-%m-%d"), "Symbol": "NIFTY", "Quantity": 1, "Lot Size": 1, "Entry Price": 24960, "Exit Price": None, "Entry Time": (now - datetime.timedelta(minutes=30)).strftime("%Y-%m-%d %H:%M:%S"), "Exit Time": None, "Fees": 0.0, "Notes": "auto-recorded [success]", "Open": 24960, "High": 24980, "Low": 24950, "Close": 24970, "Pnl": None, "Cumulative Balance": 100000},
    {"Date": now.strftime("%Y-%m-%d"), "Symbol": "NIFTY", "Quantity": 1, "Lot Size": 1, "Entry Price": 24960, "Exit Price": None, "Entry Time": now.strftime("%Y-%m-%d %H:%M:%S"), "Exit Time": None, "Fees": 0.0, "Notes": "auto-recorded [success]", "Open": 24960, "High": 24980, "Low": 24950, "Close": 24970, "Pnl": None, "Cumulative Balance": 100000},
])

# Show the table with container width to match screenshot layout
st.dataframe(sample_trades, use_container_width=True, height=220)

# --------- Export visible table to CSV ----------
csv = sample_trades.to_csv(index=False).encode("utf-8")
st.download_button("Export visible table to CSV", data=csv, file_name="trades.csv", mime="text/csv")

# --------- Add New Trade form (mock functionality) ----------
st.markdown("### Add New Trade")
with st.form("add_trade"):
    col1, col2, col3 = st.columns([2,1,1])
    with col1:
        new_symbol = st.text_input("Symbol", value="NIFTY")
    with col2:
        new_entry_price = st.number_input("Entry price", value=25000.00)
    with col3:
        new_qty = st.number_input("Qty", value=1, min_value=1)
    new_exit_price = st.number_input("Exit price", value=0.0)
    submitted = st.form_submit_button("Add trade (mock)")
    if submitted:
        st.success("Trade added (mock). Refresh to see new sample entry.")

# End of file
