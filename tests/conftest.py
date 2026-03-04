from typing import AsyncGenerator

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool
from testcontainers.postgres import PostgresContainer

from app.database import Base, get_session
from app.main import app
from app.models import IntegrationCost, PaymentMethod, Transaction  # noqa: F401

API_KEY = "dev-api-key-change-in-production"
AUTH_HEADERS = {"X-API-Key": API_KEY}


@pytest.fixture(scope="session")
def postgres_container():
    with PostgresContainer("postgres:16-alpine") as pg:
        yield pg


@pytest.fixture(scope="session")
def db_url(postgres_container):
    host = postgres_container.get_container_host_ip()
    port = postgres_container.get_exposed_port(5432)
    user = postgres_container.username
    password = postgres_container.password
    db = postgres_container.dbname
    return f"postgresql+asyncpg://{user}:{password}@{host}:{port}/{db}"


@pytest.fixture(scope="session")
def sync_db_url(postgres_container):
    host = postgres_container.get_container_host_ip()
    port = postgres_container.get_exposed_port(5432)
    user = postgres_container.username
    password = postgres_container.password
    db = postgres_container.dbname
    return f"host={host} port={port} dbname={db} user={user} password={password}"


@pytest_asyncio.fixture(scope="session")
async def engine(db_url):
    _engine = create_async_engine(db_url, poolclass=NullPool, echo=False)
    async with _engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield _engine
    await _engine.dispose()


def _truncate_sync(sync_db_url: str):
    """Truncate all tables via psycopg2. Terminates other connections first so TRUNCATE doesn't wait."""
    import psycopg2
    tables = [t.name for t in reversed(Base.metadata.sorted_tables)]
    conn = psycopg2.connect(sync_db_url)
    conn.autocommit = True
    cur = conn.cursor()
    # Force-close other connections (including asyncpg sessions with open read transactions)
    cur.execute("""
        SELECT pg_terminate_backend(pid)
        FROM pg_stat_activity
        WHERE datname = current_database()
          AND pid <> pg_backend_pid()
    """)
    cur.execute(f"TRUNCATE TABLE {', '.join(tables)} CASCADE")
    cur.close()
    conn.close()


@pytest_asyncio.fixture(scope="function")
async def session(engine, sync_db_url) -> AsyncGenerator[AsyncSession, None]:
    factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    s = factory()
    yield s
    # Tests commit explicitly; psycopg2 cleans up without asyncpg event loop conflict
    _truncate_sync(sync_db_url)


@pytest_asyncio.fixture(scope="function")
async def client(engine, sync_db_url) -> AsyncGenerator[AsyncClient, None]:
    factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async def override_get_session():
        async with factory() as s:
            yield s

    app.dependency_overrides[get_session] = override_get_session

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as ac:
        yield ac

    app.dependency_overrides.clear()
    _truncate_sync(sync_db_url)
