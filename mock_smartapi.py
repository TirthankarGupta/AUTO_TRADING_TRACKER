# mock_smartapi.py
"""
Mock SmartAPI server — guaranteed CE/PE signals
GET /quote?symbol=X&count=N&force=ce|pe
 - ce: strong uptrend, ensures BUY_CE
 - pe: strong downtrend, ensures BUY_PE
"""
from flask import Flask, request, jsonify
import time

app = Flask(__name__)

@app.route("/login", methods=["POST"])
def login():
    data = request.json or {}
    if data.get("client_code") == "demo" and data.get("password") == "demo":
        return jsonify({
            "status": "success",
            "access_token": "mock_access_token_123",
            "expires_in": 3600
        })
    return jsonify({"status": "error", "message": "invalid credentials"}), 401

def generate_forced(symbol="NIFTY", count=100, force="ce", start_price=25000):
    candles = []
    price = float(start_price)
    now = int(time.time())
    # decide slope: up = +5 each step, down = -5 each step
    slope = 5 if force == "ce" else -5
    for i in range(count):
        open_p = price
        close_p = price + slope
        high_p = max(open_p, close_p) + 1
        low_p = min(open_p, close_p) - 1
        vol = 100
        ts = now - (count - 1 - i) * 60
        candles.append({
            "symbol": symbol,
            "timestamp": ts,
            "open": round(open_p, 2),
            "high": round(high_p, 2),
            "low": round(low_p, 2),
            "close": round(close_p, 2),
            "volume": vol
        })
        price = close_p
    return candles

@app.route("/quote", methods=["GET"])
def quote():
    symbol = request.args.get("symbol", "NIFTY")
    try:
        count = int(request.args.get("count", "100"))
    except:
        count = 100
    force = (request.args.get("force") or "ce").lower()
    if force not in ("ce", "pe"):
        force = "ce"
    candles = generate_forced(symbol=symbol, count=count, force=force)
    return jsonify(candles)

@app.route("/order", methods=["POST"])
def order():
    body = request.json or {}
    return jsonify({
        "status": "success",
        "order_id": f"MOCK-{int(time.time())}",
        "details": body
    })

if __name__ == "__main__":
    app.run(port=5001, debug=True)
