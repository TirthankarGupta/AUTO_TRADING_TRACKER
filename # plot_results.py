# plot_results.py
# Usage: python plot_results.py
# Reads: data/backtest_results.csv
# Writes: data/plots/equity_curve.png, data/plots/pnl_histogram.png, data/plots/trades_scatter.png

import os
import sys
import pandas as pd
import matplotlib.pyplot as plt

INPUT = "data/backtest_results.csv"
OUT_DIR = "data/plots"

def load_results(path):
    if not os.path.exists(path):
        print("Backtest results not found:", path)
        sys.exit(1)
    df = pd.read_csv(path, parse_dates=["entry_time","exit_time"], infer_datetime_format=True)
    if df.empty:
        print("Backtest results file is empty.")
        sys.exit(1)
    return df

def make_equity_curve(df):
    # Ensure pnl column exists
    if "pnl" not in df.columns:
        raise ValueError("pnl column not found in results CSV")
    df_sorted = df.sort_values("exit_time").reset_index(drop=True).copy()
    df_sorted["cum_pnl"] = df_sorted["pnl"].cumsum()
    return df_sorted

def plot_equity(df_eq, out_dir):
    plt.figure(figsize=(10,5))
    plt.plot(df_eq["exit_time"], df_eq["cum_pnl"], linewidth=1.5, marker=None)
    plt.grid(alpha=0.3)
    plt.xlabel("Exit Time")
    plt.ylabel("Cumulative P&L")
    plt.title("Equity Curve (Cumulative P&L)")
    plt.tight_layout()
    p = os.path.join(out_dir, "equity_curve.png")
    plt.savefig(p, dpi=200)
    print("Saved:", p)
    plt.show()
    plt.close()

def plot_pnl_hist(df, out_dir):
    plt.figure(figsize=(8,5))
    plt.hist(df["pnl"].dropna(), bins=30, edgecolor="black")
    plt.xlabel("Trade P&L")
    plt.ylabel("Count")
    plt.title("Distribution of Trade P&L")
    plt.tight_layout()
    p = os.path.join(out_dir, "pnl_histogram.png")
    plt.savefig(p, dpi=200)
    print("Saved:", p)
    plt.show()
    plt.close()

def plot_trade_scatter(df, out_dir):
    plt.figure(figsize=(10,4))
    sizes = (df["pnl"].abs() / (abs(df["pnl"]).max() if df["pnl"].abs().max() else 1)) * 80 + 10
    colors = ["green" if x>0 else "red" for x in df["pnl"]]
    plt.scatter(df["exit_time"], df["pnl"], s=sizes, c=colors, alpha=0.7)
    plt.axhline(0, color="black", linewidth=0.8)
    plt.xlabel("Exit Time")
    plt.ylabel("Trade P&L")
    plt.title("Trade P&L over Time (size ~ magnitude)")
    plt.tight_layout()
    p = os.path.join(out_dir, "trades_scatter.png")
    plt.savefig(p, dpi=200)
    print("Saved:", p)
    plt.show()
    plt.close()

def summary_stats(df):
    total = len(df)
    total_pnl = df["pnl"].sum()
    avg = df["pnl"].mean()
    wins = (df["pnl"]>0).sum()
    win_rate = wins/total if total else 0
    print("Summary stats:")
    print(f"  trades: {total}")
    print(f"  total pnl: {total_pnl:.6f}")
    print(f"  avg pnl: {avg:.6f}")
    print(f"  win rate: {win_rate:.2%}")

def main():
    ensure_dir = lambda p: os.makedirs(p, exist_ok=True)
    ensure_dir(OUT_DIR)
    df = load_results(INPUT)
    summary_stats(df)
    df_eq = make_equity_curve(df)
    plot_equity(df_eq, OUT_DIR)
    plot_pnl_hist(df, OUT_DIR)
    plot_trade_scatter(df_eq, OUT_DIR)
    print("All plots saved under:", OUT_DIR)

if __name__ == "__main__":
    main()
