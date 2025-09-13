# clean_nifty.py - robust cleaner that finds datetime even if it's the CSV index or multi-header
import os, sys
import pandas as pd
import numpy as np

IN = "data/nifty_1min.csv"
OUT = "data/nifty_1min.cleaned.csv"

def try_read_basic(path):
    try:
        return pd.read_csv(path)
    except Exception:
        return None

def try_read_indexed(path):
    try:
        df = pd.read_csv(path, index_col=0, parse_dates=True)
        if isinstance(df.index, pd.DatetimeIndex) and len(df.index) > 0:
            df = df.reset_index()
            # ensure name is 'datetime'
            df.columns = [str(c).strip() for c in df.columns]
            if df.columns[0].lower() not in ("datetime", "date", "timestamp"):
                df = df.rename(columns={df.columns[0]: "datetime"})
            return df
    except Exception:
        return None

def try_read_multi(path):
    try:
        df = pd.read_csv(path, header=[0,1])
        if isinstance(df.columns, pd.MultiIndex):
            cols = []
            for a,b in df.columns:
                a_s = "" if pd.isna(a) else str(a).strip()
                b_s = "" if pd.isna(b) else str(b).strip()
                # prefer the second if first is empty
                if a_s and b_s:
                    cols.append(f"{a_s} {b_s}".strip())
                elif a_s:
                    cols.append(a_s)
                elif b_s:
                    cols.append(b_s)
                else:
                    cols.append("")
            df.columns = cols
        return df
    except Exception:
        return None

def find_datetime_col(df):
    # look for obvious names
    for c in df.columns:
        if str(c).strip().lower() in ("datetime", "date", "timestamp", "time"):
            return c
    # heuristics: first column with many parseable datetimes
    for c in df.columns[:3]:  # check first up to 3 columns
        try:
            parsed = pd.to_datetime(df[c], errors="coerce")
            if parsed.notna().sum() >= max(1, len(parsed)//10):
                return c
        except Exception:
            continue
    return None

def main():
    path = IN
    if not os.path.exists(path):
        print("Input CSV not found:", path); sys.exit(1)

    df = try_read_basic(path)
    if df is None:
        df = try_read_indexed(path)
    if df is None:
        df = try_read_multi(path)
    if df is None:
        print("Unable to read file with basic, indexed or multi-header methods."); sys.exit(1)

    print("Raw columns:", list(df.columns))

    # find datetime column (or index case was already handled by try_read_indexed)
    dt_col = find_datetime_col(df)
    if dt_col is None:
        # as a last resort, try reading index as datetime again
        df2 = try_read_indexed(path)
        if df2 is not None:
            df = df2
            dt_col = find_datetime_col(df)
    if dt_col is None:
        print("No datetime column found. Detected columns:", list(df.columns))
        raise ValueError("CSV must contain a datetime-like column or have a datetime index")

    # normalize name and parse
    if dt_col != "datetime":
        df = df.rename(columns={dt_col: "datetime"})
    df["datetime"] = pd.to_datetime(df["datetime"], errors="coerce")

    # lowercase names
    df.columns = [str(c).strip().lower() for c in df.columns]

    # standardize alt names
    alt = {"adj close":"close", "last":"close", "vol":"volume"}
    df.rename(columns={k:v for k,v in alt.items() if k in df.columns}, inplace=True)

    # if ticker or price header noise exists, drop it if not needed
    for col in list(df.columns):
        if col.lower() == "ticker" or col.lower() == "price":
            # keep if there's only one other column set; otherwise drop
            try:
                if "open" not in df.columns or "close" not in df.columns:
                    pass
                df = df.drop(columns=[col])
            except Exception:
                pass

    # ensure ohlc columns exist or try to map with common variants
    required = ["open","high","low","close"]
    col_map = {c:c for c in df.columns}
    # map capitalized variants already lowercased above
    missing = [r for r in required if r not in df.columns]
    if missing:
        print("Missing required columns after normalization:", missing)
        print("Columns present:", list(df.columns))
        raise ValueError("Missing OHLC columns after normalization")

    # coerce numeric
    for col in ["open","high","low","close","volume"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    # drop rows with invalid datetime or missing price
    before = len(df)
    df = df.dropna(subset=["datetime","open","high","low","close"])
    after = len(df)
    print(f"Dropped {before-after} invalid rows; kept {after} rows.")

    # sort by datetime & save
    df = df.sort_values("datetime").reset_index(drop=True)
    outdir = os.path.dirname(OUT)
    if outdir:
        os.makedirs(outdir, exist_ok=True)
    df.to_csv(OUT, index=False)
    print("Saved cleaned CSV to:", OUT)
    print("Clean columns:", list(df.columns))
    print("First 5 rows:
", df.head().to_string(index=False))

if __name__ == "__main__":
    main()
