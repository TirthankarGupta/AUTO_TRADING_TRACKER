#!/usr/bin/env python3
"""
backtest.py â€” revised: EMA crossover primary, VWAP/RSI supportive (not blocking)

Usage:
    python backtest.py <csv_path>

Outputs:
 - data/backtest_results.csv  (all closed trades)
 - data/trades_journal.csv    (appended per-trade rows with entry_reason & exit_reason)
"""
from __future__ import annotations
import os
import sys
import csv
from dataclasses import dataclass
from typing import Optional, List, Tuple
import pandas as pd
import numpy as np

# -------------------------
# Helpers
# -------------------------
def ensure_dir(path: str) -> None:
    if path:
        os.makedirs(path, exist_ok=True)

def read_csv_robust(path: str) -> pd.DataFrame:
    """Try to read CSV in multiple ways (plain, index-as-datetime, multi-header)."""
    if not os.path.exists(path):
        raise FileNotFoundError(f"File not found: {path}")

    # 1) plain read
    try:
        df = pd.read_csv(path)
    except Exception:
        df = None

    # 2) try index-as-datetime
    if df is None:
        try:
            tmp = pd.read_csv(path, index_col=0, parse_dates=True)
            if isinstance(tmp.index, pd.DatetimeIndex) and len(tmp.index) > 0:
                df = tmp.reset_index()
        except Exception:
            df = None

    # 3) try multi-header flatten
    if df is None:
        try:
            tmp = pd.read_csv(path, header=[0,1])
            if isinstance(tmp.columns, pd.MultiIndex):
                cols = []
                for a,b in tmp.columns:
                    a_s = "" if pd.isna(a) else str(a).strip()
                    b_s = "" if pd.isna(b) else str(b).strip()
                    if a_s and b_s:
                        cols.append(f"{a_s} {b_s}")
                    elif a_s:
                        cols.append(a_s)
                    elif b_s:
                        cols.append(b_s)
                    else:
                        cols.append("")
                tmp.columns = cols
            df = tmp
        except Exception:
            raise ValueError("Unable to read CSV (tried plain, index-as-datetime and multi-header).")

    # normalize columns
    df.columns = [str(c).strip() for c in df.columns]

    # find datetime column
    dt_col = None
    for c in df.columns:
        if str(c).strip().lower() in ("datetime", "date", "timestamp", "time"):
            dt_col = c; break
    if dt_col is None:
        # try first column heuristic
        first = df.columns[0]
        try:
            parsed = pd.to_datetime(df[first], errors="coerce")
            if parsed.notna().sum() >= max(1, len(parsed)//10):
                dt_col = first
        except Exception:
            dt_col = None

    if dt_col is None:
        raise ValueError(f"CSV must contain a datetime column (detected columns: {list(df.columns)})")

    # rename to 'datetime' and parse
    if dt_col != "datetime":
        df = df.rename(columns={dt_col: "datetime"})
    df["datetime"] = pd.to_datetime(df["datetime"], errors="coerce")

    # lowercase columns and canonicalize names
    df.columns = [c.lower() for c in df.columns]
    alt = {"adj close":"close", "last":"close", "vol":"volume", "price":"close"}
    df.rename(columns={k:v for k,v in alt.items() if k in df.columns}, inplace=True)

    # require ohlc
    for r in ("open","high","low","close"):
        if r not in df.columns:
            raise ValueError(f"Missing required column '{r}' in CSV (columns: {list(df.columns)})")

    # volume optional, fill zeros if absent
    if "volume" not in df.columns:
        df["volume"] = 0

    # coerce numeric
    for col in ("open","high","low","close","volume"):
        df[col] = pd.to_numeric(df[col], errors="coerce")

    # drop rows with missing core values
    before = len(df)
    df = df.dropna(subset=["datetime","open","high","low","close"]).sort_values("datetime").reset_index(drop=True)
    after = len(df)

    if after == 0:
        raise ValueError("No valid rows after cleaning CSV.")

    print(f"Loaded {after} rows after cleaning. Columns: {list(df.columns)}")
    if before != after:
        print(f"Dropped {before-after} rows with missing values.")

    return df

# -------------------------
# Indicators
# -------------------------
def add_indicators(df: pd.DataFrame) -> pd.DataFrame:
    d = df.copy()
    d["ema9"]  = d["close"].ewm(span=9, adjust=False).mean()
    d["ema21"] = d["close"].ewm(span=21, adjust=False).mean()

    # RSI14 (Wilder-like)
    delta = d["close"].diff()
    up = delta.clip(lower=0)
    down = -delta.clip(upper=0)
    roll_up = up.ewm(alpha=1/14, adjust=False).mean()
    roll_down = down.ewm(alpha=1/14, adjust=False).mean()
    rs = roll_up / roll_down.replace(0, np.nan)
    d["rsi14"] = 100 - (100 / (1 + rs))
    d["rsi14"] = d["rsi14"].fillna(50)

    # VWAP
    typical = (d["high"] + d["low"] + d["close"]) / 3.0
    cum_typ_vol = (typical * d["volume"]).cumsum()
    cum_vol = d["volume"].cumsum()
    with np.errstate(divide="ignore", invalid="ignore"):
        vwap = cum_typ_vol / cum_vol
    d["vwap"] = vwap.fillna(method="ffill").fillna(d["close"])

    d["vol_avg_20"] = d["volume"].rolling(window=20, min_periods=1).mean()
    return d

# -------------------------
# Trade dataclass & journal
# -------------------------
@dataclass
class Trade:
    entry_time: pd.Timestamp
    entry_price: float
    direction: str = "LONG"
    exit_time: Optional[pd.Timestamp] = None
    exit_price: Optional[float] = None
    pnl: Optional[float] = None
    entry_reason: Optional[str] = None
    exit_reason: Optional[str] = None

    def close(self, time: pd.Timestamp, price: float, reason: Optional[str]):
        self.exit_time = time
        self.exit_price = price
        if self.direction == "LONG":
            self.pnl = self.exit_price - self.entry_price
        else:
            self.pnl = self.entry_price - self.exit_price
        self.exit_reason = reason

    def to_dict(self):
        return {
            "entry_time": self.entry_time,
            "entry_price": self.entry_price,
            "exit_time": self.exit_time,
            "exit_price": self.exit_price,
            "direction": self.direction,
            "pnl": self.pnl,
            "pnl_percent": (self.pnl / self.entry_price) if (self.pnl is not None and self.entry_price) else None,
            "entry_reason": self.entry_reason,
            "exit_reason": self.exit_reason
        }

def append_journal(row: dict, path: str):
    ensure_dir(os.path.dirname(path) or ".")
    exists = os.path.exists(path)
    with open(path, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(row.keys()))
        if not exists:
            writer.writeheader()
        writer.writerow(row)

# -------------------------
# Backtest engine (EMA primary, VWAP/RSI supportive)
# -------------------------
def run_backtest(df: pd.DataFrame,
                 tp: float = 0.005,
                 sl: float = 0.0025,
                 vol_window: int = 20,
                 out_dir: str = "data") -> Tuple[pd.DataFrame, dict, str]:
    d = add_indicators(df.copy())
    d["vol_avg"] = d["volume"].rolling(window=vol_window, min_periods=1).mean()

    trades: List[Trade] = []
    position: Optional[Trade] = None

    for i in range(1, len(d)):
        prev = d.iloc[i-1]
        row  = d.iloc[i]

        # primary entry trigger: EMA9 crossing above EMA21
        ema_cross_up = (prev["ema9"] <= prev["ema21"]) and (row["ema9"] > row["ema21"])
        ema_cross_down = (prev["ema9"] >= prev["ema21"]) and (row["ema9"] < row["ema21"])

        # supportive signals
        price_above_vwap = float(row["close"]) > float(row["vwap"])
        rsi_supportive = row["rsi14"] is not None and row["rsi14"] < 70
        vol_ok = float(row["volume"]) >= max(1.0, 0.5 * float(row["vol_avg"]))

        entry_reasons = []
        if price_above_vwap:
            entry_reasons.append("VWAP_OK")
        if rsi_supportive:
            entry_reasons.append("RSI_OK")
        if vol_ok:
            entry_reasons.append("VOL_OK")

        # ENTRY: EMA cross up -> open LONG (supportive flags recorded)
        if position is None and ema_cross_up:
            entry_reason = "EMA_CROSS_UP"
            if entry_reasons:
                entry_reason += "+" + "+".join(entry_reasons)
            position = Trade(entry_time=row["datetime"], entry_price=float(row["close"]), direction="LONG")
            position.entry_reason = entry_reason
            trades.append(position)

        # MANAGE position if open
        if position is not None:
            cur = float(row["close"])
            exit_reason = None
            # take profit
            if cur >= position.entry_price * (1 + tp):
                exit_reason = "TP"
            # stop loss
            elif cur <= position.entry_price * (1 - sl):
                exit_reason = "SL"
            # VWAP break (price falling below VWAP)
            elif cur < float(row["vwap"]):
                exit_reason = "VWAP_BREAK"
            # EMA cross down
            elif ema_cross_down:
                exit_reason = "EMA_CROSS_DOWN"

            if exit_reason:
                position.close(time=row["datetime"], price=cur, reason=exit_reason)
                append_journal(position.to_dict(), os.path.join(out_dir, "trades_journal.csv"))
                position = None

    # EOD close any open position
    if position is not None and position.exit_time is None:
        last = d.iloc[-1]
        position.close(time=last["datetime"], price=float(last["close"]), reason="EOD_CLOSE")
        append_journal(position.to_dict(), os.path.join(out_dir, "trades_journal.csv"))
        position = None

    closed = [t.to_dict() for t in trades if t.exit_time is not None]
    results = pd.DataFrame(closed)

    if results.empty:
        summary = {"total_trades": 0, "total_pnl": 0.0, "avg_pnl": 0.0, "win_rate": 0.0}
    else:
        results["pnl_percent"] = results["pnl"] / results["entry_price"]
        summary = {
            "total_trades": int(len(results)),
            "total_pnl": float(results["pnl"].sum()),
            "avg_pnl": float(results["pnl"].mean()),
            "win_rate": float((results["pnl"] > 0).mean())
        }

    ensure_dir(out_dir)
    out_path = os.path.join(out_dir, "backtest_results.csv")
    results.to_csv(out_path, index=False)
    return results, summary, out_path

# -------------------------
# Main CLI
# -------------------------
def main(argv=None):
    if argv is None:
        argv = sys.argv[1:]
    if not argv:
        print("Usage: python backtest.py <data.csv>")
        sys.exit(1)

    csv_path = argv[0]
    try:
        df = read_csv_robust(csv_path)
        results, summary, outp = run_backtest(df, tp=0.005, sl=0.0025, vol_window=20, out_dir="data")
        print("
Backtest Summary:")
        for k,v in summary.items():
            print(f"  {k}: {v}")
        print(f"Saved trade results to: {outp}")
        if not results.empty:
            print("
Sample trades:")
            print(results.head(10).to_string(index=False))
    except Exception as exc:
        print("Error during backtest:", str(exc))
        sys.exit(1)

if __name__ == "__main__":
    main()
