# save_session.py
from SmartApi.smartConnect import SmartConnect
import getpass, os, json

def main():
    print("\n=== Save SmartAPI session tokens ===\n")

    api_key = os.environ.get("SMARTAPI_KEY")
    if not api_key:
        api_key = getpass.getpass("Enter your SmartAPI API Key (input hidden): ")

    client_code = input("Enter your client code / User ID: ").strip()
    password = getpass.getpass("Enter your PIN / Password (input hidden): ").strip()
    totp = input("Enter the 6-digit TOTP from your Authenticator app: ").strip()

    print("\nAttempting login and saving session tokens...\n")
    api = SmartConnect(api_key=api_key)
    resp = api.generateSession(client_code, password, totp)

    if isinstance(resp, dict) and resp.get("status") is True and "data" in resp:
        data = resp["data"]
        session = {
            "clientcode": data.get("clientcode"),
            "name": data.get("name"),
            "jwtToken": data.get("jwtToken"),
            "refreshToken": data.get("refreshToken"),
            "feedToken": data.get("feedToken")
        }
        with open("session.json", "w") as f:
            json.dump(session, f, indent=2)
        print("✅ Saved session tokens to session.json (in C:\\AUTO_TRADING_TRACKER).")
        print("DO NOT share session.json publicly. Keep it secure.")
    else:
        print("❌ Login FAILED or no tokens returned.")
        if isinstance(resp, dict) and resp.get("message"):
            print("Server message:", resp.get("message"))
        else:
            print("Response:", resp)

if __name__ == "__main__":
    main()
