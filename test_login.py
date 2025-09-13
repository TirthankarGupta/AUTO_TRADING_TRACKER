import os, json, requests
from dotenv import load_dotenv

load_dotenv()
url = os.getenv("ANGEL_LOGIN_URL", "https://apiconnect.angelbroking.com/rest/auth/angelbroking/user/v1/loginByPassword")
payload = {
    "client_id": os.getenv("ANGEL_API_KEY"),
    "client_secret": os.getenv("ANGEL_API_SECRET"),
    "username": os.getenv("ANGEL_USERNAME"),
    "password": os.getenv("ANGEL_CLIENT_PASSWORD"),
    "totp": os.getenv("ANGEL_TOTP", "")  # may be blank while support responds
}
headers = {"Content-Type": "application/json", "Accept": "application/json"}

print("Attempting login to:", url)
try:
    resp = requests.post(url, json=payload, headers=headers, timeout=15)
    print("HTTP", resp.status_code)
    # Print limited response body (avoid dumping very long or secret data)
    txt = resp.text
    print("Response (first 1000 chars):")
    print(txt[:1000])
except Exception as e:
    print("Request failed:", repr(e))
