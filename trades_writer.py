# trades_writer.py
"""
Lightweight writer for executed trades.
Safe to import from non-Streamlit scripts (e.g., trading_bot.py).
Writes/appends to trades.csv with columns compatible with trading_journal.py.
"""
import os
from datetime import datetime
import pandas as pd
import pytz

KOLKATA = pytz.timezone("Asia/Kolkata")

def append_trade_to_csv(order_resp: dict, order_payload: dict, trades_csv_path: str = "trades.csv"):
    """
    Append a single executed trade to trades.csv.
    order_resp: dict returned by the mock /order endpoint (expects 'order_id' and 'status' and optionally 'details')
    order_payload: dict used to place the order (expects symbol, quantity, price, instrument)
    """
    try:
        trade_row = {
            "trade_id": order_resp.get("order_id") if isinstance(order_resp, dict) else str(int(datetime.now().timestamp())),
            "symbol": order_payload.get("symbol", ""),
            "quantity": order_payload.get("quantity", 0),
            "lot_size": order_payload.get("lot_size", None) if order_payload.get("lot_size", None) is not None else 1,
            "entry_price": order_payload.get("price", None),
            "exit_price": None,
            "entry_time": datetime.now(tz=KOLKATA).strftime("%Y-%m-%d %H:%M:%S"),
            "exit_time": "",
            "fees": 0.0,
            "notes": f"auto-recorded ({order_resp.get('status') if isinstance(order_resp, dict) else 'unknown'})"
        }

        file_exists = os.path.exists(trades_csv_path)
        df_row = pd.DataFrame([trade_row])
        if not file_exists:
            df_row.to_csv(trades_csv_path, index=False, mode="w")
        else:
            df_row.to_csv(trades_csv_path, index=False, mode="a", header=False)

        print(f"Appended trade to {trades_csv_path}: {trade_row['trade_id']}")
        return True
    except Exception as e:
        print("Failed to append trade to CSV:", e)
        return False
