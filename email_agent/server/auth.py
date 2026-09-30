import os
import msal

from email_agent.config import settings, PKG_ROOT

SCOPES = ["Mail.Read", "Mail.ReadWrite", "Mail.Send", "User.Read"]
AUTHORITY = "https://login.microsoftonline.com/common"
CACHE_FILE = PKG_ROOT / "token_cache.bin"

CLIENT_ID = settings.email_agent_id
if not CLIENT_ID:
    raise SystemExit("MICROSOFT_ID 未配置,请检查 .env")


cache = msal.SerializableTokenCache()
if os.path.exists(CACHE_FILE):
    with open(CACHE_FILE, encoding="utf-8") as f:
        cache.deserialize(f.read())

app = msal.PublicClientApplication(CLIENT_ID, authority=AUTHORITY, token_cache=cache)

def _acquire_token() -> dict:
    account = app.get_accounts()
    if account:
        result = app.acquire_token_silent(SCOPES, account=account[0])
        if result and "access_token" in result:
            return result

    flow = app.initiate_device_flow(scopes=SCOPES)
    if "error" in flow:
        raise RuntimeError(flow["error_description"])

    print(flow["message"])
    result = app.acquire_token_by_device_flow(flow)

    # if "access_token" in result:
    #     raise RuntimeError(f'{result.get("error")}: {result.get("error_description")}')


    if "access_token" not in result:
        print("=" * 30, "完整 result 如下", "=" * 30)
        print(result)                    # ← 关键调试行
        raise RuntimeError(f'{result.get("error")}: {result.get("error_description")}')
    return result

def get_token():
    result = _acquire_token()
    if cache.has_state_changed:
        with open(CACHE_FILE, "w", encoding="utf-8") as f:
            f.write(cache.serialize())

    return result["access_token"]

