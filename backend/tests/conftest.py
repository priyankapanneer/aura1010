import pytest_asyncio
from app.db.init_db import init_db


@pytest_asyncio.fixture(scope="session", autouse=True)
async def setup_test_database():
    """Initializes tables for the test session."""
    await init_db()
