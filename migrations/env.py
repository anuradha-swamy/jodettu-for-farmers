from logging.config import fileConfig
from sqlalchemy import pool, create_engine
from alembic import context
import os
from dotenv import load_dotenv
from pathlib import Path

# Alembic Config object
config = context.config

# Setup logging
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Import your Base metadata
from db.base import Base
target_metadata = Base.metadata


# ✅ Load .env from project root (IMPORTANT FIX)
BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")


def get_database_url():
    url = os.getenv("SYNC_DATABASE_URL")
    if not url:
        raise RuntimeError("❌ SYNC_DATABASE_URL is not set. Check your .env file.")
    return url


def run_migrations_offline():
    """Run migrations in 'offline' mode."""
    url = get_database_url()

    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        compare_type=True,
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online():
    """Run migrations in 'online' mode."""
    url = get_database_url()

    # ✅ Debug log (remove in production if needed)
    print(f"✅ Using DB URL: {url}")

    connectable = create_engine(
        url,
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
        )

        with context.begin_transaction():
            context.run_migrations()


# Entry point
if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()