# test_funds.py
"""
Test SmartAPI session by fetching funds (safe read-only call).
Uses session.json created by smartapi_session_manager.py.
"""

import os, json
from SmartApi.smartConnect import SmartConnect

def main():
    print("\n=== Test Funds Fetch ===\n")

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
        api.setFeedToken(session["feedToken"])

        funds = api.getFunds()
    except Exception as e:
        print("❌ Exception while fetching funds:", e)
        return

    # Print safe summary
    if isinstance(funds, dict):
        print("DEBUG keys in response:", list(funds.keys()))
        print("DEBUG status field:", funds.get("status") or funds.get("success"))
        if "data" in funds and isinstance(funds["data"], dict):
            print("Funds available keys:", list(funds["data"].keys()))
        print("\n✅ Funds fetch call completed.")
    else:
        print("⚠️ Unexpected response type:", type(funds))
        print(funds)

if __name__ == "__main__":
    main()
