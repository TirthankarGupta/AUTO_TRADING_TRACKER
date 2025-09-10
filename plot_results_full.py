#!/usr/bin/env python3
"""
plot_results_full.py

One self-contained, fail-safe plotting script that:
 - loads data/backtest_results.csv (or a file passed on the CLI)
 - computes cumulative equity & drawdown
 - plots equity curve (clean x/y formatting)
 - annotates biggest win & biggest loss
 - plots drawdown, pnl distribution, and pnl scatter
 - saves PNGs to data/plots/

Usage (from project root, venv activated):
    python plot_results_full.py                # uses data/backtest_results.csv
or
    python plot_results_full.py data/my_results.csv
"""

from __future__ import annotations
import os
import sys
from typing import Optional
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.ticker import FuncFormatter

# ---------- Config ----------
DEFAULT_INPUT = os.path.join("data", "backtest_results.csv")
OUT_DIR = os.path.join("data", "plots")
PNG_DPI = 150
# ----------------------------

def ensure_out_dir(path: str) -> None:
    os.makedirs(path, exist_ok=True)

def load_results(path: str) -> pd.DataFrame:
    if not os.path.exists(path):
        raise SystemExit(f"ERROR: file not found: {path}")
    df = pd.read_csv(path, low_memory=False)
    if df.empty:
        raise SystemExit("ERROR: results CSV is empty.")
    # normalize columns
    df.columns = [c.strip().lower() for c in df.columns]
    # required columns
    if "pnl" not in df.columns:
        raise SystemExit("ERROR: results CSV must contain a 'pnl' column.")
    # datetime column can be 'exit_time' or 'datetime' or first column
    dt_col: Optional[str] = None
    for candidate in ("exit_time", "datetime", "time", "date"):
        if candidate in df.columns:
            dt_col = candidate
            break
    if dt_col is None:
        # fallback: first column if it looks like a datetime
        first = df.columns[0]
        # try parse first column to datetime to check
        try:
            parsed = pd.to_datetime(df[first], errors="coerce")
            if parsed.notna().any():
                dt_col = first
        except Exception:
            dt_col = None
    if dt_col is None:
        raise SystemExit("ERROR: CSV must contain a datetime column (exit_time/datetime/time/date or first column).")

    # parse datetime safely
    df[dt_col] = pd.to_datetime(df[dt_col], errors="coerce")
    if df[dt_col].isna().all():
        raise SystemExit(f"ERROR: Could not parse datetime in column '{dt_col}'.")
    # rename to exit_time for internal consistency
    df.rename(columns={dt_col: "exit_time"}, inplace=True)

    # ensure numeric pnl and drop rows without exit_time
    df["pnl"] = pd.to_numeric(df["pnl"], errors="coerce").fillna(0.0)
    df = df[df["exit_time"].notna()].copy()
    df.sort_values("exit_time", inplace=True)
    df.reset_index(drop=True, inplace=True)
    return df

def compute_stats(df: pd.DataFrame) -> pd.DataFrame:
    df2 = df.copy()
    df2["cum_pnl"] = df2["pnl"].cumsum()
    df2["running_max"] = df2["cum_pnl"].cummax()
    df2["drawdown"] = df2["cum_pnl"] - df2["running_max"]
    return df2

def format_currency_int(x, pos):
    # integer currency with sign and commas
    return f"{int(x):+,d}"

def plot_equity(df: pd.DataFrame, out_dir: str) -> str:
    fig, ax = plt.subplots(figsize=(12, 5))
    ax.plot(df["exit_time"], df["cum_pnl"], lw=1.8, label="Equity Curve", color="#1f77b4")

    # annotate best and worst trades (by pnl)
    if "pnl" in df.columns and not df.empty:
        best_idx = df["pnl"].idxmax()
        worst_idx = df["pnl"].idxmin()
        for idx, label, color in (
            (best_idx, "Biggest Win", "green"),
            (worst_idx, "Biggest Loss", "red"),
        ):
            try:
                x = df.at[idx, "exit_time"]
                y = df.at[idx, "cum_pnl"]
                val = df.at[idx, "pnl"]
                ax.scatter([x], [y], s=60, color=color, zorder=5, edgecolor="k")
                ax.annotate(f"{label}\nPNL: {val:.2f}",
                            xy=(x, y), xytext=(10, 8 if color=="green" else -18),
                            textcoords="offset points", fontsize=9,
                            bbox=dict(boxstyle="round,pad=0.2", fc="white", alpha=0.8),
                            arrowprops=dict(arrowstyle="->", color=color, lw=0.8))
            except Exception:
                # fail safe - ignore annotation errors
                pass

    ax.set_title("Equity Curve (Cumulative P&L)")
    ax.set_xlabel("Exit Time")
    ax.set_ylabel("Cumulative P&L")
    ax.grid(alpha=0.3)

    # x formatting - auto locator + concise formatter
    locator = mdates.AutoDateLocator(maxticks=10)
    ax.xaxis.set_major_locator(locator)
    ax.xaxis.set_major_formatter(mdates.ConciseDateFormatter(locator))

    # y formatting - integer commas
    ax.yaxis.set_major_formatter(FuncFormatter(format_currency_int))

    ax.legend(loc="upper left")
    plt.xticks(rotation=25, ha="right")
    plt.tight_layout()

    out = os.path.join(out_dir, "equity_curve.png")
    fig.savefig(out, dpi=PNG_DPI)
    plt.show()
    plt.close(fig)
    return out

