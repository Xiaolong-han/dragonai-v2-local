
import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.ext.asyncio import async_sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.database import Base
from app.config import settings


@pytest.fixture
def test_settings():
    settings.database_url = "sqlite+aiosqlite:///:memory:"
    settings.secret_key = "test-secret-key"
    settings.access_token_expire_minutes = 30
    return settings


@pytest.fixture
def async_engine():
    return create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )


@pytest.fixture
def AsyncTestingSessionLocal(async_engine):
    return async_sessionmaker(
        bind=async_engine,
        class_=AsyncSession,
        autocommit=False,
        autoflush=False,
        expire_on_commit=False,
    )


@pytest_asyncio.fixture(autouse=True)
async def create_tables(async_engine):
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture
async def db_session(AsyncTestingSessionLocal):
    async with AsyncTestingSessionLocal() as session:
        yield session


@pytest_asyncio.fixture
async def mock_redis_client(mocker):
    mock_redis = mocker.AsyncMock()
    mock_redis.get.return_value = None
    mock_redis.set.return_value = None
    mock_redis.delete.return_value = False
    mock_redis.exists.return_value = False
    mock_redis.scan.return_value = (0, [])
    mock_redis.client = mock_redis
    mock_redis.ping.return_value = True
    return mock_redis


@pytest.fixture
def mock_request():
    class MockRequest:
        def __init__(self):
            self.state = type('State', (), {})()
            self.headers = {}
            self.url = type('URL', (), {'path': '/test'})()
            self.method = 'GET'
            self.client = type('Client', (), {'host': '127.0.0.1'})()
    
    return MockRequest()
