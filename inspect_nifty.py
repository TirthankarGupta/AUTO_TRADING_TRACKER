import pandas as pd
import numpy as np
from pathlib import Path

p = Path("data/nifty_1min.csv")
if not p.exists():
    raise SystemExit("File not found: data/nifty_1min.csv")

# Try reading with yfinance-style multi-header first
try:
    df_try = pd.read_csv(p, header=[0,1])
    if isinstance(df_try.columns, pd.MultiIndex):
        cols = []
        for a, b in df_try.columns:
            a = str(a).strip()
            b = str(b).strip()
            if a.lower() == "price" and b.lower() == "datetime":
                cols.append("datetime")
            elif a and a.lower() != "price":
                cols.append(a)
            elif b:
                cols.append(b)
            else:
                cols.append(f"{a}_{b}")
        df_try.columns = cols
        df = df_try
    else:
        df = df_try
except Exception:
    df = pd.read_csv(p)

# Normalize column names
df.columns = [str(c).strip() for c in df.columns]

# Rename datetime-like first column if needed
if any(c.lower() == "datetime" for c in df.columns):
    dt_col = next(c for c in df.columns if c.lower() == "datetime")
    df.rename(columns={dt_col:"datetime"}, inplace=True)
else:
    # fallback: assume first col is datetime if parseable
    first = df.columns[0]
    try:
        parsed = pd.to_datetime(df[first])
        df.rename(columns={first:"datetime"}, inplace=True)
    except Exception:
        pass

# Ensure column names to lower-case standard
mapping = {}
for c in df.columns:
    lc = c.lower()
    if lc == "open": mapping[c] = "open"
    if lc == "high": mapping[c] = "high"
    if lc == "low": mapping[c] = "low"
    if lc == "close": mapping[c] = "close"
    if lc == "volume": mapping[c] = "volume"
if mapping:
    df.rename(columns=mapping, inplace=True)

# Force numeric on ohlcv
for col in ["open","high","low","close","volume"]:
    if col in df.columns:
        df[col] = pd.to_numeric(df[col], errors="coerce")

# Parse datetime
if "datetime" in df.columns:
    df["datetime"] = pd.to_datetime(df["datetime"], errors="coerce")

print("COLUMNS:", df.columns.tolist())
print("\nDTYPES:\n", df.dtypes)
print("\nHEAD (first 6 rows):\n", df.head(6).to_string(index=False))

# Quick stats about NaNs in numeric cols
print("\nNaN counts in OHLCV:")
for c in ["open","high","low","close","volume"]:
    print(f" {c}: {df[c].isna().sum() if c in df.columns else 'MISSING'}")

# Compute EMA crossovers if close exists
if "close" in df.columns and df["close"].notna().sum() > 10:
    ema9 = df["close"].ewm(span=9, adjust=False).mean()
    ema21 = df["close"].ewm(span=21, adjust=False).mean()
    crosses = ((ema9 > ema21) & (ema9.shift(1) <= ema21.shift(1))).sum()
    print("\nEMA9>EMA21 crossups count:", crosses)
else:
    print("\nNot enough numeric 'close' data to compute EMA crossovers.")
