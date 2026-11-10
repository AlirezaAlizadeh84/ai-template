from contextlib import asynccontextmanager
from fastapi import FastAPI

from ai_template.database import engine
from ai_template.models import Base
from ai_template.routers import auth, chat


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield


app = FastAPI(title="My AI Project API", lifespan=lifespan)

app.include_router(auth.router)
app.include_router(chat.router)