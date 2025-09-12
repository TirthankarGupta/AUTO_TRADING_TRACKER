# trading_bot.py
"""
Trading Bot with trade logging
- Supports forced CE/PE (ce, pe)
- Places mock order
- Logs executed trade into trades.csv via trades_writer
"""
import pandas as pd
from datetime import datetime
import requests
import sys
import trades_writer   # <-- NEW

class MockSmartAPI:
    def __init__(self, base_url="http://127.0.0.1:5001"):
        self.base_url = base_url.rstrip("/")
        self.token = None

    def login(self, client_code="demo", password="demo"):
        url = f"{self.base_url}/login"
        r = requests.post(url, json={"client_code": client_code, "password": password})
        r.raise_for_status()
        data = r.json()
        self.token = data.get("access_token")
        return data

    def get_quote(self, symbol="NIFTY", count=100, force=None):
        url = f"{self.base_url}/quote"
        params = {"symbol": symbol, "count": count}
        if force:
            params["force"] = force
        r = requests.get(url, params=params)
        r.raise_for_status()
        return r.json()

    def place_order(self, order_payload):
        url = f"{self.base_url}/order"
        headers = {}
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        r = requests.post(url, json=order_payload, headers=headers)
        r.raise_for_status()
        return r.json()

# --- indicators ---
def ema(series: pd.Series, span: int) -> pd.Series:
    return series.ewm(span=span, adjust=False).mean()

def rsi(series: pd.Series, length: int = 14) -> pd.Series:
    delta = series.diff()
    up = delta.clip(lower=0)
    down = -1 * delta.clip(upper=0)
    ma_up = up.ewm(alpha=1/length, adjust=False).mean()
    ma_down = down.ewm(alpha=1/length, adjust=False).mean()
    rs = ma_up / (ma_down.replace(0, 1e-10))
    rsi_val = 100 - (100 / (1 + rs))
    return rsi_val

def compute_indicators(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    if "close" not in df.columns:
        raise ValueError("Dataframe must contain 'close' column'")
    df["close"] = pd.to_numeric(df["close"], errors="coerce")
    df = df.dropna(subset=["close"])
    df["ema9"] = ema(df["close"], span=9)
    df["ema21"] = ema(df["close"], span=21)
    df["rsi"] = rsi(df["close"], length=14)
    return df

def generate_signal(df: pd.DataFrame) -> str:
    latest = df.iloc[-1]
    if pd.isna(latest["ema9"]) or pd.isna(latest["ema21"]) or pd.isna(latest["rsi"]):
        return "HOLD"
    if latest["ema9"] > latest["ema21"] and latest["rsi"] < 70:
        return "BUY_CE"
    elif latest["ema9"] < latest["ema21"] and latest["rsi"] > 30:
        return "BUY_PE"
    else:
        return "HOLD"

def build_order_payload(signal: str, symbol: str, qty: int, price: float):
    instrument = "CE" if signal == "BUY_CE" else "PE"
    return {
        "symbol": symbol,
        "instrument": instrument,
        "side": "BUY",
        "quantity": qty,
        "price": round(float(price), 2),
        "order_type": "MARKET",
        "timestamp": int(datetime.now().timestamp()),
        "reason": signal
    }

if __name__ == "__main__":
    symbol = sys.argv[1] if len(sys.argv) > 1 else "NIFTY"
    try:
        count = int(sys.argv[2]) if len(sys.argv) > 2 else 100
    except:
        count = 100
    try:
        qty = int(sys.argv[3]) if len(sys.argv) > 3 and sys.argv[3].isdigit() else 1
    except:
        qty = 1

    # parse force arg
    force_arg = None
    if len(sys.argv) >= 5:
        force_arg = sys.argv[4].lower()
    elif len(sys.argv) == 4:
        maybe = sys.argv[3].lower()
        if maybe in ("ce", "pe"):
            force_arg = maybe

    api = MockSmartAPI()
    print("Login response:", api.login())

    # fetch candles
    raw = api.get_quote(symbol=symbol, count=count, force=force_arg)
    candles = raw["value"] if isinstance(raw, dict) and "value" in raw else raw
    df = compute_indicators(pd.DataFrame(candles))

    # generate or force signal
    if force_arg == "ce":
        signal = "BUY_CE"
    elif force_arg == "pe":
        signal = "BUY_PE"
    else:
        signal = generate_signal(df)

    print(f"{datetime.now()} → Signal: {signal}")

    if signal in ("BUY_CE", "BUY_PE"):
        last_close = float(df.iloc[-1]["close"])
        order_payload = build_order_payload(signal, symbol, qty, last_close)
        print("Placing mock order:", order_payload)
        order_resp = api.place_order(order_payload)
        print("Mock order response:", order_resp)

        # NEW: record the trade
        trades_writer.append_trade_to_csv(order_resp, order_payload)
