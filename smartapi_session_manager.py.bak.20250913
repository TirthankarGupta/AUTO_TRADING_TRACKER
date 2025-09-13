# smartapi_session_manager.py
"""
Fail-safe SmartAPI session manager (updated)
- Ensures generateToken(refreshToken) is called immediately after generateSession
- Tries refresh first, falls back to manual login, and always exchanges refresh->jwt properly
"""
import os
import json
import logging
import getpass

# Import SmartConnect from installed package
try:
    from SmartApi.smartConnect import SmartConnect
except Exception:
    try:
        from smartapi.smartConnect import SmartConnect
    except Exception as e:
        raise ImportError("Could not import SmartConnect from installed smartapi packages.") from e

# optional pyotp
try:
    import pyotp
except Exception:
    pyotp = None

SESSION_FILE = "session.json"
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s: %(message)s")
log = logging.getLogger("smartapi-session-manager")


def load_session():
    if not os.path.exists(SESSION_FILE):
        return None
    try:
        with open(SESSION_FILE, "r") as f:
            return json.load(f)
    except Exception as e:
        log.error("Failed to read %s: %s", SESSION_FILE, e)
        return None


def save_session(session):
    try:
        with open(SESSION_FILE, "w") as f:
            json.dump(session, f, indent=2)
        log.info("Saved session.json (clientcode=%s). Keep this file private.", session.get("clientcode"))
    except Exception as e:
        log.error("Failed to save session.json: %s", e)


def get_api_key():
    api_key = os.environ.get("SMARTAPI_KEY")
    if api_key:
        return api_key
    return getpass.getpass("Enter SmartAPI API Key (hidden input): ").strip()


def prompt_totp():
    secret = os.environ.get("SMARTAPI_TOTP_SECRET")
    if secret and pyotp:
        try:
            return pyotp.TOTP(secret).now()
        except Exception as e:
            log.warning("pyotp generation failed: %s", e)
    return input("Enter 6-digit TOTP from Authenticator app: ").strip()


def prompt_credentials():
    client = input("Client code / User ID: ").strip()
    pwd = getpass.getpass("Password / PIN (hidden): ").strip()
    totp = prompt_totp()
    return client, pwd, totp


def _response_ok(resp):
    if not isinstance(resp, dict):
        return False
    if "status" in resp:
        return bool(resp.get("status") is True)
    if "success" in resp:
        return bool(resp.get("success") is True)
    return False


def _extract_data(resp):
    if isinstance(resp, dict):
        return resp.get("data")
    return None


def safe_get_profile(api, session):
    refresh_token = session.get("refreshToken")
    if not refresh_token:
        return False, {"message": "no refreshToken in session"}
    try:
        if session.get("jwtToken"):
            try:
                api.setAccessToken(session.get("jwtToken"))
            except Exception:
                pass
        resp = api.getProfile(refresh_token)
    except Exception as e:
        return False, {"exception": str(e)}
    if _response_ok(resp):
        return True, resp
    return False, resp


def attempt_refresh(api, session):
    refresh_token = session.get("refreshToken")
    if not refresh_token:
        return False, {"message": "no refreshToken"}
    try:
        resp = api.generateToken(refresh_token)
    except Exception as e:
        return False, {"exception": str(e)}
    if not isinstance(resp, dict):
        return False, {"message": "unexpected response type from generateToken", "type": str(type(resp))}
    if _response_ok(resp):
        data = _extract_data(resp) or {}
        jwt = data.get("jwtToken") if isinstance(data, dict) else None
        new_refresh = data.get("refreshToken") if isinstance(data, dict) else None
        feed = data.get("feedToken") if isinstance(data, dict) else None
        if jwt:
            session["jwtToken"] = jwt
            try:
                api.setAccessToken(jwt)
            except Exception:
                pass
        if new_refresh:
            session["refreshToken"] = new_refresh
            try:
                api.setRefreshToken(new_refresh)
            except Exception:
                pass
        if feed:
            session["feedToken"] = feed
            try:
                api.setFeedToken(feed)
            except Exception:
                pass
        save_session(session)
        return True, resp
    return False, resp


