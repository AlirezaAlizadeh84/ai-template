from contextlib import asynccontextmanager
from typing import Annotated
from fastapi import FastAPI, Depends, HTTPException, status
import httpx
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select


from ai_template.database import get_db, engine
from ai_template.models import User, Base
from ai_template.schemas import ChatRequest, ChatResponse, UserCreate, UserResponse
from ai_template.security import get_password_hash
from ai_template.llm import ask_ollama
from ai_template.config import settings


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


@app.post('/chat',response_model = ChatResponse)
async def chat(request:ChatRequest): 
    try:
        ai_reply = await ask_ollama(request.prompt)
    except httpx.HTTPError as e :
        raise HTTPException(
            status_code = status.HTTP_503_SERVICE_UNAVAILBLE,
            detail = f"Ai service is currently unavailable : {str(e)}"
        )
            

    return ChatResponse(
        response = ai_reply,
        model = settings.ollama_model
    )

