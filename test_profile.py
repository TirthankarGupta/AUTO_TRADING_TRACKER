# test_profile.py
from SmartApi.smartConnect import SmartConnect
import json, os

def main():
    print("\n=== Test Profile Fetch with Saved Session ===\n")

    # Load session tokens
    try:
        with open("session.json", "r") as f:
            session = json.load(f)
    except Exception as e:
        print("❌ Could not read session.json:", str(e))
        return

    api_key = os.environ.get("SMARTAPI_KEY")
    if not api_key:
        print("❌ API Key not found. Set SMARTAPI_KEY environment variable or login again.")
        return

    try:
        api = SmartConnect(api_key=api_key)
        # Reuse jwtToken saved earlier
        api.setAccessToken(session["jwtToken"])
        profile = api.getProfile(session["clientcode"])
    except Exception as e:
        print("❌ Exception during profile fetch:", str(e))
        return

    # Debug output (safe: no tokens shown)
    if isinstance(profile, dict):
        print("DEBUG keys in profile response:", list(profile.keys()))
        print("DEBUG status field:", profile.get("status"))
        print("DEBUG message field:", profile.get("message"))
        if "data" in profile:
            print("DEBUG data keys:", list(profile["data"].keys()))
    else:
        print("DEBUG profile type:", type(profile))

    if isinstance(profile, dict) and profile.get("status") is True:
        print("\n✅ Profile fetch SUCCESS.")
    else:
        print("\n⚠️ Profile fetch returned unexpected data.")

if __name__ == "__main__":
    main()