def plot_drawdown(df: pd.DataFrame, out_dir: str) -> str:
    fig, ax = plt.subplots(figsize=(12, 3))
    ax.fill_between(df["exit_time"], df["drawdown"], 0, color="#d62728", alpha=0.6)
    ax.set_title("Running Drawdown")
    ax.set_xlabel("Exit Time")
    ax.set_ylabel("Drawdown")
    ax.grid(alpha=0.3)
    ax.yaxis.set_major_formatter(FuncFormatter(format_currency_int))
    locator = mdates.AutoDateLocator(maxticks=8)
    ax.xaxis.set_major_locator(locator)
    ax.xaxis.set_major_formatter(mdates.ConciseDateFormatter(locator))
    plt.tight_layout()
    out = os.path.join(out_dir, "drawdown.png")
    fig.savefig(out, dpi=PNG_DPI)
    plt.show()
    plt.close(fig)
    return out

def plot_pnl_distribution(df: pd.DataFrame, out_dir: str) -> str:
    fig, axes = plt.subplots(1, 2, figsize=(12, 4))
    axes[0].hist(df["pnl"].dropna(), bins=30, alpha=0.8)
    axes[0].set_title("P&L Distribution")
    axes[0].set_xlabel("Trade P&L")
    axes[0].grid(alpha=0.25)

    # scatter P&L vs time (small)
    axes[1].scatter(df["exit_time"], df["pnl"], s=18, alpha=0.8)
    axes[1].set_title("Trade P&L by Exit Time")
    axes[1].set_xlabel("Exit Time")
    axes[1].set_ylabel("P&L")
    locator = mdates.AutoDateLocator(maxticks=6)
    axes[1].xaxis.set_major_locator(locator)
    axes[1].xaxis.set_major_formatter(mdates.ConciseDateFormatter(locator))
    axes[1].yaxis.set_major_formatter(FuncFormatter(format_currency_int))
    axes[1].grid(alpha=0.25)

    plt.tight_layout()
    out = os.path.join(out_dir, "pnl_dist_and_scatter.png")
    fig.savefig(out, dpi=PNG_DPI)
    plt.show()
    plt.close(fig)
    return out

def print_summary(df: pd.DataFrame) -> None:
    total_trades = len(df)
    total_pnl = float(df["pnl"].sum())
    avg_pnl = float(df["pnl"].mean()) if total_trades > 0 else 0.0
    wins = df[df["pnl"] > 0]["pnl"]
    win_rate = float(len(wins) / total_trades) if total_trades > 0 else 0.0
    max_dd = int(df["drawdown"].min()) if "drawdown" in df.columns else 0

    print("\nBacktest Summary:")
    print(f"  total_trades: {total_trades}")
    print(f"  total_pnl: {total_pnl:.6f}")
    print(f"  avg_pnl: {avg_pnl:.6f}")
    print(f"  win_rate: {win_rate:.4f}")
    print(f"  max_drawdown: {max_dd}")

def main():
    # accept optional path argument
    path = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_INPUT
    ensure_out_dir(OUT_DIR)
    df = load_results(path)
    df_eq = compute_stats(df)
    print_summary(df_eq)

    try:
        print("Plotting equity curve...")
        p1 = plot_equity(df_eq, OUT_DIR)
        print("Plot saved:", p1)
    except Exception as e:
        print("Warning: equity plot failed:", e)

    try:
        p2 = plot_drawdown(df_eq, OUT_DIR)
        print("Plot saved:", p2)
    except Exception as e:
        print("Warning: drawdown plot failed:", e)

    try:
        p3 = plot_pnl_distribution(df_eq, OUT_DIR)
        print("Plot saved:", p3)
    except Exception as e:
        print("Warning: pnl distribution plot failed:", e)

    print("\nAll done. Plots saved under:", OUT_DIR)

if __name__ == "__main__":
    main()
