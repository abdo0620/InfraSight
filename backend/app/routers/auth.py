from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from ..auth import check_password, current_user, hash_password, make_token
from ..db import User, get_db

router = APIRouter(prefix="/api/auth", tags=["auth"])
# Languages of the AI updates sent to citizens: name given to the AI -> name shown to the user
LANGS = {"English": "English", "French": "Français", "Breton": "Brezhoneg", "Spanish": "Español", "Portuguese": "Português",
         "Arabic": "العربية", "Turkish": "Türkçe", "German": "Deutsch", "Italian": "Italiano"}


class Login(BaseModel):
    username: str
    password: str


class Register(BaseModel):
    username: str = Field(min_length=3, max_length=40, pattern=r"^[A-Za-z0-9_.-]+$")
    name: str = Field(min_length=1, max_length=80)
    password: str = Field(min_length=8, max_length=200)
    lang: str = "English"


class Prefs(BaseModel):
    lang: str


def _lang(v: str) -> str:
    if v not in LANGS:
        raise HTTPException(422, "Unknown language")
    return v


def _session(u: User) -> dict:
    return {"token": make_token(u), "user": me(u)}


@router.post("/login")
def login(b: Login, s: Session = Depends(get_db)):
    u = s.query(User).filter_by(username=b.username.strip().lower()).first()
    if not u or not check_password(b.password, u.password_hash):
        raise HTTPException(401, "Wrong username or password")
    return _session(u)


@router.post("/register")
def register(b: Register, s: Session = Depends(get_db)):
    """Self sign-up always creates a citizen. Staff accounts: python -m app.cli create-user."""
    name = b.username.lower()
    if s.query(User).filter_by(username=name).first():
        raise HTTPException(409, "This username is taken")
    u = User(username=name, name=b.name.strip(), role="citizen", lang=_lang(b.lang), password_hash=hash_password(b.password))
    s.add(u)
    s.commit()
    return _session(u)


@router.get("/me")
def me(u: User = Depends(current_user)):
    return {"id": u.id, "username": u.username, "name": u.name, "role": u.role, "lang": u.lang, "langs": LANGS}


@router.put("/me")
def set_prefs(p: Prefs, u: User = Depends(current_user), s: Session = Depends(get_db)):
    u.lang = _lang(p.lang)
    s.commit()
    return me(u)
