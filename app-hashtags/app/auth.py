import os
from jose import JWTError, jwt
from fastapi import Request, HTTPException

SECRET_KEY = os.environ.get("SECRET_KEY", "CHANGE_THIS_TO_256_BIT_SECRET").strip()
ALGORITHM = "HS256"


async def verify_token(request: Request):
    token = request.cookies.get("access_token")
    if not token:
        raise HTTPException(status_code=302, headers={"Location": f"/login?redirect_uri={request.url.path}"})
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload.get("sub")
    except JWTError:
        raise HTTPException(status_code=302, headers={"Location": f"/login?redirect_uri={request.url.path}"})
