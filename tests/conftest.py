import asyncio
from asyncio import AbstractEventLoop
from collections.abc import AsyncGenerator

import motor.motor_asyncio
import pytest
from httpx import ASGITransport, AsyncClient

from core import settings
from core.database import initialize_database
from src.app.app import app


@pytest.fixture(scope="session")
def event_loop() -> AbstractEventLoop:
    return asyncio.get_event_loop()


@pytest.fixture(autouse=True, scope="session")
async def init_db() -> None:
    """Ининциализировать базу данных"""
    await initialize_database()


@pytest.fixture(autouse=True)
async def drop_db() -> None:
    if not settings.mongo.db_name.lower().endswith("test"):
        raise RuntimeError

    mongo: motor.motor_asyncio.AsyncIOMotorClient = motor.motor_asyncio.AsyncIOMotorClient(settings.mongo.url)
    await mongo.drop_database(settings.mongo.db_name)


@pytest.fixture(scope="session")
async def client() -> AsyncGenerator[AsyncClient]:
    """Получить тестовый клиент"""
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://testserver",
    ) as client:
        yield client
