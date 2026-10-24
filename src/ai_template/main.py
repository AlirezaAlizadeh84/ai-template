from contextlib import asynccontextmanager
from typing import Annotated
from fastapi import FastAPI, Depends, HTTPException, status
import httpx
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from fastapi.security import OAuth2PasswordRequestForm,OAuth2PasswordBearer
import jwt


from ai_template.database import get_db, engine
from ai_template.models import User, Base
from ai_template.schemas import ChatRequest, ChatResponse, UserCreate, UserResponse,Token
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

CurrentUserDep = Annotated[User,Depends(get_current_user)]

@app.post('/chat',response_model = ChatResponse)
async def chat(request:ChatRequest,current_user : CurrentUserDep): 
    try:
        ai_reply = await ask_ollama(request.prompt)
    except httpx.HTTPError as e :
        raise HTTPException(
            status_code = status.HTTP_503_SERVICE_UNAVAILABLE,
            detail = f"Ai service is currently unavailable : {str(e)}"
        )
            

    return ChatResponse(
        response = ai_reply,
        model = settings.ollama_model
    )



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



