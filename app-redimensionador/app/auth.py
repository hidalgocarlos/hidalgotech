import os
from jose import JWTError, jwt
from fastapi import Request, HTTPException

SECRET_KEY = os.environ.get("SECRET_KEY", "CHANGE_THIS_TO_256_BIT_SECRET")
ALGORITHM = "HS256"
IS_DEV = os.environ.get("APP_ENV") == "development"


async def verify_token(request: Request):
    token = request.cookies.get("access_token")
    if not token:
        if IS_DEV:
            return "dev"
        raise HTTPException(status_code=302, headers={"Location": "/"})
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload.get("sub")
    except JWTError:
        if IS_DEV:
            return "dev"
        raise HTTPException(status_code=302, headers={"Location": "/"})
