# direct_login_test.py
"""
Direct login test: generateSession + generateToken + holding()
This bypasses session.json, to confirm Angel One API sequence works.
"""

from SmartApi.smartConnect import SmartConnect
import getpass, os

def main():
    print("\n=== Direct Login Test ===\n")
    api_key = os.environ.get("SMARTAPI_KEY") or getpass.getpass("Enter API Key (hidden): ").strip()
    client = input("Client code / User ID: ").strip()
    pwd = getpass.getpass("Password / PIN (hidden): ").strip()
    totp = input("Enter 6-digit TOTP from Authenticator app: ").strip()

    api = SmartConnect(api_key=api_key)

    try:
        # Step 1: Login
        session_resp = api.generateSession(client, pwd, totp)
        print("DEBUG generateSession keys:", list(session_resp.keys()))
        data = session_resp.get("data", {})
        refresh_token = data.get("refreshToken")
        print("Got refreshToken? ->", bool(refresh_token))

        # Step 2: Get JWT using refreshToken
        token_resp = api.generateToken(refresh_token)
        print("DEBUG generateToken keys:", list(token_resp.keys()))
        tdata = token_resp.get("data", {})
        jwt = tdata.get("jwtToken")
        print("Got jwtToken? ->", bool(jwt))

        # Step 3: Call holdings
        if jwt:
            api.setAccessToken(jwt)
        holdings_resp = api.holding()
        print("DEBUG holding keys:", list(holdings_resp.keys()))
        print("DEBUG status/success:", holdings_resp.get("status") or holdings_resp.get("success"))
        print("Message:", holdings_resp.get("message"))

    except Exception as e:
        print("❌ Exception:", e)

if __name__ == "__main__":
    main()
