from sqlalchemy.ext.asyncio import create_async_engine,async_sessionmaker
from ai_template.config import settings

db_url = settings.database_url.replace("postgresql://","postgresql+asyncpg://")

engine = create_async_engine(db_url,echo = True)
AsyncSessionLocal = async_sessionmaker(engine,expire_on_commit = False)

async def get_db():
    async with AsyncSessionLocal() as session:
        yield session 