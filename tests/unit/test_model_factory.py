"""ModelFactory 连接池与重试机制测试"""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock

from app.llm.model_factory import ModelFactory


class TestModelFactoryConnectionPool:
    """ModelFactory 连接池测试"""

    def setup_method(self):
        """每个测试前清理缓存"""
        ModelFactory._chat_clients.clear()
        ModelFactory._async_clients.clear()

    @pytest.mark.asyncio
    async def test_get_async_client_caches_client(self):
        """测试异步客户端被缓存"""
        with patch('app.llm.model_factory.AsyncOpenAI') as mock_async_openai:
            mock_client = MagicMock()
            mock_client.close = AsyncMock()
            mock_async_openai.return_value = mock_client

            client1 = await ModelFactory.get_async_client(
                api_key="test_api_key_123",
                base_url="https://api.test.com"
            )
            client2 = await ModelFactory.get_async_client(
                api_key="test_api_key_123",
                base_url="https://api.test.com"
            )

            assert client1 is client2
            assert mock_async_openai.call_count == 1

    @pytest.mark.asyncio
    async def test_get_async_client_different_keys_different_cache(self):
        """测试不同 API key 创建不同客户端"""
        with patch('app.llm.model_factory.AsyncOpenAI') as mock_async_openai:
            mock_client1 = MagicMock()
            mock_client1.close = AsyncMock()
            mock_client2 = MagicMock()
            mock_client2.close = AsyncMock()
            mock_async_openai.side_effect = [mock_client1, mock_client2]

            client1 = await ModelFactory.get_async_client(api_key="key1_12345", base_url="https://api.test.com")
            client2 = await ModelFactory.get_async_client(api_key="key2_67890", base_url="https://api.test.com")

            assert client1 is not client2
            assert mock_async_openai.call_count == 2

    @pytest.mark.asyncio
    async def test_get_async_client_cache_key_uses_hash(self):
        """测试缓存键使用哈希而非截断"""
        import hashlib
        
        with patch('app.llm.model_factory.AsyncOpenAI') as mock_async_openai:
            mock_client = MagicMock()
            mock_client.close = AsyncMock()
            mock_async_openai.return_value = mock_client

            api_key = "test_api_key_with_long_prefix_12345"
            base_url = "https://api.test.com"
            
            await ModelFactory.get_async_client(api_key=api_key, base_url=base_url)
            
            expected_key = hashlib.sha256(f"{api_key}_{base_url}".encode()).hexdigest()[:16]
            assert expected_key in ModelFactory._async_clients

    @pytest.mark.asyncio
    async def test_get_async_client_similar_prefixes_no_collision(self):
        """测试相似前缀的 API key 不会产生缓存冲突"""
        with patch('app.llm.model_factory.AsyncOpenAI') as mock_async_openai:
            mock_client1 = MagicMock()
            mock_client1.close = AsyncMock()
            mock_client2 = MagicMock()
            mock_client2.close = AsyncMock()
            mock_async_openai.side_effect = [mock_client1, mock_client2]

            client1 = await ModelFactory.get_async_client(
                api_key="api_key_prefix_a_12345",
                base_url="https://api.test.com"
            )
            client2 = await ModelFactory.get_async_client(
                api_key="api_key_prefix_b_67890",
                base_url="https://api.test.com"
            )

            assert client1 is not client2
            assert len(ModelFactory._async_clients) == 2

    @pytest.mark.asyncio
    async def test_get_async_client_with_retry_config(self):
        """测试重试配置"""
        with patch('app.llm.model_factory.AsyncOpenAI') as mock_async_openai:
            mock_client = MagicMock()
            mock_client.close = AsyncMock()
            mock_async_openai.return_value = mock_client

            await ModelFactory.get_async_client(
                api_key="test_key",
                base_url="https://api.test.com",
                timeout=30.0,
                max_retries=5
            )

            call_kwargs = mock_async_openai.call_args[1]
            assert call_kwargs["timeout"] == 30.0
            assert call_kwargs["max_retries"] == 5

    def test_get_general_model_caches_client(self):
        """测试通用模型被缓存"""
        with patch('app.llm.model_factory.ChatTongyi') as mock_chat_tongyi:
            mock_model = MagicMock()
            mock_chat_tongyi.return_value = mock_model

            model1 = ModelFactory.get_general_model(is_expert=False, enable_thinking=False)
            model2 = ModelFactory.get_general_model(is_expert=False, enable_thinking=False)

            assert model1 is model2
            assert mock_chat_tongyi.call_count == 1

    def test_get_general_model_different_configs_different_cache(self):
        """测试不同配置创建不同模型"""
        with patch('app.llm.model_factory.ChatTongyi') as mock_chat_tongyi:
            mock_model1 = MagicMock()
            mock_model2 = MagicMock()
            mock_chat_tongyi.side_effect = [mock_model1, mock_model2]

            model1 = ModelFactory.get_general_model(is_expert=False, enable_thinking=False)
            model2 = ModelFactory.get_general_model(is_expert=True, enable_thinking=False)

            assert model1 is not model2
            assert mock_chat_tongyi.call_count == 2

    def test_get_general_model_skip_cache(self):
        """测试跳过缓存"""
        with patch('app.llm.model_factory.ChatTongyi') as mock_chat_tongyi:
            mock_model1 = MagicMock()
            mock_model2 = MagicMock()
            mock_chat_tongyi.side_effect = [mock_model1, mock_model2]

            model1 = ModelFactory.get_general_model(use_cache=False)
            model2 = ModelFactory.get_general_model(use_cache=False)

            assert model1 is not model2
            assert mock_chat_tongyi.call_count == 2

    def test_get_general_model_with_retry_config(self):
        """测试通用模型重试配置"""
        with patch('app.llm.model_factory.ChatTongyi') as mock_chat_tongyi:
            mock_model = MagicMock()
            mock_chat_tongyi.return_value = mock_model

            ModelFactory.get_general_model()

            call_kwargs = mock_chat_tongyi.call_args[1]
            assert call_kwargs["request_timeout"] == 60
            assert call_kwargs["max_retries"] == 3

    @pytest.mark.asyncio
    async def test_close_all_clears_caches(self):
        """测试关闭所有客户端"""
        with patch('app.llm.model_factory.AsyncOpenAI') as mock_async_openai:
            mock_client = MagicMock()
            mock_client.close = AsyncMock()
            mock_async_openai.return_value = mock_client

            await ModelFactory.get_async_client(api_key="test_key")
            ModelFactory.get_general_model()

            assert len(ModelFactory._async_clients) == 1
            assert len(ModelFactory._chat_clients) == 1

            await ModelFactory.close_all()

            assert len(ModelFactory._async_clients) == 0
            assert len(ModelFactory._chat_clients) == 0
            mock_client.close.assert_called_once()

    def test_get_cache_stats(self):
        """测试获取缓存状态"""
        ModelFactory._chat_clients = {"test1": MagicMock(), "test2": MagicMock()}
        ModelFactory._async_clients = {"test3": MagicMock()}

        stats = ModelFactory.get_cache_stats()

        assert stats["total_chat"] == 2
        assert stats["total_async"] == 1
        assert "test1" in stats["chat_clients"]
        assert "test3" in stats["async_clients"]
