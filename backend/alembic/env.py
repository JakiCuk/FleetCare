"""Alembic migration environment (async-compatible).

Resolves the database URL from the ``DATABASE_URL`` environment variable,
imports the application's :data:`Base` metadata (importing ``app.models`` so
every table is registered), and runs migrations online against the async
engine. A sane local default mirrors ``database.py`` so the env stays usable
outside Docker.
"""

from __future__ import annotations

import asyncio
import os
import sys
from logging.config import fileConfig

from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config

from alembic import context

# When alembic runs as a console script, sys.path[0] is alembic's bin directory,
# not the project root, so ``import app`` would fail (ModuleNotFoundError). Add
# the directory that contains this ``alembic/`` folder (the backend project
# root) to sys.path before importing the application package.
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Importing app.models registers every ORM class on Base.metadata.
from app import models  # noqa: E402, F401  (side-effect import: populates metadata)
from app.database import Base  # noqa: E402

# Alembic Config object, providing access to values within alembic.ini.
config = context.config

# Resolve the connection string from the environment, falling back to the same
# local default used by app.database (mirrored here to avoid an import cycle of
# concerns: env.py owns its own URL resolution).
DATABASE_URL = os.environ.get(
    "DATABASE_URL",
    "postgresql+asyncpg://fleetcare:changeme@localhost:5432/fleetcare",
)
config.set_main_option("sqlalchemy.url", DATABASE_URL)

# Configure Python logging from the ini file, if present.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Target metadata for 'autogenerate' support.
target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode (emit SQL without a DBAPI connection)."""
    context.configure(
        url=DATABASE_URL,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
        compare_server_default=True,
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    """Configure the context with a live connection and run migrations."""
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        compare_type=True,
        compare_server_default=True,
    )

    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    """Create an async engine and run migrations within a connection."""
    connectable = async_engine_from_config(
        {"sqlalchemy.url": DATABASE_URL},
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode using the async engine."""
    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
