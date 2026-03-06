import os
from datetime import datetime, timedelta

from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import Request, HTTPException

SECRET_KEY = os.environ.get("SECRET_KEY", "CHANGE_THIS_TO_256_BIT_SECRET").strip()
ALGORITHM = "HS256"
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


def create_token(data: dict) -> str:
    to_encode = data.copy()
    to_encode["exp"] = datetime.utcnow() + timedelta(hours=8)
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def _portal_login_url() -> str:
    """URL del portal para redirigir cuando no hay sesión (mismo dominio, p. ej. / o /portal/)."""
    url = (os.environ.get("PORTAL_URL") or "/").strip().rstrip("/")
    if not url or url == "/":
        return "/"
    return url + "/"


async def verify_token(request: Request):
    token = request.cookies.get("access_token")
    if not token:
        raise HTTPException(status_code=302, headers={"Location": _portal_login_url()})
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload.get("sub")
    except JWTError:
        raise HTTPException(status_code=302, headers={"Location": _portal_login_url()})
