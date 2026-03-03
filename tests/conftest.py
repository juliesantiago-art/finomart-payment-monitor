import asyncio
import os
from typing import AsyncGenerator

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from testcontainers.postgres import PostgresContainer

from app.database import Base, get_session
from app.main import app
from app.models import IntegrationCost, PaymentMethod, Transaction  # noqa: F401


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


@pytest_asyncio.fixture(scope="session")
async def engine(db_url):
    _engine = create_async_engine(db_url, echo=False)
    async with _engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield _engine
    await _engine.dispose()


@pytest_asyncio.fixture(scope="function")
async def session(engine) -> AsyncGenerator[AsyncSession, None]:
    factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with factory() as s:
        yield s
        await s.rollback()
        # Clean up tables between tests
        for table in reversed(Base.metadata.sorted_tables):
            await s.execute(table.delete())
        await s.commit()


@pytest_asyncio.fixture(scope="function")
async def client(engine) -> AsyncGenerator[AsyncClient, None]:
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


API_KEY = "dev-api-key-change-in-production"
AUTH_HEADERS = {"X-API-Key": API_KEY}
