from logging.config import fileConfig
import os

from sqlalchemy import engine_from_config
from sqlalchemy import pool
import models
from alembic import context
from core.base import Base
# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# add your model's MetaData object here
# for 'autogenerate' support
# from myapp import mymodel
# target_metadata = mymodel.Base.metadata
target_metadata = Base.metadata

# Get database URL - use environment variable directly to avoid loading settings
# during build when env vars might not be available
def get_database_url():
    """Get database URL from environment or settings"""
    # Try to get from environment first (for Railway, Render, etc.)
    if "DATABASE_URL" in os.environ:
        db_url = os.environ["DATABASE_URL"]
        # Convert postgresql:// to postgresql+psycopg:// for compatibility
        if db_url.startswith("postgresql://") and "+psycopg" not in db_url:
            db_url = db_url.replace("postgresql://", "postgresql+psycopg://")
        return db_url
    
    # Fall back to building from individual components
    if all(k in os.environ for k in ["POSTGRES_USER", "POSTGRES_PASSWORD", "POSTGRES_SERVER", "POSTGRES_DB"]):
        from urllib.parse import quote_plus
        username = quote_plus(os.environ["POSTGRES_USER"])
        password = quote_plus(os.environ["POSTGRES_PASSWORD"])
        host = os.environ["POSTGRES_SERVER"]
        db = os.environ["POSTGRES_DB"]
        return f"postgresql+psycopg://{username}:{password}@{host}/{db}"
    
    # Finally try to import settings (this should work at runtime)
    try:
        from core.settings import settings
        return settings.SQLALCHEMY_DATABASE_URI
    except Exception:
        return ""

settings = type('Settings', (), {'SQLALCHEMY_DATABASE_URI': get_database_url()})

# other values from the config, defined by the needs of env.py,
# can be acquired:
# my_important_option = config.get_main_option("my_important_option")
# ... etc.

def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    url = settings.SQLALCHEMY_DATABASE_URI
    if not url:
        raise ValueError("Database URL is not configured. Please set DATABASE_URL or individual POSTGRES_* environment variables.")
    
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.

    """
    db_url = settings.SQLALCHEMY_DATABASE_URI
    if not db_url:
        raise ValueError("Database URL is not configured. Please set DATABASE_URL or individual POSTGRES_* environment variables.")
    
    configuration = config.get_section(config.config_ini_section)
    configuration["sqlalchemy.url"] = db_url
    connectable = engine_from_config(
        configuration, prefix="sqlalchemy.", poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection, target_metadata=target_metadata
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
