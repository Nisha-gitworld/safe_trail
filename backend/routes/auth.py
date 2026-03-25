"""Routes — Authentication"""
from fastapi import APIRouter, HTTPException, Depends, status
from sqlalchemy import select
from models.schemas import UserRegister, UserLogin, TokenResponse
from models.db_models import User
from services.auth_service import hash_password, verify_password, create_access_token
from database.db import get_db
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter()


@router.post("/register", status_code=201)
async def register(payload: UserRegister, db: AsyncSession = Depends(get_db)):
    # Check duplicate email
    result = await db.execute(select(User).where(User.email == payload.email))
    if result.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="Email already registered")

    user = User(
        email=payload.email,
        hashed_password=hash_password(payload.password),
        full_name=payload.full_name,
        nationality=payload.nationality,
        phone=payload.phone,
        blood_type=payload.blood_type,
        allergies=payload.allergies,
        embassy_contact=payload.embassy_contact,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)

    return {"message": "User registered successfully", "user_id": str(user.id)}


@router.post("/login", response_model=TokenResponse)
async def login(payload: UserLogin, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.email == payload.email))
    user = result.scalar_one_or_none()

    if not user or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    token = create_access_token(str(user.id), user.email)
    return TokenResponse(access_token=token)


@router.get("/me")
async def get_me(current_user=Depends(__import__("services.auth_service", fromlist=["get_current_user"]).get_current_user)):
    return current_user
