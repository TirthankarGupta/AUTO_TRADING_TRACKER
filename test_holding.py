# test_holding.py
"""
Test SmartAPI session by fetching holdings (safe read-only call).
Uses session.json created by smartapi_session_manager.py.
"""

import os
import json
from SmartApi.smartConnect import SmartConnect

def main():
    print("\n=== Test Holdings Fetch ===\n")

    # Load session
    try:
        with open("session.json", "r") as f:
            session = json.load(f)
    except Exception as e:
        print("❌ Could not read session.json:", e)
        return

    api_key = os.environ.get("SMARTAPI_KEY")
    if not api_key:
        print("❌ SMARTAPI_KEY not set. Run:")
        print('   $env:SMARTAPI_KEY = "YOUR_API_KEY"')
        return

    try:
        api = SmartConnect(api_key=api_key)
        api.setAccessToken(session["jwtToken"])
        api.setRefreshToken(session["refreshToken"])
        # call holdings
        holdings_resp = api.holding()
    except Exception as e:
        print("❌ Exception while fetching holdings:", e)
        return

    if isinstance(holdings_resp, dict):
        print("DEBUG keys in holdings response:", list(holdings_resp.keys()))
        print("DEBUG status/success field:", holdings_resp.get("status") or holdings_resp.get("success"))
        if "data" in holdings_resp and isinstance(holdings_resp["data"], dict):
            print("Holding keys:", list(holdings_resp["data"].keys()))
        print("\n✅ Holdings fetch completed.")
    else:
        print("⚠️ Unexpected response type:", type(holdings_resp))
        print(holdings_resp)

if __name__ == "__main__":
    main()
