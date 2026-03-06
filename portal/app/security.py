"""
Utilidades de seguridad: CSRF y rate limiting.
No exponer secretos ni datos sensibles en logs.
"""
import secrets
import time
from typing import Dict, Tuple

# Rate limit: (count, window_end)
_rate_limit_store: Dict[str, Tuple[int, float]] = {}
RATE_LIMIT_WINDOW = 300  # 5 minutos
RATE_LIMIT_MAX_REQUESTS = 200  # por IP por ventana


def generate_csrf_token() -> str:
    """Genera un token CSRF seguro (32 bytes en URL-safe base64)."""
    return secrets.token_urlsafe(32)


def verify_csrf(cookie_token: str | None, form_token: str | None) -> bool:
    """Compara token de cookie con el del formulario. Constant-time."""
    if not cookie_token or not form_token:
        return False
    return secrets.compare_digest(cookie_token, form_token)


def rate_limit_check(client_ip: str) -> bool:
    """
    Devuelve True si la IP está dentro del límite, False si debe bloquearse.
    Limpia ventanas expiradas.
    """
    now = time.time()
    # Limpiar entradas vencidas
    to_del = [ip for ip, (_, end) in _rate_limit_store.items() if now > end]
    for ip in to_del:
        del _rate_limit_store[ip]
    count, window_end = _rate_limit_store.get(client_ip, (0, now + RATE_LIMIT_WINDOW))
    if now > window_end:
        _rate_limit_store[client_ip] = (1, now + RATE_LIMIT_WINDOW)
        return True
    if count >= RATE_LIMIT_MAX_REQUESTS:
        return False
    _rate_limit_store[client_ip] = (count + 1, window_end)
    return True
