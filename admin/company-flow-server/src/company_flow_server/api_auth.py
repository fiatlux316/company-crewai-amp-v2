from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session
import hashlib
import jwt
import os
from datetime import datetime, timedelta, timezone

from .distributed.db import SessionLocal, User

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

class SignUpRequest(BaseModel):
    user_id: str
    name: str
    password: str
    user_type: str

class LoginRequest(BaseModel):
    user_id: str
    password: str

def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

def create_access_token(user: User) -> str:
    alg = os.getenv("AUTH_JWT_ALGORITHM", "HS256")
    key = os.getenv("AUTH_JWT_PUBLIC_KEY") or os.getenv("AUTH_JWT_SECRET", "dev-secret-change-me")
    
    roles = []
    if user.user_type == "1":
        roles = ["platform_admin"]
    elif user.user_type == "2":
        roles = ["operator", "flow_admin"]
    elif user.user_type == "3":
        roles = ["developer", "crew_owner"]
    elif user.user_type == "4":
        roles = ["viewer"]
        
    payload = {
        "sub": user.user_id,
        "roles": roles,
        "name": user.name,
        "user_type": user.user_type,
        "exp": datetime.now(timezone.utc) + timedelta(days=1)
    }
    return jwt.encode(payload, key, algorithm=alg)

@router.post("/signup")
def signup(req: SignUpRequest, db: Session = Depends(get_db)):
    if db.query(User).filter(User.user_id == req.user_id).first():
        raise HTTPException(status_code=400, detail="User ID already exists")
    
    user = User(
        user_id=req.user_id,
        name=req.name,
        password=hash_password(req.password),
        user_type=req.user_type,
        status="0"
    )
    db.add(user)
    db.commit()
    return {"message": "Signup successful, waiting for approval"}

@router.post("/login")
def login(req: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.user_id == req.user_id).first()
    if not user or user.password != hash_password(req.password):
        raise HTTPException(status_code=401, detail="Invalid user ID or password")
    
    if user.status != "1":
        raise HTTPException(status_code=403, detail="Account not approved yet")
    
    token = create_access_token(user)
    return {
        "access_token": token,
        "user_id": user.user_id,
        "name": user.name,
        "user_type": user.user_type
    }

class UserResponse(BaseModel):
    id: str
    user_id: str
    name: str
    user_type: str
    status: str
    created_at: datetime
    
@router.get("/users")
def list_users(db: Session = Depends(get_db)):
    users = db.query(User).all()
    return users

@router.put("/users/{user_id}/approve")
def approve_user(user_id: str, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.user_id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    user.status = "1"
    db.commit()
    return {"message": "User approved"}

