# mock_api.py
from flask import Flask, request, jsonify
import time
import math
from datetime import datetime, timedelta
import random

app = Flask(__name__)

@app.route("/login", methods=["POST"])
def login():
    data = request.json or {}
    client_code = data.get("client_code", "unknown")
    token = f"mock-token-{int(time.time())}"
    return jsonify({"status": "ok", "token": token, "client_code": client_code})

@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok", "uptime": int(time.time())})

@app.route("/place_order", methods=["POST"])
def place_order():
    payload = request.json or {}
    order_id = f"MOCK-{int(time.time()*1000)}"
    return jsonify({"status": "ok", "order_id": order_id, "received": payload})

@app.route("/quote", methods=["GET"])
def quote():
    """
    GET /quote?symbol=NIFTY&count=100&force=false
    Returns a simple time-series of price points (timestamp, price).
    """
    symbol = request.args.get("symbol", "NIFTY")
    count = int(request.args.get("count", "100"))
    # optional parameter 'force' for compatibility
    force = request.args.get("force", "false").lower() in ("1","true","yes")

    # generate mock price series ending now, 1-minute spacing
    now = datetime.now()
    base = 25000 if symbol.upper().startswith("NIFTY") else 20000
    # small deterministic-ish seed per symbol so repeated calls look similar
    random.seed(hash(symbol) & 0xffffffff)
    prices = []
    price = base + random.uniform(-10, 10)
    for i in range(count):
        # simulate minute-by-minute walk
        delta = random.gauss(0, 4)
        price = max(1, price + delta)
        ts = (now - timedelta(minutes=(count - 1 - i))).isoformat()
        prices.append({"datetime": ts, "price": round(price, 2)})

    return jsonify({
        "status": "ok",
        "symbol": symbol,
        "count": count,
        "force": force,
        "data": prices
    })

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5001, debug=True)

