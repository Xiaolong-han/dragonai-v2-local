
import pytest
import pytest_asyncio
from unittest.mock import patch, AsyncMock, MagicMock
from app.core.redis import RedisClient, cache_aside, cached


class TestRedisClient:
    @pytest.fixture
    def mock_redis(self):
        with patch('app.core.redis.redis') as mock:
            mock_client = AsyncMock()
            mock.from_url.return_value = mock_client
            yield mock_client

    @pytest.mark.asyncio
    async def test_connect(self, mock_redis):
        client = RedisClient()
        await client.connect()
        assert client._client is not None

    @pytest.mark.asyncio
    async def test_disconnect(self, mock_redis):
        client = RedisClient()
        await client.connect()
        await client.disconnect()
        assert client._client is None

    @pytest.mark.asyncio
    async def test_get_set_string(self, mock_redis):
        mock_redis.get.return_value = "test_value"
        client = RedisClient()
        client._client = mock_redis
        
        await client.set("key", "test_value", ttl=3600)
        value = await client.get("key")
        assert value == "test_value"

    @pytest.mark.asyncio
    async def test_get_set_json(self, mock_redis):
        test_data = {"key": "value"}
        mock_redis.get.return_value = '{"key": "value"}'
        client = RedisClient()
        client._client = mock_redis
        
        await client.set("json_key", test_data)
        value = await client.get("json_key")
        assert value == {"key": "value"}

    @pytest.mark.asyncio
    async def test_delete(self, mock_redis):
        client = RedisClient()
        client._client = mock_redis
        await client.delete("key")
        mock_redis.delete.assert_called_once_with("key")

    @pytest.mark.asyncio
    async def test_exists(self, mock_redis):
        mock_redis.exists.return_value = 1
        client = RedisClient()
        client._client = mock_redis
        exists = await client.exists("key")
        assert exists is True


class TestCacheAside:
    @pytest.fixture
    def mock_redis_client(self):
        with patch('app.core.redis.redis_client') as mock:
            mock.get = AsyncMock(return_value=None)
            mock.set = AsyncMock(return_value=None)
            yield mock

    @pytest.mark.asyncio
    async def test_cache_aside_miss(self, mock_redis_client):
        async def fetch_data():
            return "fetched_data"
        
        result = await cache_aside(
            key="test_key",
            ttl=3600,
            data_func=fetch_data
        )
        assert result == "fetched_data"
        mock_redis_client.set.assert_called_once()

    @pytest.mark.asyncio
    async def test_cache_aside_hit(self, mock_redis_client):
        mock_redis_client.get.return_value = "cached_data"
        async def fetch_data():
            return "fetched_data"
        
        result = await cache_aside(
            key="test_key",
            ttl=3600,
            data_func=fetch_data
        )
        assert result == "cached_data"

    @pytest.mark.asyncio
    async def test_cache_aside_no_data_func(self, mock_redis_client):
        mock_redis_client.get.return_value = None
        result = await cache_aside(key="test_key", ttl=3600)
        assert result is None

