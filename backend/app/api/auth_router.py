from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from pydantic import BaseModel

from app.database import get_db
from app.models.models import User
from app.auth import verify_password, create_access_token

router = APIRouter(prefix="/auth", tags=["auth"])


class LoginRequest(BaseModel):
    email: str
    password: str


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    role: str
    name: str
    email: str


@router.post("/login", response_model=LoginResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    clean_email = payload.email.strip().lower()
    
    try:
        user = db.query(User).filter(func.lower(User.email) == clean_email).first()
    except Exception:
        user = None

    if not user:
        try:
            from seed import ensure_seeded
            ensure_seeded(db)
            user = db.query(User).filter(func.lower(User.email) == clean_email).first()
        except Exception as e:
            print(f"Auth seed error: {e}")

    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid email or password")

    token = create_access_token({"sub": user.email, "role": user.role})
    return LoginResponse(access_token=token, role=user.role, name=user.name, email=user.email)

