# refresh_session.py
from SmartApi.smartConnect import SmartConnect
import json, os

def main():
    print("\n=== Refresh SmartAPI Session ===\n")

    # Load the previous session
    try:
        with open("session.json", "r") as f:
            session = json.load(f)
    except Exception as e:
        print("❌ Could not read session.json:", str(e))
        return

    api_key = os.environ.get("SMARTAPI_KEY")
    if not api_key:
        print("❌ API Key not found. Set SMARTAPI_KEY environment variable.")
        return

    try:
        api = SmartConnect(api_key=api_key)
        # Use refreshToken to get a new jwtToken
        resp = api.generateToken(session["refreshToken"])
    except Exception as e:
        print("❌ Exception during refresh:", str(e))
        return

    # Handle response
    if isinstance(resp, dict) and resp.get("status") is True and "data" in resp:
        data = resp["data"]
        session.update({
            "jwtToken": data.get("jwtToken"),
            "refreshToken": data.get("refreshToken"),  # Angel may rotate this
            "feedToken": data.get("feedToken")
        })
        with open("session.json", "w") as f:
            json.dump(session, f, indent=2)
        print("✅ Session refreshed. New tokens saved to session.json.")
    else:
        print("❌ Refresh failed. Full response:")
        print(resp)

if __name__ == "__main__":
    main()
