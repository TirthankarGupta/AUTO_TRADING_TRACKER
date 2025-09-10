# trading_dashboard.py
# Overwrite your existing file with this single script.
# This version applies:
#  - Sidebar background matching the top header gradient (blue)
#  - Top header with orange "AT" logo and Login pill
#  - All other UI and candlestick behavior retained from previous working version

import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import plotly.graph_objects as go

st.set_page_config(page_title="AUTO TRADING TRACKER", layout="wide", initial_sidebar_state="expanded")

# ---------------------
# Config values (tweak if needed)
# ---------------------
SIDEBAR_W = 260
HEADER_H = 72
CONTENT_PAD = 22

# ---------------------
# CSS (no f-strings with braces)
# ---------------------
css_template = """
<style>
:root {
  --sidebar-w: __SIDEBAR_W__;
  --header-h: __HEADER_H__;
  --content-pad: __CONTENT_PAD__;
}

/* hide default Streamlit top menu/header/footer (we provide our own) */
#MainMenu, header, footer, header[data-testid="stHeader"] {
  display: none !important;
}

/* force sidebar width and style it with same gradient as header */
section[data-testid="stSidebar"] > div:first-of-type {
  min-width: var(--sidebar-w) !important;
  max-width: var(--sidebar-w) !important;
  width: var(--sidebar-w) !important;
  padding-left: 20px !important;
  padding-right: 14px !important;
  box-sizing: border-box;
  border-top-left-radius: 12px;
  border-bottom-left-radius: 12px;
  /* Sidebar background matches header gradient */
  background: linear-gradient(90deg,#071428,#0b2440) !important;
  color: #ffffff !important;
}

/* Adjust form control backgrounds inside sidebar to stay visible */
section[data-testid="stSidebar"] .stTextInput > div > input,
section[data-testid="stSidebar"] .stSelectbox > div[role="combobox"] > div,
section[data-testid="stSidebar"] textarea, 
section[data-testid="stSidebar"] .stNumberInput > div > input {
  background: #ffffff !important;
  color: #111 !important;
}

/* labels and small text color in sidebar */
section[data-testid="stSidebar"] label, section[data-testid="stSidebar"] .field-label, section[data-testid="stSidebar"] .css-1aumxhk {
  color: #dbe9fb !important;
}

/* main content: move right of sidebar and reserve space for header */
.main .block-container {
  margin-left: var(--sidebar-w) !important;
  padding-left: var(--content-pad) !important;
  padding-right: var(--content-pad) !important;
  padding-top: calc(var(--header-h) + 18px) !important;
  box-sizing: border-box;
  max-width: calc(100% - var(--sidebar-w)) !important;
}

/* fixed single top header */
.custom-top-header {
  position: fixed;
  top: 0;
  left: calc(var(--sidebar-w) + 12px);
  right: 12px;
  height: var(--header-h);
  background: linear-gradient(90deg,#071428,#0b2440);
  border-radius: 10px;
  padding: 10px 18px;
  z-index: 9999;
  display:flex;
  align-items:center;
  gap:16px;
  color: #ffffff;
  box-shadow: 0 8px 18px rgba(0,0,0,0.08);
  font-family: "Segoe UI", Roboto, Arial, sans-serif;
}

/* orange square logo */
.custom-top-header .logo {
  width:46px;
  height:46px;
  background:#ff8a00;
  border-radius:10px;
  display:flex;
  align-items:center;
  justify-content:center;
  font-weight:800;
  color:#fff;
  box-shadow: 0 3px 0 rgba(0,0,0,0.06) inset;
  font-family: "Segoe UI", Roboto, Arial, sans-serif;
  font-size: 18px;
}

/* title block */
.custom-top-header .titleblock {
  display:flex;
  flex-direction:column;
  line-height:1;
}
.custom-top-header .maintitle {
  font-size:18px;
  font-weight:700;
  letter-spacing:0.6px;
}
.custom-top-header .subtitle {
  font-size:11px;
  opacity:0.85;
  margin-top:2px;
}

/* Login pill on right */
.custom-top-header .login-pill {
  margin-left:auto;
  padding:8px 12px;
  background: rgba(255,255,255,0.06);
  border-radius:8px;
  font-size:13px;
  color: #e8eef7;
  border: 1px solid rgba(255,255,255,0.03);
}

/* Sidebar headings bold and CAPS */
section[data-testid="stSidebar"] h2, section[data-testid="stSidebar"] .section-title {
  font-weight: 800 !important;
  text-transform: uppercase !important;
  letter-spacing: 0.6px;
  color: #ffffff !important;
}

/* zebra table */
.zebra-table {
  border-collapse: collapse;
  width: 100%;
  font-family: "Segoe UI", Roboto, Arial, sans-serif;
  margin-bottom: 18px;
}
.zebra-table th {
  text-align: left;
  padding: 10px 12px;
  background: #f6f7fb;
  color: #333;
  font-weight: 600;
  border-bottom: 1px solid #e6e9ef;
}
.zebra-table td {
  padding: 10px 12px;
  border-bottom: 1px solid #f2f4f8;
  color: #1e2a36;
}
.zebra-table tr:nth-child(even) { background: #ffffff; }
.zebra-table tr:nth-child(odd)  { background: #fbfcfe; }

/* keep first child of block container tidy */
.block-container > div:first-child {
  margin-top: 0 !important;
  padding-top: 0 !important;
}
</style>
"""

