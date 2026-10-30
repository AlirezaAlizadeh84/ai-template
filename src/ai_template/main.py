from contextlib import asynccontextmanager
from typing import Annotated
from fastapi import FastAPI, Depends, HTTPException, Query, status
import httpx
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import delete, select
from fastapi.security import OAuth2PasswordRequestForm,OAuth2PasswordBearer
import jwt


from ai_template.database import get_db, engine
from ai_template.models import ChatMessage, User, Base
from ai_template.schemas import ChatHistoryResponse, ChatRequest, ChatResponse, UserCreate, UserResponse,Token
from ai_template.security import get_password_hash,verify_password,create_access_token
from ai_template.llm import ask_ollama
from ai_template.config import settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    
    async with engine.begin() as conn:
       
        await conn.run_sync(Base.metadata.create_all)
    yield  


app = FastAPI(title="My AI Project API", lifespan=lifespan)

DBDep = Annotated[AsyncSession,Depends(get_db)]
OAuthFormDep = Annotated[OAuth2PasswordRequestForm,Depends()]
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/login")



async def get_current_user(db: DBDep, token: Annotated[str, Depends(oauth2_scheme)]) -> User:

    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
    )
    try:
        payload = jwt.decode(
            token, settings.secret_key, algorithms=[settings.algorithm]
        )
        email: str | None = payload.get("sub")
        if email is None:
            raise credentials_exception
    except jwt.PyJWTError:
        raise credentials_exception

    query = select(User).where(User.email == email)
    result = await db.execute(query)
    user = result.scalar_one_or_none()

    if user is None:
        raise credentials_exception

    return user

CurrentUserDep = Annotated[User,Depends(get_current_user)]




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





@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest, current_user: CurrentUserDep, db: DBDep):
    # ۱. واکشی ۵ پیام آخر کاربر برای ساخت حافظه (Context)
    query = (
        select(ChatMessage)
        .where(ChatMessage.user_id == current_user.id)
        .order_by(ChatMessage.created_at.desc())
        .limit(5)
    )
    result = await db.execute(query)
    recent_messages = result.scalars().all()

    # ۲. ساخت پرامپت هوشمند در صورت وجود سابقه چت
    if recent_messages:
        context = ""
        for msg in reversed(recent_messages):
            context += f"User: {msg.prompt}\nAI: {msg.response}\n"
        full_prompt = (
            f"Previous conversation:\n{context}\nCurrent question:\nUser: {request.prompt}"
        )
    else:
        full_prompt = request.prompt

    # ۳. ارسال به سرویس هوش مصنوعی Ollama
    try:
        ai_reply = await ask_ollama(full_prompt)
    except httpx.HTTPError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"AI service is currently unavailable: {str(e)}",
        )

    # ۴. ذخیره فقط سوال جدید و پاسخ آن در دیتابیس
    chat_message = ChatMessage(
        user_id=current_user.id,
        prompt=request.prompt,
        response=ai_reply,
        model=settings.ollama_model,
    )
    db.add(chat_message)
    await db.commit()

    return ChatResponse(response=ai_reply, model=settings.ollama_model)


@app.get('/chat/history',response_model = list[ChatHistoryResponse])
async def get_chat_history(db:DBDep,current_user : CurrentUserDep,
                           skip : Annotated[int,Query(ge=0)] = 0 ,
                           limit : Annotated[int,Query (ge=1,le=100)] = 20) :
    
    query = (

        select(ChatMessage)
        .where(ChatMessage.user_id == current_user.id)
        .order_by(ChatMessage.created_at.desc())
        .offset(skip)
        .limit(limit)

        )
    
    result = await db.execute(query)
    return result.scalars().all()
        



@app.post('/login',response_model = Token)
async def login(form_data : OAuthFormDep,db : DBDep):

    query = select(User).where(User.email == form_data.username)
    result = await db.execute(query)
    user = result.scalars().first()

    if not user or not verify_password(form_data.password,user.hashed_password):
        raise HTTPException(
            status_code = status.HTTP_401_UNAUTHORIZED,
            detail = "Invalid email or password"
        )
    data = {"sub":user.email,"exp":settings.access_token_expire_minutes}
    access_token = create_access_token(data)


    return {"access_token":access_token,"token_type":"bearer"}


@app.delete("/chat/history", status_code = status.HTTP_204_NO_CONTENT)
async def delete_chat_history(current_user : CurrentUserDep,db : DBDep):
    query = delete(ChatMessage).where(ChatMessage.user_id == current_user.id)
    await db.execute(query)
    await db.commit()