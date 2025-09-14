# trading_journal.py
# Trading Journal — consolidated baseline (mock candles + indicators)
# Run with: streamlit run trading_journal.py
# or: python trading_journal.py  (for smoke-run behavior)

from datetime import datetime, timedelta
import math
import pandas as pd
import numpy as np
import streamlit as st
import plotly.graph_objects as go

# -------------------------
# Utility: EMA (simple)
# -------------------------
def ema(series: pd.Series, period: int) -> pd.Series:
    """
    Compute exponential moving average. Returns a Series aligned with the input.
    Uses pandas' ewm if available (preferred).
    """
    try:
        return series.ewm(span=period, adjust=False).mean()
    except Exception:
        # fallback simple implementation
        alpha = 2 / (period + 1)
        out = []
        prev = None
        for v in series.fillna(method="ffill").tolist():
            if prev is None:
                prev = v
            else:
                prev = alpha * v + (1 - alpha) * prev
            out.append(prev)
        return pd.Series(out, index=series.index)

# -------------------------
# Mock OHLC generator
# -------------------------
def make_mock_ohlc(start_dt: datetime = None, periods: int = 30, freq_minutes: int = 15, start_price: float = 25000.0) -> pd.DataFrame:
    """
    Generate simple synthetic OHLC candles.
    Returns DataFrame with columns: time, open, high, low, close, volume
    """
    if start_dt is None:
        start_dt = datetime.now()
    rng = [start_dt + timedelta(minutes=freq_minutes * i) for i in range(periods)]
    prices = []
    p = float(start_price)
    for i in range(periods):
        # random walk
        move = np.random.normal(loc=0.0, scale=0.3) * (1 + math.sin(i / 3))
        p = max(1, p + move)
        o = p + np.random.normal(0, 0.5)
        c = p + np.random.normal(0, 0.5)
        hi = max(o, c) + abs(np.random.normal(0, 0.5))
        lo = min(o, c) - abs(np.random.normal(0, 0.5))
        vol = max(1, int(abs(np.random.normal(200, 50))))
        prices.append((rng[i], round(o, 2), round(hi, 2), round(lo, 2), round(c, 2), vol))
    df = pd.DataFrame(prices, columns=["time", "open", "high", "low", "close", "volume"])
    df["time"] = pd.to_datetime(df["time"])
    return df

# -------------------------
# Streamlit UI / Main
# -------------------------
def main():
    st.set_page_config(page_title="Trading Journal (mock)", layout="wide")
    st.title("Trading Journal — Mock Candles + EMA indicators")

    # Controls
    show_candles = st.checkbox("Show candles (mock OHLC)", value=True)
    periods = st.number_input("Candles (count)", min_value=10, max_value=2000, value=30, step=10)
    freq_minutes = st.number_input("Candle frequency (min)", min_value=1, max_value=1440, value=15, step=1)
    start_price = st.number_input("Start price", min_value=1.0, value=25000.0, step=1.0)

    st.markdown("---")

    # Candles + Indicators (plotly)
    if show_candles:
        try:
            candles_df = make_mock_ohlc(periods=periods, freq_minutes=freq_minutes, start_price=start_price)
        except Exception as e:
            st.error(f"make_mock_ohlc failed: {e}")
            return

        if candles_df is None or len(candles_df) == 0:
            st.error("No candle data produced.")
            return

        # Time formatting
        if "time" in candles_df.columns:
            candles_df["time"] = pd.to_datetime(candles_df["time"], errors="coerce")
            candles_df["time_str"] = candles_df["time"].dt.strftime("%H:%M")
        else:
            candles_df["time_str"] = ""

        # EMAs
        if "close" in candles_df.columns:
            candles_df["ema9"] = ema(candles_df["close"], 9)
            candles_df["ema21"] = ema(candles_df["close"], 21)

        # Plotly figure
        fig = go.Figure(layout=dict(margin=dict(l=10, r=10, t=30, b=10)))

        if all(col in candles_df.columns for col in ["open", "high", "low", "close"]):
            fig.add_trace(go.Candlestick(
                x=candles_df["time"],
                open=candles_df["open"],
                high=candles_df["high"],
                low=candles_df["low"],
                close=candles_df["close"],
                name="Price"
            ))
        if "ema9" in candles_df.columns:
            fig.add_trace(go.Scatter(x=candles_df["time"], y=candles_df["ema9"], mode="lines", name="EMA9"))
        if "ema21" in candles_df.columns:
            fig.add_trace(go.Scatter(x=candles_df["time"], y=candles_df["ema21"], mode="lines", name="EMA21"))

        fig.update_layout(xaxis_rangeslider_visible=False, height=520)
        st.plotly_chart(fig, use_container_width=True)

        with st.expander("Show recent candles"):
            st.dataframe(candles_df.tail(50), use_container_width=True)

    st.markdown("---")

    # Quick stats / demo trades
    st.subheader("Quick stats")
    trades = []
    if "trades" not in st.session_state:
        trades = [
            {
                "entry_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "exit_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "pnl": round(np.random.normal(50, 200), 2),
                "pct": round(np.random.normal(0.5, 2), 2),
            }
            for _ in range(5)
        ]
        st.session_state.trades = trades
    else:
        trades = st.session_state.trades

    df_trades = pd.DataFrame(trades)
    if not df_trades.empty:
        st.dataframe(df_trades, use_container_width=True)
        total_realized = df_trades["pnl"].sum()
        st.write(f"Realized P&L (INR): {total_realized:.2f}")
    else:
        st.info("No trades in demo sample.")

# When executed directly
if __name__ == "__main__":
    main()