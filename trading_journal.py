# trading_journal.py
"""
Trading Journal — BUY-only with lot_size support and editable Notes.

Run:
    streamlit run "C:\AUTO_TRADING_TRACKER\trading_journal.py"
"""
import io
from datetime import datetime
import pandas as pd
import numpy as np
import streamlit as st
import pytz

KOLKATA = pytz.timezone("Asia/Kolkata")

# ------------------------
# Helpers
# ------------------------
def parse_datetime(val):
    if pd.isna(val) or (isinstance(val, str) and val.strip() == ""):
        return pd.NaT
    try:
        ts = pd.to_datetime(val, errors="coerce")
        if pd.isna(ts):
            return pd.NaT
        # localize naive -> Kolkata, else convert
        if getattr(ts, "tzinfo", None) is None and getattr(ts, "tz", None) is None:
            try:
                return ts.tz_localize(KOLKATA)
            except Exception:
                try:
                    return KOLKATA.localize(ts.to_pydatetime())
                except Exception:
                    return pd.NaT
        else:
            try:
                return ts.tz_convert(KOLKATA)
            except Exception:
                return ts
    except Exception:
        return pd.NaT

def compute_pnl_units(row, default_lot_size):
    """Compute PnL using units = quantity (lots) * lot_size (units/lot)."""
    try:
        lots = float(row.get("quantity", 0.0))
        lot_size = float(row.get("lot_size", default_lot_size)) if not pd.isna(row.get("lot_size", np.nan)) else float(default_lot_size)
        units = lots * lot_size
        ep = float(row.get("entry_price", np.nan))
        xp = float(row.get("exit_price", np.nan))
        fees = float(row.get("fees", 0.0)) if not pd.isna(row.get("fees", np.nan)) else 0.0
        if np.isnan(ep) or np.isnan(xp) or units == 0:
            return np.nan
        return (xp - ep) * units - fees
    except Exception:
        return np.nan

def ensure_columns(df):
    required = [
        "trade_id", "symbol", "quantity",
        "lot_size", "entry_price", "exit_price",
        "entry_time", "exit_time",
        "fees", "notes"
    ]
    for c in required:
        if c not in df.columns:
            df[c] = np.nan
    return df

def fmt_dt_display(ts):
    if pd.isna(ts):
        return ""
    try:
        return ts.tz_convert(KOLKATA).strftime("%Y-%m-%d %H:%M:%S")
    except Exception:
        return str(ts)

# ------------------------
# Streamlit UI
# ------------------------
st.set_page_config(page_title="Trading Journal", layout="wide")
st.title("📒 Trading Journal — BUY-only (lot_size & editable notes)")

col1, col2 = st.columns([3,1])
with col1:
    uploaded = st.file_uploader("Upload trades CSV (headers: trade_id,symbol,quantity,entry_price,exit_price,entry_time,exit_time,fees,notes,lot_size optional)", type=["csv","txt"], accept_multiple_files=False)
    use_sample = st.checkbox("Use sample dataset if no upload", value=False)
with col2:
    initial_balance = st.number_input("Initial starting balance (₹)", value=100000.0, step=1000.0, format="%.2f")
    default_fees = st.number_input("Default per-trade fees (₹) if missing", value=0.0, step=1.0, format="%.2f")
    global_lot_size = st.number_input("Default lot size (units per lot)", value=75, step=1, help="Contract multiplier (e.g. 75 for NIFTY options)")

# ------------------------
# Sample data
# ------------------------
def sample_data():
    return pd.DataFrame([
        {"trade_id":1,"symbol":"NIFTY24SEP24700CE","quantity":1,"lot_size":75,"entry_price":20.0,"exit_price":45.0,"entry_time":"2025-09-01 09:17:00","exit_time":"2025-09-01 09:43:00","fees":15,"notes":"Breakout"},
        {"trade_id":2,"symbol":"NIFTY24SEP24800CE","quantity":2,"lot_size":75,"entry_price":12.0,"exit_price":7.0,"entry_time":"2025-09-01 10:05:00","exit_time":"2025-09-01 10:45:00","fees":10,"notes":"Volatile"},
        {"trade_id":3,"symbol":"BANKNIFTY24SEPXYZ","quantity":1,"lot_size":25,"entry_price":150.0,"exit_price":130.0,"entry_time":"2025-09-02 11:00:00","exit_time":"2025-09-02 11:40:00","fees":12,"notes":""},
        {"trade_id":4,"symbol":"NIFTY24SEP24700CE","quantity":2,"lot_size":75,"entry_price":30.0,"exit_price":50.0,"entry_time":"2025-09-02 13:05:00","exit_time":"2025-09-02 13:30:00","fees":8,"notes":"Momentum"}
    ])

