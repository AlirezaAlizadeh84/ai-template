from contextlib import asynccontextmanager
from typing import Annotated
from fastapi import FastAPI, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select


from ai_template.database import get_db, engine
from ai_template.models import User, Base
from ai_template.schemas import UserCreate, UserResponse
from ai_template.security import get_password_hash


@asynccontextmanager
async def lifespan(app: FastAPI):
    
    async with engine.begin() as conn:
       
        await conn.run_sync(Base.metadata.create_all)
    yield  


app = FastAPI(title="My AI Project API", lifespan=lifespan)

DBDep = Annotated[AsyncSession,Depends(get_db)]

@app.post('/signup',response_model = UserResponse,status_code = status.HTTP_201_CREATED)
async def sign_up(user_data : UserCreate,db:DBDep):

    query = select(User).where(User.email == user_data.email)
    result = await db.execute(query)
    existing_user = result.scalars().first()

    if existing_user :
        raise HTTPException(
            status_code = status.HTTP_400_BAD_REQUEST,
            detail = "Email already registered!"
        )

    hashed_pwd = get_password_hash(user_data.password)

    new_user = User(
        email = user_data.email,
        hashed_password = hashed_pwd 
    )

    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)


    return new_user