css = css_template.replace("__SIDEBAR_W__", f"{SIDEBAR_W}px").replace("__HEADER_H__", f"{HEADER_H}px").replace("__CONTENT_PAD__", f"{CONTENT_PAD}px")
st.markdown(css, unsafe_allow_html=True)

# ---------------------
# Top header HTML (single header with orange AT and Login pill)
# ---------------------
st.markdown("""
<div class="custom-top-header" role="banner">
  <div class="logo">AT</div>
  <div class="titleblock">
    <div class="maintitle">AUTO TRADING TRACKER</div>
    <div class="subtitle">Demo</div>
  </div>
  <div class="login-pill">Login</div>
</div>
""", unsafe_allow_html=True)

# ---------------------
# Sidebar controls (unchanged layout; only background color changed via CSS above)
# ---------------------
with st.sidebar:
    st.markdown("<div style='padding-top:6px;'>", unsafe_allow_html=True)
    st.subheader("Controls")
    st.markdown('<div class="field-label">Symbol (e.g. NIFTY)</div>', unsafe_allow_html=True)
    symbol = st.text_input("", value="NIFTY", placeholder="NIFTY")
    st.markdown('<div class="field-label">Timeframe</div>', unsafe_allow_html=True)
    timeframe = st.selectbox("", ["1m", "5m", "15m", "1h"], index=0)
    st.markdown("<div style='height:10px;'></div>", unsafe_allow_html=True)
    st.markdown('<div class="section-title">Project folder:</div>', unsafe_allow_html=True)
    st.code("C:\\AUTO_TRADING_TRACKER", language="text")
    st.markdown("<div style='height:10px;'></div>", unsafe_allow_html=True)
    st.markdown('<div class="section-title">Trade actions</div>', unsafe_allow_html=True)
    st.button("Run backtest (placeholder)", disabled=True)
    st.button("New trade (mock)", disabled=True)
    st.markdown("<hr/>", unsafe_allow_html=True)
    st.markdown('<div class="section-title">Quick actions</div>', unsafe_allow_html=True)
    st.button("Create sample price CSV", disabled=True)
    st.markdown("<div style='height:10px;'></div>", unsafe_allow_html=True)
    st.markdown('<div class="section-title">Indicators</div>', unsafe_allow_html=True)
    st.checkbox("EMA (9)", value=True)
    st.checkbox("EMA (21)", value=True)
    st.checkbox("VWAP", value=True)
    st.checkbox("RSI (14)", value=True)
    st.number_input("RSI period", value=14, step=1)
    st.markdown("</div>", unsafe_allow_html=True)

# ---------------------
# Sample candlestick data (keeps visuals)
# ---------------------
def make_sample_candles(n=40, start_price=19500):
    rng = pd.date_range(end=datetime.now(), periods=n, freq='T')
    p = start_price + np.cumsum(np.random.randn(n).clip(-2,2) * 10.0)
    openp  = p + np.random.randn(n) * 1.5
    closep = p + np.random.randn(n) * 1.5
    highp  = np.maximum(openp, closep) + np.abs(np.random.randn(n) * 4.0)
    lowp   = np.minimum(openp, closep) - np.abs(np.random.randn(n) * 4.0)
    df = pd.DataFrame({
        "datetime": rng,
        "open": openp.round(2),
        "high": highp.round(2),
        "low": lowp.round(2),
        "close": closep.round(2),
    })
    return df

df_candles = make_sample_candles(40, start_price=19500)
df_candles['ema9'] = df_candles['close'].ewm(span=9, adjust=False).mean()
df_candles['ema21'] = df_candles['close'].ewm(span=21, adjust=False).mean()
df_candles['vwap'] = df_candles['close'].expanding().mean()

# ---------------------
# Plotly candlestick + invisible scatter for hover + explicit up/down colors
# ---------------------
up_color = "#1f7a1f"
down_color = "#c13b3b"

fig = go.Figure()

fig.add_trace(go.Candlestick(
    x=df_candles['datetime'],
    open=df_candles['open'],
    high=df_candles['high'],
    low=df_candles['low'],
    close=df_candles['close'],
    increasing=dict(line=dict(color=up_color), fillcolor=up_color),
    decreasing=dict(line=dict(color=down_color), fillcolor=down_color),
    name="Candles",
    showlegend=False
))

