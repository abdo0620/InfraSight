"""Password hashing, signed tokens and role guards (standard library only)."""
import base64
import hashlib
import hmac
import json
import os
import time

from fastapi import HTTPException, Request

from config import settings

ITERATIONS = 200_000


def hash_password(password: str) -> str:
    salt = os.urandom(16)
    dk = hashlib.pbkdf2_hmac('sha256', password.encode(), salt, ITERATIONS)
    return f'pbkdf2_sha256${ITERATIONS}${salt.hex()}${dk.hex()}'


def verify_password(password: str, stored: str) -> bool:
    try:
        _, iters, salt, digest = stored.split('$')
        dk = hashlib.pbkdf2_hmac('sha256', password.encode(), bytes.fromhex(salt), int(iters))
        return hmac.compare_digest(dk.hex(), digest)
    except (ValueError, TypeError):
        return False


def _b64(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).decode().rstrip('=')


def _unb64(s: str) -> bytes:
    return base64.urlsafe_b64decode(s + '=' * (-len(s) % 4))


def _sig(body: str) -> str:
    return hmac.new(settings.secret_key().encode(), body.encode(), hashlib.sha256).hexdigest()


def create_token(user_id: str, role: str, ttl_s: int = 8 * 3600) -> str:
    body = _b64(json.dumps({'sub': user_id, 'role': role, 'exp': int(time.time()) + ttl_s}).encode())
    return f'{body}.{_sig(body)}'


def read_token(token: str) -> dict | None:
    try:
        body, sig = token.split('.')
        if not hmac.compare_digest(sig, _sig(body)):
            return None
        payload = json.loads(_unb64(body))
        return payload if payload['exp'] > time.time() else None
    except (ValueError, KeyError, TypeError):
        return None


def require_role(role: str):
    """FastAPI dependency factory: 401 without a valid token, 403 with the wrong role."""
    def dependency(request: Request) -> dict:
        header = request.headers.get('authorization', '')
        payload = read_token(header[7:]) if header.lower().startswith('bearer ') else None
        if not payload:
            raise HTTPException(401, 'Authentication required')
        if payload['role'] != role:
            raise HTTPException(403, 'Insufficient role')
        return payload
    return dependency
