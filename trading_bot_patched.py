# trading_bot_patched.py
import requests
import pandas as pd
from requests.exceptions import RequestException
from datetime import datetime

API_BASE = 'http://127.0.0.1:5001'

def login(client_code='demo', password='demo'):
    try:
        r = requests.post(f"{API_BASE}/login", json={"client_code": client_code, "password": password}, timeout=5)
        r.raise_for_status()
        return r.json()
    except RequestException as e:
        print('Login failed (network):', e)
        return None

def get_quote(symbol='NIFTY', count=100):
    try:
        params = {"symbol": symbol, "count": count}
        r = requests.get(f"{API_BASE}/quote", params=params, timeout=8)
        r.raise_for_status()
        return r.json()
    except RequestException as e:
        print('get_quote failed (network):', e)
        return None

def place_order(payload: dict):
    try:
        r = requests.post(f"{API_BASE}/place_order", json=payload, timeout=5)
        r.raise_for_status()
        return r.json()
    except RequestException as e:
        print('place_order failed:', e)
        return None

def normalize_candles(payload):
    if not payload:
        return pd.DataFrame(columns=['open','high','low','close'])
    data = payload.get('data') if isinstance(payload, dict) and 'data' in payload else (payload if isinstance(payload, list) else None)
    if not data:
        return pd.DataFrame(columns=['open','high','low','close'])
    df = pd.DataFrame(data)
    if 'datetime' in df.columns:
        df['datetime'] = pd.to_datetime(df['datetime'], errors='coerce')
        if df['datetime'].notna().all():
            df = df.set_index('datetime')
    if 'close' in df.columns:
        if 'open' not in df.columns:
            df['open'] = df['close'].shift(1).fillna(df['close'])
        if 'high' not in df.columns:
            df['high'] = df[['open','close']].max(axis=1) + (df['close'] * 0.001).abs()
        if 'low' not in df.columns:
            df['low'] = df[['open','close']].min(axis=1) - (df['close'] * 0.001).abs()
        return df[['open','high','low','close']].copy()
    if 'price' in df.columns:
        df['close'] = df['price']
        df['open'] = df['close'].shift(1).fillna(df['close'])
        df['high'] = df[['open','close']].max(axis=1) + (df['close'] * 0.001).abs()
        df['low']  = df[['open','close']].min(axis=1) - (df['close'] * 0.001).abs()
        return df[['open','high','low','close']].copy()
    numeric_cols = df.select_dtypes(include=['number']).columns.tolist()
    if numeric_cols:
        col = numeric_cols[0]
        df['close'] = df[col]
        df['open'] = df['close'].shift(1).fillna(df['close'])
        df['high'] = df[['open','close']].max(axis=1) + (df['close'] * 0.001).abs()
        df['low']  = df[['open','close']].min(axis=1) - (df['close'] * 0.001).abs()
        return df[['open','high','low','close']].copy()
    return pd.DataFrame(columns=['open','high','low','close'])

def compute_indicators(df: pd.DataFrame):
    if df.empty or 'close' not in df.columns:
        print('No data for indicators')
        return df
    out = df.copy()
    out['sma_20'] = out['close'].rolling(window=20, min_periods=1).mean()
    out['sma_50'] = out['close'].rolling(window=50, min_periods=1).mean()
    out['ema_20'] = out['close'].ewm(span=20, adjust=False).mean()
    return out

def main():
    print('Starting patched trading bot (demo) against:', API_BASE)
    res = login()
    if not res:
        print('Login failed, exiting')
        return
    print('Login response:', res)

    q = get_quote(symbol='NIFTY', count=120)
    if not q:
        print('Quote fetch failed or returned nothing. Exiting.')
        return

    df = normalize_candles(q)
    if df.empty:
        print('Normalized dataframe empty — nothing to compute.')
        return

    df_ind = compute_indicators(df)
    print('Latest prices and indicators:')
    print(df_ind.tail(5).to_string())

    last_close = df_ind['close'].iloc[-1]
    order_payload = {'symbol': 'NIFTY', 'type': 'CE', 'strike': int(round(last_close)), 'qty': 1}
    print('Placing demo order:', order_payload)
    order_res = place_order(order_payload)
    print('Place order response:', order_res)

if __name__ == '__main__':
    main()
