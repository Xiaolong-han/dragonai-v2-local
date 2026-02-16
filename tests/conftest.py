
import pytest
import pytest_asyncio
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.database import Base
from app.config import settings


@pytest.fixture
def test_settings():
    settings.database_url = "sqlite:///:memory:"
    settings.secret_key = "test-secret-key"
    settings.access_token_expire_minutes = 30
    return settings


@pytest.fixture
def engine():
    return create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )


@pytest.fixture
def TestingSessionLocal(engine):
    return sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(autouse=True)
def create_tables(engine):
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def db_session(TestingSessionLocal):
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest_asyncio.fixture
async def mock_redis_client(mocker):
    mock_redis = mocker.AsyncMock()
    mock_redis.get.return_value = None
    mock_redis.set.return_value = None
    mock_redis.delete.return_value = None
    mock_redis.exists.return_value = False
    mock_redis.scan.return_value = (0, [])
    mock_redis.client = mock_redis
    return mock_redis

