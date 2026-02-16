
import pytest
import pytest_asyncio
from unittest.mock import patch, AsyncMock, MagicMock
from httpx import AsyncClient, ASGITransport
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from app.core.database import Base, get_db
from app.core.redis import redis_client


SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


@pytest.fixture
def mock_redis():
    mock_redis_client = AsyncMock()
    mock_redis_client.get = AsyncMock(return_value=None)
    mock_redis_client.set = AsyncMock(return_value=None)
    mock_redis_client.delete = AsyncMock(return_value=None)
    mock_redis_client.client = AsyncMock()
    mock_redis_client.client.scan = AsyncMock(return_value=(0, []))
    mock_redis_client.client.delete = AsyncMock(return_value=None)
    mock_redis_client.connect = AsyncMock()
    mock_redis_client.disconnect = AsyncMock()
    
    with patch('app.core.redis.redis_client', mock_redis_client), \
         patch('app.services.conversation_service.redis_client', mock_redis_client), \
         patch('app.services.chat_service.redis_client', mock_redis_client):
        yield mock_redis_client


@pytest.fixture(autouse=True)
def setup_database():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


app.dependency_overrides[get_db] = override_get_db


class TestHealthCheck:
    @pytest.mark.asyncio
    async def test_health_check(self, mock_redis):
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test"
        ) as client:
            response = await client.get("/health")
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "healthy"

    @pytest.mark.asyncio
    async def test_root_endpoint(self, mock_redis):
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test"
        ) as client:
            response = await client.get("/")
            assert response.status_code == 200
            data = response.json()
            assert "Welcome" in data["message"]


class TestAuthAPI:
    @pytest.mark.asyncio
    async def test_register_user(self, mock_redis):
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test"
        ) as client:
            response = await client.post(
                "/api/v1/auth/register",
                json={
                    "username": "testuser",
                    "email": "test@example.com",
                    "password": "testpassword123"
                }
            )
            assert response.status_code in [200, 201]

    @pytest.mark.asyncio
    async def test_login_user(self, mock_redis):
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test"
        ) as client:
            await client.post(
                "/api/v1/auth/register",
                json={
                    "username": "testuser",
                    "email": "test@example.com",
                    "password": "testpassword123"
                }
            )
            
            response = await client.post(
                "/api/v1/auth/login",
                json={
                    "username": "testuser",
                    "password": "testpassword123"
                }
            )
            assert response.status_code == 200
            data = response.json()
            assert "access_token" in data


class TestConversationAPI:
    @pytest.fixture
    async def auth_token(self, mock_redis):
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test"
        ) as client:
            await client.post(
                "/api/v1/auth/register",
                json={
                    "username": "convuser",
                    "email": "conv@example.com",
                    "password": "password123"
                }
            )
            login_response = await client.post(
                "/api/v1/auth/login",
                json={
                    "username": "convuser",
                    "password": "password123"
                }
            )
            return login_response.json()["access_token"]

    @pytest.mark.asyncio
    async def test_create_conversation(self, mock_redis):
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test"
        ) as client:
            await client.post(
                "/api/v1/auth/register",
                json={
                    "username": "convuser2",
                    "email": "conv2@example.com",
                    "password": "password123"
                }
            )
            login_response = await client.post(
                "/api/v1/auth/login",
                json={
                    "username": "convuser2",
                    "password": "password123"
                }
            )
            token = login_response.json()["access_token"]
            
            response = await client.post(
                "/api/v1/conversations",
                json={
                    "title": "Test Conversation",
                    "model_name": "qwen-flash"
                },
                headers={"Authorization": f"Bearer {token}"}
            )
            assert response.status_code in [200, 201]