# ------------------------
# Load data
# ------------------------
if uploaded:
    try:
        df_raw = pd.read_csv(uploaded)
        st.success(f"Loaded {len(df_raw)} rows from uploaded CSV.")
    except Exception as e:
        st.error(f"Failed to read CSV: {e}")
        st.stop()
elif use_sample or not uploaded:
    df_raw = sample_data()
    st.info("Using sample dataset. Upload your CSV to use real trades.")

if df_raw is None or df_raw.empty:
    st.warning("No trades loaded.")
    st.stop()

# Normalize header names to lower-case keys
df = df_raw.copy()
df.columns = [str(c).strip().lower() for c in df.columns]

# Ensure important columns exist
df = ensure_columns(df)

# Coerce numeric columns
df["quantity"] = pd.to_numeric(df.get("quantity", np.nan), errors="coerce").fillna(0)
df["lot_size"] = pd.to_numeric(df.get("lot_size", np.nan), errors="coerce").fillna(global_lot_size)
df["entry_price"] = pd.to_numeric(df.get("entry_price", np.nan), errors="coerce")
df["exit_price"] = pd.to_numeric(df.get("exit_price", np.nan), errors="coerce")
df["fees"] = pd.to_numeric(df.get("fees", np.nan), errors="coerce").fillna(default_fees)
df["notes"] = df.get("notes", "").astype(str)

# Parse datetimes
df["entry_time_parsed"] = df["entry_time"].apply(parse_datetime)
df["exit_time_parsed"]  = df["exit_time"].apply(parse_datetime)

# Display-friendly time strings
df["entry_time_display"] = df["entry_time_parsed"].apply(fmt_dt_display)
df["exit_time_display"]  = df["exit_time_parsed"].apply(fmt_dt_display)

# PnL using lot_size (units = quantity * lot_size)
df["pnl"] = df.apply(lambda r: compute_pnl_units(r, global_lot_size), axis=1)

# pct per trade uses entry_value = entry_price * units
def pct_trade_calc(r, default_lot_size):
    try:
        lots = float(r.get("quantity", 0.0))
        lot_size = float(r.get("lot_size", default_lot_size)) if not pd.isna(r.get("lot_size", np.nan)) else float(default_lot_size)
        units = lots * lot_size
        ep = float(r.get("entry_price", np.nan))
        pnl = float(r.get("pnl", np.nan)) if not pd.isna(r.get("pnl")) else np.nan
        if np.isnan(ep) or units == 0 or np.isnan(pnl):
            return np.nan
        entry_value = ep * units
        if entry_value == 0:
            return np.nan
        return pnl / entry_value * 100.0
    except Exception:
        return np.nan

df["pct_trade"] = df.apply(lambda r: pct_trade_calc(r, global_lot_size), axis=1)

# Sort by exit_time_parsed so realized trades are chronological
df = df.sort_values(by=["exit_time_parsed"], ascending=True, na_position="last").reset_index(drop=True)

# Preserve original index mapping for editing mapping back
df["__idx__"] = df.index

# Cumulative balance (realized only)
running = float(initial_balance)
cumulatives = []
for _, row in df.iterrows():
    if pd.notna(row.get("exit_price")) and pd.notna(row.get("exit_time_parsed")):
        pnl = 0.0 if pd.isna(row.get("pnl")) else float(row.get("pnl"))
        running += pnl
        cumulatives.append(running)
    else:
        cumulatives.append(running)
df["cumulative_balance"] = cumulatives

# Day & Date based on exit_time_parsed (for closed trades)
df["day"]  = df["exit_time_parsed"].dt.tz_convert(KOLKATA).dt.strftime("%A").fillna("")
df["date"] = df["exit_time_parsed"].dt.tz_convert(KOLKATA).dt.date

# ------------------------
# Editable ledger (notes)
# ------------------------
st.subheader("Per-trade ledger (editable Notes)")
# Build display ledger with required columns in the order requested
display_cols = [
    "day", "date", "entry_time_display", "exit_time_display",
    "symbol", "quantity", "lot_size", "entry_price", "exit_price",
    "pnl", "cumulative_balance", "notes", "__idx__"
]
display_cols = [c for c in display_cols if c in df.columns]

ledger = df[display_cols].copy()

