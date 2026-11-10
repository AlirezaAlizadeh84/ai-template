from typing import Annotated
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
import jwt
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession


from ai_template.database import get_db
from ai_template.models import User
from ai_template.config import settings


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

