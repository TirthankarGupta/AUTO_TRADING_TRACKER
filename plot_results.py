#!/usr/bin/env python3
"""
plot_results.py (improved version)
"""

import os
import sys
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.ticker import FuncFormatter

# Config
INPUT_CSV = os.path.join("data", "backtest_results.csv")
OUT_DIR = os.path.join("data", "plots")
PNG_DPI = 180


def ensure_out_dir(path: str):
    os.makedirs(path, exist_ok=True)


def load_results(path: str) -> pd.DataFrame:
    if not os.path.exists(path):
        raise SystemExit(f"ERROR: results file not found: {path}")

    df = pd.read_csv(path, low_memory=False)
    if df.empty:
        raise SystemExit("ERROR: results CSV is empty.")

    df.columns = [c.strip().lower() for c in df.columns]

    if "exit_time" in df.columns:
        df["exit_time"] = pd.to_datetime(df["exit_time"], errors="coerce")
    else:
        raise SystemExit("ERROR: backtest_results.csv must contain 'exit_time' column")

    if "pnl" not in df.columns:
        raise SystemExit("ERROR: backtest_results.csv must contain 'pnl' column")

    df["pnl"] = pd.to_numeric(df["pnl"], errors="coerce").fillna(0.0)
    df = df[df["exit_time"].notna()].copy()
    df.sort_values("exit_time", inplace=True)
    df.reset_index(drop=True, inplace=True)
    return df


def compute_equity_and_drawdown(df: pd.DataFrame) -> pd.DataFrame:
    df2 = df.copy()
    df2["cum_pnl"] = df2["pnl"].cumsum()
    df2["running_max"] = df2["cum_pnl"].cummax()
    df2["drawdown"] = df2["cum_pnl"] - df2["running_max"]
    return df2


def format_currency(x, pos):
    return f"{x:,.0f}"  # force integer with commas


def plot_equity_curve(df: pd.DataFrame, out_dir: str):
    fig, ax = plt.subplots(figsize=(12, 5))
    ax.plot(df["exit_time"], df["cum_pnl"], lw=1.8, label="Equity Curve", color="blue")

    ax.set_title("Equity Curve (Cumulative P&L)")
    ax.set_xlabel("Exit Time")
    ax.set_ylabel("Cumulative P&L")
    ax.grid(alpha=0.35)

    # Format x-axis (daily ticks, nice labels)
    locator = mdates.AutoDateLocator(maxticks=10)
    ax.xaxis.set_major_locator(locator)
    ax.xaxis.set_major_formatter(mdates.ConciseDateFormatter(locator))

    # Format y-axis
    ax.yaxis.set_major_formatter(FuncFormatter(format_currency))

    ax.legend(loc="upper left")
    plt.xticks(rotation=30, ha="right")
    plt.tight_layout()
    out = os.path.join(out_dir, "equity_curve.png")
    plt.savefig(out, dpi=PNG_DPI)
    print("Saved equity curve:", out)
    plt.show()
    plt.close()


def main():
    ensure_out_dir(OUT_DIR)
    df = load_results(INPUT_CSV)
    df_eq = compute_equity_and_drawdown(df)
    plot_equity_curve(df_eq, OUT_DIR)


if __name__ == "__main__":
    main()
