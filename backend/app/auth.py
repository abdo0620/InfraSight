"""Passwords, login tokens, role checks, signed photo links and the per-user AI rate limit."""
import hashlib, hmac, logging, secrets, time
from collections import defaultdict, deque
from datetime import datetime, timedelta, timezone
import jwt
from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session
from .config import settings
from .db import User, get_db

ROLES = ("citizen", "tech", "elected")
STAFF = ("tech", "elected")
SECRET = settings.secret_key or secrets.token_hex(32)
if not settings.secret_key:
    logging.warning("SECRET_KEY is not set: using a random key, everyone is logged out on restart.")

_bearer = HTTPBearer(auto_error=False)


def hash_password(pw: str) -> str:
    salt = secrets.token_bytes(16)
    h = hashlib.scrypt(pw.encode(), salt=salt, n=2**14, r=8, p=1)
    return f"scrypt${salt.hex()}${h.hex()}"


def check_password(pw: str, stored: str) -> bool:
    try:
        _, salt, h = stored.split("$")
    except ValueError:
        return False
    test = hashlib.scrypt(pw.encode(), salt=bytes.fromhex(salt), n=2**14, r=8, p=1)
    return hmac.compare_digest(test.hex(), h)


def make_token(u: User) -> str:
    exp = datetime.now(timezone.utc) + timedelta(hours=settings.token_hours)
    return jwt.encode({"sub": str(u.id), "exp": exp}, SECRET, algorithm="HS256")


def current_user(cred: HTTPAuthorizationCredentials | None = Depends(_bearer), s: Session = Depends(get_db)) -> User:
    if not cred:
        raise HTTPException(401, "Sign in first")
    try:
        uid = int(jwt.decode(cred.credentials, SECRET, algorithms=["HS256"])["sub"])
    except (jwt.PyJWTError, KeyError, ValueError):
        raise HTTPException(401, "Session expired, sign in again")
    u = s.get(User, uid)                # loaded each request, so a role change or deletion applies at once
    if not u:
        raise HTTPException(401, "Session expired, sign in again")
    return u


def staff(u: User = Depends(current_user)) -> User:
    if u.role not in STAFF:
        raise HTTPException(403, "Only technicians and elected officials can do this")
    return u


def user_label(u: User) -> str:
    return {"tech": "Technician", "elected": "Elected official"}.get(u.role, "Citizen") + f" ({u.name})"


# Photo links: <img> tags cannot send the login token, so photo URLs carry a short-lived signature instead.
def sign_image(ref: str, hours: int = 24) -> str:
    exp = int(time.time()) + hours * 3600
    sig = hmac.new(SECRET.encode(), f"{ref}:{exp}".encode(), hashlib.sha256).hexdigest()[:32]
    return f"exp={exp}&sig={sig}"


def check_image(ref: str, exp: int, sig: str) -> bool:
    good = hmac.new(SECRET.encode(), f"{ref}:{exp}".encode(), hashlib.sha256).hexdigest()[:32]
    return exp > time.time() and hmac.compare_digest(good, sig)


# In-memory, per process. Enough for one server; use Redis if you run several workers.
_calls: dict[int, deque] = defaultdict(deque)


def ai_quota(u: User = Depends(current_user)) -> User:
    q, now = _calls[u.id], time.time()
    while q and q[0] < now - 3600:
        q.popleft()
    if len(q) >= settings.ai_calls_per_hour:
        raise HTTPException(429, "Too many AI requests. Try again later.")
    q.append(now)
    return u
