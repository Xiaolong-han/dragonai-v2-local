"""AgentFactory 连接池测试"""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock

from app.agents.agent_factory import AgentFactory, get_chat_model, _chat_model_cache


class TestAgentFactory:
    """AgentFactory 测试"""

    def setup_method(self):
        """每个测试前清理缓存"""
        AgentFactory._agent_cache.clear()
        _chat_model_cache.clear()

    def test_get_chat_model_caches_model(self):
        """测试聊天模型被缓存"""
        with patch('app.agents.agent_factory.ChatTongyi') as mock_chat_tongyi:
            mock_model = MagicMock()
            mock_chat_tongyi.return_value = mock_model

            model1 = get_chat_model(is_expert=False, enable_thinking=False)
            model2 = get_chat_model(is_expert=False, enable_thinking=False)

            assert model1 is model2
            assert mock_chat_tongyi.call_count == 1

    def test_get_chat_model_different_configs_different_cache(self):
        """测试不同配置创建不同模型"""
        with patch('app.agents.agent_factory.ChatTongyi') as mock_chat_tongyi:
            mock_model1 = MagicMock()
            mock_model2 = MagicMock()
            mock_chat_tongyi.side_effect = [mock_model1, mock_model2]

            model1 = get_chat_model(is_expert=False, enable_thinking=False)
            model2 = get_chat_model(is_expert=True, enable_thinking=False)

            assert model1 is not model2
            assert mock_chat_tongyi.call_count == 2

    def test_get_chat_model_skip_cache(self):
        """测试跳过缓存"""
        with patch('app.agents.agent_factory.ChatTongyi') as mock_chat_tongyi:
            mock_model1 = MagicMock()
            mock_model2 = MagicMock()
            mock_chat_tongyi.side_effect = [mock_model1, mock_model2]

            model1 = get_chat_model(use_cache=False)
            model2 = get_chat_model(use_cache=False)

            assert model1 is not model2
            assert mock_chat_tongyi.call_count == 2

    @pytest.mark.asyncio
    async def test_close_checkpointer_clears_cache(self):
        """测试关闭 checkpointer 清理缓存"""
        AgentFactory._agent_cache = {"test1": MagicMock(), "test2": MagicMock()}
        _chat_model_cache["test3"] = MagicMock()

        await AgentFactory.close_checkpointer()

        assert len(AgentFactory._agent_cache) == 0
        assert len(_chat_model_cache) == 0

    def test_get_cache_stats(self):
        """测试获取缓存状态"""
        AgentFactory._agent_cache = {"test1": MagicMock(), "test2": MagicMock()}

        stats = AgentFactory.get_cache_stats()

        assert stats["total"] == 2
        assert "test1" in stats["cached_agents"]
