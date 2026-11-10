from fastapi import APIRouter, HTTPException, status
from sqlalchemy import select

from ai_template.config import settings
from ai_template.dependencies import CurrentUserDep, DBDep, OAuthFormDep
from ai_template.models import User
from ai_template.schemas import Token, UserCreate, UserResponse
from ai_template.security import (
    create_access_token,
    get_password_hash,
    verify_password,
)

router = APIRouter(tags=["Auth"])


@router.post(
    "/signup", response_model=UserResponse, status_code=status.HTTP_201_CREATED
)
async def sign_up(user_data: UserCreate, db: DBDep):
    query = select(User).where(User.email == user_data.email)
    result = await db.execute(query)
    existing_user = result.scalars().first()

    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered!",
        )

    hashed_pwd = get_password_hash(user_data.password)

    new_user = User(email=user_data.email, hashed_password=hashed_pwd)

    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)

    return new_user


@router.post("/login", response_model=Token)
async def login(form_data: OAuthFormDep, db: DBDep):
    query = select(User).where(User.email == form_data.username)
    result = await db.execute(query)
    user = result.scalars().first()

    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )
    data = {"sub": user.email, "exp": settings.access_token_expire_minutes}
    access_token = create_access_token(data)

    return {"access_token": access_token, "token_type": "bearer"}


@router.get("/users/me", response_model=UserResponse)
async def get_user_information(current_user: CurrentUserDep):
    return current_user
