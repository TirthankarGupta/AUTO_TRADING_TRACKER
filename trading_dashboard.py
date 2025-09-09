# trading_dashboard.py
# Workable Streamlit dashboard: candlestick chart + extended persistent journal

import streamlit as st
import pandas as pd
from pathlib import Path
from datetime import datetime
import plotly.graph_objects as go

# --- Paths (file sits next to this script) ---
BASE_DIR = Path(__file__).parent.resolve()
price_path = BASE_DIR / "price_data.csv"
journal_path = BASE_DIR / "journal.csv"

st.set_page_config(page_title="Auto Trading Tracker", layout="wide")
st.title("AUTO TRADING TRACKER — Dashboard (Workable)")

# ---------------- Sidebar (controls + actions) ----------------
with st.sidebar:
    st.header("Controls")
    symbol = st.text_input("Symbol (e.g. NIFTY)", value="NIFTY")
    timeframe = st.selectbox("Timeframe", ["1m", "5m", "15m", "1h", "1d"])
    st.markdown(f"**Project folder:** `{BASE_DIR}`")
    st.markdown("---")

    if st.button("Run backtest (placeholder)"):
        st.info("Backtest: placeholder — we'll add the runner later.")

    st.markdown("### Trade actions")

    # ----------------- New trade (mock) that saves extended journal -----------------
    if st.button("New trade (mock)"):
        new_trade = {
            "entry_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "exit_time": "",                # empty for now, can be updated later
            "symbol": symbol,
            "qty": 75,
            "side": "BUY",
            "entry_price": None,
            "exit_price": None,
            "pnl": 0.0,
            "notes": ""
        }

        # Append to CSV (create if doesn't exist)
        if journal_path.exists():
            try:
                dfj = pd.read_csv(journal_path)
                dfj = pd.concat([dfj, pd.DataFrame([new_trade])], ignore_index=True)
            except Exception:
                dfj = pd.DataFrame([new_trade])
        else:
            dfj = pd.DataFrame([new_trade])

        # Ensure consistent column order
        cols = ["entry_time", "exit_time", "symbol", "qty", "side", "entry_price", "exit_price", "pnl", "notes"]
        dfj = dfj.reindex(columns=cols)
        dfj.to_csv(journal_path, index=False)
        st.success("New trade saved to journal.csv (extended format)")

    st.markdown("---")
    st.write("Quick actions")
    if st.button("Create sample price CSV"):
        sample = [
            {"datetime": "2025-09-09 09:15:00", "open": 19450, "high": 19480, "low": 19430, "close": 19460, "volume": 1200},
            {"datetime": "2025-09-09 09:16:00", "open": 19460, "high": 19490, "low": 19455, "close": 19480, "volume": 900},
            {"datetime": "2025-09-09 09:17:00", "open": 19480, "high": 19500, "low": 19470, "close": 19495, "volume": 1100},
            {"datetime": "2025-09-09 09:18:00", "open": 19495, "high": 19510, "low": 19490, "close": 19500, "volume": 950},
            {"datetime": "2025-09-09 09:19:00", "open": 19500, "high": 19520, "low": 19495, "close": 19510, "volume": 1250},
        ]
        pd.DataFrame(sample).to_csv(price_path, index=False)
        st.success(f"Sample price CSV created at `{price_path}`")

# ---------------- Main layout ----------------
col1, col2 = st.columns([2, 1])

# Try to load price CSV (located next to script)
loaded = False
if price_path.exists():
    try:
        df = pd.read_csv(price_path, parse_dates=["datetime"])
        df = df.sort_values("datetime").set_index("datetime")
        loaded = True
    except Exception as e:
        st.error(f"Error loading CSV: {e}")
else:
    pass  # show a small hint later

with col1:
    st.subheader("Price / Candlestick")
    if loaded:
        fig = go.Figure(data=[go.Candlestick(
            x=df.index,
            open=df['open'],
            high=df['high'],
            low=df['low'],
            close=df['close']
        )])
        fig.update_layout(height=540, margin=dict(l=10, r=10, t=30, b=10))
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info(f"No price CSV found at `{price_path}`. Use the sidebar button 'Create sample price CSV' to create sample data.")

    st.subheader("Signals")
    st.write("No signals yet — we'll add indicator panels and signal logic next.")

with col2:
    st.subheader("Trade Journal")
    if journal_path.exists():
        try:
            dfj = pd.read_csv(journal_path)
            st.dataframe(dfj)
            csv_bytes = dfj.to_csv(index=False).encode('utf-8')
            st.download_button("Download journal.csv", data=csv_bytes, file_name="journal.csv", mime="text/csv")
        except Exception as e:
            st.error(f"Unable to read journal: {e}")
    else:
        st.info("No trades yet. Use 'New trade (mock)' in the sidebar to add a trade.")

st.markdown("---")
st.caption("Workable version: candlestick + extended persistent journal. Run `streamlit run trading_dashboard.py`.")
