# run_with_refresh_and_holding.py
"""
One-step runner:
- imports ensure_session() from smartapi_session_manager.py
- ensures session (refresh or manual login if needed)
- then calls holding() and prints a safe debug summary
"""
import os
import json
import sys

# Import the session manager's ensure_session() function
try:
    from smartapi_session_manager import ensure_session
except Exception as e:
    print("❌ Could not import ensure_session from smartapi_session_manager.py:", e)
    sys.exit(1)

# Import SmartConnect
try:
    from SmartApi.smartConnect import SmartConnect
except Exception:
    try:
        from smartapi.smartConnect import SmartConnect
    except Exception as e:
        print("❌ Could not import SmartConnect:", e)
        sys.exit(1)

def call_holding():
    # Load session.json
    try:
        with open("session.json", "r") as f:
            session = json.load(f)
    except Exception as e:
        print("❌ Could not read session.json:", e)
        return False

    api_key = os.environ.get("SMARTAPI_KEY")
    if not api_key:
        print('❌ SMARTAPI_KEY not set for this session. Run:')
        print('   $env:SMARTAPI_KEY = "YOUR_API_KEY"')
        return False

    try:
        api = SmartConnect(api_key=api_key)
        # apply tokens (if present)
        if session.get("jwtToken"):
            try:
                api.setAccessToken(session["jwtToken"])
            except Exception:
                pass
        if session.get("refreshToken"):
            try:
                api.setRefreshToken(session["refreshToken"])
            except Exception:
                pass

        resp = api.holding()
    except Exception as e:
        print("❌ Exception while calling holding():", e)
        return False

    # Safe debug output
    if isinstance(resp, dict):
        keys = list(resp.keys())
        print("DEBUG keys in holdings response:", keys)
        # show whether API considers it successful
        status_val = resp.get("status") if "status" in resp else resp.get("success")
        print("DEBUG status/success field:", status_val)
        if isinstance(resp.get("data"), dict):
            print("DEBUG data keys (sample):", list(resp["data"].keys())[:10])
        # If success True, show short confirmation
        if status_val:
            print("\n✅ Holdings fetch SUCCESS.")
        else:
            # show message if present, safe (message text is fine)
            print("\n⚠️ Holdings fetch returned not-success. Message:", resp.get("message") or resp.get("errorCode"))
    else:
        print("⚠️ Unexpected response type from holding():", type(resp))
        print(resp)

    return True

def main():
    print("\n=== Run: ensure session -> holding ===\n")
    ok = ensure_session()
    if not ok:
        print("\n❌ ensure_session() failed. Aborting holding call.")
        return
    print("\nSession is ready. Now calling holding()...\n")
    call_holding()

if __name__ == "__main__":
    main()
