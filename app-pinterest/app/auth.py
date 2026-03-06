import os
from jose import JWTError, jwt
from fastapi import Request, HTTPException

SECRET_KEY = os.environ.get("SECRET_KEY", "CHANGE_THIS_TO_256_BIT_SECRET").strip()
ALGORITHM = "HS256"

def _portal_login_url() -> str:
    url = (os.environ.get("PORTAL_URL") or "/").strip().rstrip("/")
    return (url + "/") if url and url != "/" else "/"


async def verify_token(request: Request):
    token = request.cookies.get("access_token")
    if not token:
        raise HTTPException(status_code=302, headers={"Location": _portal_login_url()})
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload.get("sub")
    except JWTError:
        raise HTTPException(status_code=302, headers={"Location": _portal_login_url()})