# indicator lines
fig.add_trace(go.Scatter(x=df_candles['datetime'], y=df_candles['ema9'], mode='lines', name='EMA 9', line=dict(color='#f2a400', width=2)))
fig.add_trace(go.Scatter(x=df_candles['datetime'], y=df_candles['ema21'], mode='lines', name='EMA 21', line=dict(color='#66b466', width=2)))
fig.add_trace(go.Scatter(x=df_candles['datetime'], y=df_candles['vwap'], mode='lines', name='VWAP', line=dict(color='#2d6cff', width=2, dash='dash')))

# invisible scatter for hover (works across plotly versions)
customdata = np.stack([df_candles['open'], df_candles['high'], df_candles['low'], df_candles['close']], axis=-1)
hover_template = "Time: %{x}<br>Open: %{customdata[0]}<br>High: %{customdata[1]}<br>Low: %{customdata[2]}<br>Close: %{customdata[3]}<extra></extra>"

fig.add_trace(go.Scatter(
    x=df_candles['datetime'],
    y=df_candles['close'],
    mode='markers',
    marker=dict(size=6, color='rgba(0,0,0,0)'),
    hovertemplate=hover_template,
    customdata=customdata,
    showlegend=False,
    hoverinfo='text'
))

fig.update_layout(
    template="plotly_white",
    margin=dict(l=20, r=24, t=8, b=36),
    showlegend=True,
    legend=dict(orientation="v", x=0.98, xanchor="right", y=0.95),
    xaxis=dict(showgrid=False, title=dict(text="Time", font=dict(size=11)), tickformat='%H:%M'),
    yaxis=dict(showgrid=False, title=dict(text="Price (INR)", font=dict(size=11))),
    hovermode='x unified'
)

st.markdown("<div style='height:6px;'></div>", unsafe_allow_html=True)
st.title("Price / Candlestick")
st.plotly_chart(fig, use_container_width=True, theme="streamlit", height=640)

# ---------------------
# Simple session journal + zebra tables
# ---------------------
if 'journal' not in st.session_state:
    st.session_state['journal'] = pd.DataFrame([
        {"Date": (datetime.now() - timedelta(minutes=45)).strftime("%Y-%m-%d"),
         "Symbol": "NIFTY",
         "Entry time": (datetime.now() - timedelta(minutes=44)).strftime("%H:%M:%S"),
         "Entry price": 19500,
         "Exit price": 19520,
         "Entry exit": "19500 -> 19520",
         "PnL": 20},
        {"Date": (datetime.now() - timedelta(minutes=12)).strftime("%Y-%m-%d"),
         "Symbol": "NIFTY",
         "Entry time": (datetime.now() - timedelta(minutes=11)).strftime("%H:%M:%S"),
         "Entry price": 19530,
         "Exit price": 19510,
         "Entry exit": "19530 -> 19510",
         "PnL": -20},
    ])

def df_to_zebra_html(df: pd.DataFrame, max_rows=10):
    df2 = df.copy()
    df2.columns = [str(c).strip().title().replace("_", " ") for c in df2.columns]
    html = '<table class="zebra-table"><thead><tr>'
    for col in df2.columns:
        html += f"<th>{col}</th>"
    html += "</tr></thead><tbody>"
    for _, row in df2.head(max_rows).iterrows():
        html += "<tr>"
        for col in df2.columns:
            html += f"<td>{row[col]}</td>"
        html += "</tr>"
    html += "</tbody></table>"
    return html

st.markdown("<h2 style='margin-top:28px;'>Trade Journal</h2>", unsafe_allow_html=True)
st.markdown(df_to_zebra_html(st.session_state['journal']), unsafe_allow_html=True)

st.markdown("<h2 style='margin-top:10px;'>Add New Trade</h2>", unsafe_allow_html=True)
with st.form(key='add_trade_form', clear_on_submit=False):
    c1, c2, c3 = st.columns([2,1,1])
    symbol_in = c1.text_input("Symbol", value="NIFTY")
    entry_price = c2.number_input("Entry price", value=19500.0, step=0.5, format="%.2f")
    qty = c3.number_input("Qty", value=1, step=1)
    c4, c5 = st.columns([1,1])
    exit_price = c4.number_input("Exit price", value=0.0, step=0.5, format="%.2f")
    pnl = c5.number_input("P&L", value=0.0, step=0.5, format="%.2f")
    submit = st.form_submit_button("Add trade (mock)")
    if submit:
        new_row = {
            "Date": datetime.now().strftime("%Y-%m-%d"),
            "Symbol": symbol_in,
            "Entry time": datetime.now().strftime("%H:%M:%S"),
            "Entry price": entry_price,
            "Exit price": exit_price if exit_price!=0 else "",
            "Entry exit": f"{entry_price} -> {exit_price}" if exit_price!=0 else "",
            "PnL": pnl
        }
        st.session_state['journal'] = pd.concat([pd.DataFrame([new_row]), st.session_state['journal']], ignore_index=True)
        st.success("Trade appended to journal (mock). Scroll down to view.")

st.markdown(df_to_zebra_html(st.session_state['journal']), unsafe_allow_html=True)
st.markdown("<div style='height:60px;'></div>", unsafe_allow_html=True)
