# test_smartapi_login.py
from SmartApi.smartConnect import SmartConnect
import getpass
import os
import json

def main():
    print("\n=== SmartAPI minimal login test ===\n")

    # Prefer environment variable; otherwise prompt securely
    api_key = os.environ.get("SMARTAPI_KEY")
    if not api_key:
        api_key = getpass.getpass("Enter your SmartAPI API Key (input hidden): ")

    client_code = input("Enter your client code / User ID: ").strip()
    password = getpass.getpass("Enter your PIN / Password (input hidden): ").strip()

    # Manual TOTP entry for this test
    totp = input("Enter the 6-digit TOTP from your Authenticator app: ").strip()

    print("\nAttempting login... (please wait)\n")

    try:
        api = SmartConnect(api_key=api_key)
        # generateSession(clientCode, password, totp)
        resp = api.generateSession(client_code, password, totp)
    except Exception as e:
        print("Exception while attempting to call generateSession():", str(e))
        return

    # Inspect response (safe to print) — don't share sensitive tokens publicly
    print("Raw response from SmartAPI:\n")
    try:
        print(json.dumps(resp, indent=2))
    except Exception:
        print(resp)

    # Typical success condition: resp['status'] is True and resp['data'] contains tokens
    if isinstance(resp, dict) and resp.get("status") is True:
        print("\n✅ Login SUCCESS. You have an active session.")
        # We intentionally do not display tokens here in full. Show keys only.
        if "data" in resp:
            print("Returned data keys:", list(resp["data"].keys()))
    else:
        print("\n❌ Login FAILED. Check your credentials / totp and try again.")
        # If there is an error message, print it to help debugging:
        if isinstance(resp, dict) and resp.get("message"):
            print("Server message:", resp.get("message"))

if __name__ == "__main__":
    main()
