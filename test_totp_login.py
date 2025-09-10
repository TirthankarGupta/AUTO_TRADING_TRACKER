# test_totp_login.py
import requests, pyotp

BASE32SECRET = "HKXC22Z4EOYLHQLVZNN7JBM3BU"
CLIENT = "AAAJ983675"
PASSWORD = "1772"

totp_code = pyotp.TOTP(BASE32SECRET).now()
print("Code generated from secret (should match your phone):", totp_code)

url = "https://apiconnect.angelone.in/rest/auth/angelbroking/user/v1/loginByPassword"
payload = {"clientcode": CLIENT, "password": PASSWORD, "totp": totp_code}

r = requests.post(url, json=payload, timeout=10)
print("HTTP status:", r.status_code)
print("Response text:", r.text)
