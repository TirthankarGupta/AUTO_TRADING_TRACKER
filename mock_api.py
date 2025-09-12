# mock_api.py
from flask import Flask, request, jsonify
import time
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
    symbol = request.args.get("symbol", "NIFTY")
    count = int(request.args.get("count", "100"))
    now = datetime.now()
    base = 25000 if symbol.upper().startswith("NIFTY") else 20000
    random.seed(hash(symbol) & 0xffffffff)
    candles = []
    price = base + random.uniform(-10, 10)
    for i in range(count):
        delta = random.gauss(0, 4)
        new_close = max(1, price + delta)
        open_p = price
        high_p = max(open_p, new_close) + abs(random.gauss(0, 1))
        low_p = min(open_p, new_close) - abs(random.gauss(0, 1))
        ts = (now - timedelta(minutes=(count - 1 - i))).isoformat()
        candles.append({
            "datetime": ts,
            "open": round(open_p,2),
            "high": round(high_p,2),
            "low": round(low_p,2),
            "close": round(new_close,2)
        })
        price = new_close

    return jsonify({
        "status": "ok",
        "symbol": symbol,
        "count": count,
        "data": candles
    })

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5001, debug=True)