def do_manual_login_and_exchange(api):
    """
    Perform generateSession -> generateToken(refreshToken) sequence, then save session.
    """
    log.info("Manual login required. You will be prompted for client code, password and TOTP.")
    client, pwd, totp = prompt_credentials()
    try:
        resp = api.generateSession(client, pwd, totp)
    except Exception as e:
        return False, {"exception": str(e)}
    if not isinstance(resp, dict):
        return False, {"message": "unexpected response type from generateSession", "type": str(type(resp))}
    if not _response_ok(resp):
        return False, resp

    # extract refreshToken from generateSession response data
    gen_data = _extract_data(resp) or {}
    refresh_token = gen_data.get("refreshToken") if isinstance(gen_data, dict) else None
    if not refresh_token:
        # if generateSession didn't return refreshToken, fail-safe: save what we have and return
        session = {
            "clientcode": gen_data.get("clientcode") if isinstance(gen_data, dict) else client,
            "name": gen_data.get("name") if isinstance(gen_data, dict) else None
        }
        save_session(session)
        return False, {"message": "generateSession did not return refreshToken", "resp": resp}

    # Now exchange refreshToken for jwtToken via generateToken
    try:
        token_resp = api.generateToken(refresh_token)
    except Exception as e:
        return False, {"exception": str(e)}
    if not isinstance(token_resp, dict):
        return False, {"message": "unexpected response type from generateToken", "type": str(type(token_resp))}
    if not _response_ok(token_resp):
        return False, token_resp

    tok_data = _extract_data(token_resp) or {}
    jwt = tok_data.get("jwtToken") if isinstance(tok_data, dict) else None
    new_refresh = tok_data.get("refreshToken") if isinstance(tok_data, dict) else None
    feed = tok_data.get("feedToken") if isinstance(tok_data, dict) else None

    session = {
        "clientcode": gen_data.get("clientcode") if isinstance(gen_data, dict) else client,
        "name": gen_data.get("name") if isinstance(gen_data, dict) else None,
        "jwtToken": jwt,
        "refreshToken": new_refresh or refresh_token,
        "feedToken": feed
    }
    save_session(session)
    return True, session


def ensure_session():
    api_key = get_api_key()
    if not api_key:
        log.error("API key required.")
        return False

    api = SmartConnect(api_key=api_key)
    session = load_session()

    if session:
        log.info("Found existing session.json — checking profile with stored tokens.")
        ok, result = safe_get_profile(api, session)
        if ok:
            data = _extract_data(result) or {}
            log.info("Profile check OK. Client: %s", data.get("clientcode"))
            return True
        log.warning("Profile check failed: %s", result)

        log.info("Attempting token refresh with refreshToken...")
        ok, result = attempt_refresh(api, session)
        if ok:
            log.info("Refresh succeeded. Verifying profile with refreshed token...")
            ok2, r2 = safe_get_profile(api, session)
            if ok2:
                data = _extract_data(r2) or {}
                log.info("Profile check OK after refresh. Client: %s", data.get("clientcode"))
                return True
            else:
                log.warning("Profile still failed after refresh: %s", r2)
        else:
            log.warning("Refresh attempt failed: %s", result)

    # fallback: manual login then immediate token exchange
    log.info("Falling back to manual login and token exchange (generateSession -> generateToken).")
    ok, result = do_manual_login_and_exchange(api)
    if ok:
        log.info("Manual login + token exchange succeeded. Session stored.")
        return True
    else:
        log.error("Manual login/token exchange failed: %s", result)
        return False


if __name__ == "__main__":
    ok = ensure_session()
    if ok:
        log.info("Session ready. You can now run API calls that use session.json tokens.")
    else:
        log.error("Session not ready. Please read the messages above and retry.")