# data_editor: allow editing only 'notes'
editable_columns = ["notes"] if "notes" in ledger.columns else []
disabled_cols = [c for c in ledger.columns if c not in editable_columns]
edited = st.data_editor(ledger, num_rows="dynamic", use_container_width=True, disabled=disabled_cols)

# If edited, allow applying edits back to df
if not edited.equals(ledger):
    st.info("Edits detected in ledger.")
    if st.button("Apply edits to ledger"):
        # Map edited rows back to df using __idx__
        for _, row in edited.iterrows():
            if "__idx__" in edited.columns:
                idx = int(row["__idx__"])
                if idx in df.index:
                    if "notes" in edited.columns:
                        df.at[idx, "notes"] = row.get("notes", df.at[idx, "notes"])
        st.success("Notes updated in journal (in-memory).")
        # Recompute export_df and rerun UI to reflect changes
        st.experimental_rerun()

# ------------------------
# Cumulative time series (closed trades)
# ------------------------
st.subheader("Cumulative balance time series (closed trades)")
closed = df[df["exit_time_parsed"].notna()].copy()
if closed.empty:
    st.info("No closed trades to show here.")
else:
    ts = closed[["exit_time_display","trade_id","symbol","quantity","lot_size","pnl","cumulative_balance","notes"]].copy()
    ts = ts.rename(columns={"exit_time_display":"exit_time"})
    st.dataframe(ts.sort_values("exit_time").reset_index(drop=True), use_container_width=True, height=300)

# ------------------------
# Daily summary
# ------------------------
st.subheader("Daily summary (realized)")
if not closed.empty:
    daily_rows = []
    prev_bal = float(initial_balance)
    for day in sorted(closed["date"].dropna().unique()):
        day_trades = closed[closed["date"] == day]
        day_pnl = day_trades["pnl"].sum(min_count=1)
        start_bal = prev_bal
        end_bal = float(day_trades["cumulative_balance"].dropna().iloc[-1]) if not day_trades["cumulative_balance"].dropna().empty else start_bal
        daily_pct = np.nan if start_bal == 0 else (end_bal - start_bal) / start_bal * 100.0
        daily_rows.append({
            "date": pd.to_datetime(day).date(),
            "start_balance": round(start_bal,2),
            "end_balance": round(end_bal,2),
            "daily_pnl": round(day_pnl,2),
            "daily_pct": round(daily_pct,4)
        })
        prev_bal = end_bal
    daily_df = pd.DataFrame(daily_rows)
    st.dataframe(daily_df, use_container_width=True)
else:
    st.info("No realized trades found; daily summary empty.")

# ------------------------
# Quick stats
# ------------------------
st.subheader("Quick stats")
total_realized = df["pnl"].sum(min_count=1)
num_realized = closed.shape[0]
win_rate = (closed["pnl"] > 0).sum() / max(1, closed["pnl"].notna().sum()) * 100.0 if num_realized>0 else np.nan
avg_pct = df["pct_trade"].dropna().mean() if df["pct_trade"].notna().any() else np.nan

st.write(f"Realized P&L: ₹ {total_realized:,.2f}")
st.write(f"Realized trades: {num_realized}")
st.write(f"Win rate (realized): {win_rate:.2f}%")
st.write(f"Average % P&L per trade: {avg_pct:.2f}%")

# ------------------------
# Export updated ledger & daily summary
# ------------------------
st.subheader("Export")
export_cols = [
    "trade_id","symbol","quantity","lot_size","entry_price","exit_price",
    "entry_time_display","exit_time_display","pnl","pct_trade","cumulative_balance","notes","fees"
]
export_cols = [c for c in export_cols if c in df.columns]
export_df = df[export_cols].copy().rename(columns={"entry_time_display":"entry_time","exit_time_display":"exit_time"})

csv_buffer = io.StringIO()
export_df.to_csv(csv_buffer, index=False)
st.download_button("Download ledger CSV (with notes)", data=csv_buffer.getvalue().encode("utf-8"), file_name="trading_journal_ledger.csv", mime="text/csv")

if not closed.empty:
    csv_buffer2 = io.StringIO()
    daily_df.to_csv(csv_buffer2, index=False)
    st.download_button("Download daily summary CSV", data=csv_buffer2.getvalue().encode("utf-8"), file_name="trading_journal_daily_summary.csv", mime="text/csv")

st.caption("Notes: Entry/Exit times shown in Asia/Kolkata. Edit Notes in the ledger and click 'Apply edits to ledger' to update (in-memory), then use Download to export.")