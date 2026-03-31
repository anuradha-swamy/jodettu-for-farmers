import os
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy import pool

from db.base import Base

load_dotenv()

SYNC_DATABASE_URL = os.getenv("SYNC_DATABASE_URL")
if not SYNC_DATABASE_URL:
    raise RuntimeError("SYNC_DATABASE_URL is not set")


def get_sync_engine():
    return create_engine(SYNC_DATABASE_URL, poolclass=pool.NullPool)


def get_metadata():
    return Base.metadata
