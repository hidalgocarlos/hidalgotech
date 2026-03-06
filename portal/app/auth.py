import os
from datetime import datetime, timedelta
from urllib.parse import urlparse

from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import Request, HTTPException

# Ruta base del portal (igual que en main) para redirect al login
_portal_url = (os.environ.get("PORTAL_URL") or "").strip().rstrip("/")
PORTAL_PATH = ""
if _portal_url:
    try:
        parsed = urlparse(_portal_url)
        path = (parsed.path or "").strip()
        if path and path != "/":
            PORTAL_PATH = path.rstrip("/")
    except Exception:
        pass

def _login_url() -> str:
    return (PORTAL_PATH + "/") if PORTAL_PATH else "/"

# En producción obligatorio desde variable de entorno; en desarrollo permite fallback
_SECRET_KEY = os.environ.get("SECRET_KEY", "CHANGE_THIS_TO_256_BIT_SECRET").strip()
if os.environ.get("APP_ENV") == "production" and (
    not _SECRET_KEY or _SECRET_KEY == "CHANGE_THIS_TO_256_BIT_SECRET"
):
    raise RuntimeError("En producción debes definir SECRET_KEY (variable de entorno).")
SECRET_KEY = _SECRET_KEY
ALGORITHM = "HS256"
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    # bcrypt limita a 72 bytes; truncar en UTF-8 para evitar ValueError
    if isinstance(password, str):
        password = password.encode("utf-8")[:72].decode("utf-8", errors="ignore")
    return pwd_context.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


def create_token(data: dict) -> str:
    to_encode = data.copy()
    to_encode["exp"] = datetime.utcnow() + timedelta(hours=8)
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


async def verify_token(request: Request):
    token = request.cookies.get("access_token")
    if not token:
        raise HTTPException(status_code=302, headers={"Location": _login_url()})
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload.get("sub")
    except JWTError:
        raise HTTPException(status_code=302, headers={"Location": _login_url()})
