from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from db.models.core import User
from routes.deps import get_db
from schemas import LoginIn
from services.security import create_token, verify_password

router = APIRouter(prefix='/api/auth', tags=['auth'])


@router.post('/login')
def login(body: LoginIn, db: Session = Depends(get_db)):
    user = db.scalar(select(User).where(User.username == body.username))
    if not user or not verify_password(body.password, user.password_hash):
        raise HTTPException(401, 'Invalid credentials')
    return {'token': create_token(user.id, user.role), 'role': user.role}
