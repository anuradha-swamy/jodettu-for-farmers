import os
from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from db.base import Base

load_dotenv(override=True)

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL is not set")

engine = create_async_engine(
    DATABASE_URL,
    echo=True,
    future=True,
)

AsyncSessionLocal = sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def get_postgres_db():
    async with AsyncSessionLocal() as session:
        yield session


async def init_postgres_db():
    async with engine.begin() as conn:
        from models.postgres_models import AnimalType, Breed  # noqa: F401
        await conn.run_sync(Base.metadata.create_all)


async def close_postgres_db():
    await engine.dispose()
