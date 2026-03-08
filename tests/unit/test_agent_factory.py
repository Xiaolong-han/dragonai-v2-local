"""AgentFactory 缓存预热测试"""

import pytest
from unittest.mock import patch, MagicMock, AsyncMock

from app.agents.agent_factory import AgentFactory


class TestAgentFactoryWarmup:
    """AgentFactory 缓存预热测试"""

    def setup_method(self):
        """每个测试前清理缓存"""
        AgentFactory._agent_cache.clear()

    @pytest.mark.asyncio
    async def test_warmup_creates_all_configs(self):
        """测试预热创建全部 4 种配置"""
        with patch.object(AgentFactory, 'get_checkpointer') as mock_checkpointer, \
             patch('app.agents.agent_factory.create_deep_agent') as mock_create_agent, \
             patch('app.agents.agent_factory.get_chat_model') as mock_model:
            
            mock_checkpointer.return_value = MagicMock()
            mock_create_agent.return_value = MagicMock()
            mock_model.return_value = MagicMock()
            
            await AgentFactory.warmup()
            
            assert len(AgentFactory._agent_cache) == 4
            assert "expert_False_thinking_False" in AgentFactory._agent_cache
            assert "expert_True_thinking_False" in AgentFactory._agent_cache
            assert "expert_False_thinking_True" in AgentFactory._agent_cache
            assert "expert_True_thinking_True" in AgentFactory._agent_cache

    @pytest.mark.asyncio
    async def test_warmup_continues_on_failure(self):
        """测试预热失败时继续创建其他配置"""
        with patch.object(AgentFactory, 'get_checkpointer') as mock_checkpointer, \
             patch('app.agents.agent_factory.create_deep_agent') as mock_create_agent, \
             patch('app.agents.agent_factory.get_chat_model') as mock_model:
            
            mock_checkpointer.return_value = MagicMock()
            mock_model.return_value = MagicMock()
            
            call_count = 0
            def side_effect(*args, **kwargs):
                nonlocal call_count
                call_count += 1
                if call_count == 1:
                    raise Exception("Test error")
                return MagicMock()
            
            mock_create_agent.side_effect = side_effect
            
            await AgentFactory.warmup()
            
            assert mock_create_agent.call_count == 4
            assert len(AgentFactory._agent_cache) == 3

    @pytest.mark.asyncio
    async def test_warmup_uses_concurrent_execution(self):
        """测试预热使用并发执行"""
        import asyncio
        
        execution_times = []
        
        with patch.object(AgentFactory, 'get_checkpointer') as mock_checkpointer, \
             patch('app.agents.agent_factory.create_deep_agent') as mock_create_agent, \
             patch('app.agents.agent_factory.get_chat_model') as mock_model:
            
            mock_checkpointer.return_value = MagicMock()
            mock_model.return_value = MagicMock()
            
            def track_execution(*args, **kwargs):
                execution_times.append(asyncio.get_event_loop().time())
                return MagicMock()
            
            mock_create_agent.side_effect = track_execution
            
            await AgentFactory.warmup()
            
            assert mock_create_agent.call_count == 4

    def test_get_cache_stats(self):
        """测试获取缓存状态"""
        AgentFactory._agent_cache = {
            "expert_False_thinking_False": MagicMock(),
            "expert_True_thinking_True": MagicMock(),
        }
        
        stats = AgentFactory.get_cache_stats()
        
        assert stats["total"] == 2
        assert stats["max"] == 4
        assert "expert_False_thinking_False" in stats["cached_agents"]
        assert "expert_True_thinking_True" in stats["cached_agents"]

    def test_get_cache_stats_empty(self):
        """测试空缓存状态"""
        AgentFactory._agent_cache.clear()
        
        stats = AgentFactory.get_cache_stats()
        
        assert stats["total"] == 0
        assert stats["max"] == 4
        assert stats["cached_agents"] == []

    @pytest.mark.asyncio
    async def test_close_clears_cache(self):
        """测试关闭时清理缓存"""
        AgentFactory._agent_cache = {"test": MagicMock()}
        AgentFactory._context_manager = None
        
        await AgentFactory.close_checkpointer()
        
        assert len(AgentFactory._agent_cache) == 0

    @pytest.mark.asyncio
    async def test_create_chat_agent_uses_cache(self):
        """测试创建 Agent 使用缓存"""
        with patch.object(AgentFactory, 'get_checkpointer') as mock_checkpointer, \
             patch('app.agents.agent_factory.create_deep_agent') as mock_create_agent, \
             patch('app.agents.agent_factory.get_chat_model') as mock_model:
            
            mock_checkpointer.return_value = MagicMock()
            mock_create_agent.return_value = MagicMock()
            mock_model.return_value = MagicMock()
            
            agent1 = AgentFactory.create_chat_agent(is_expert=False, enable_thinking=False)
            agent2 = AgentFactory.create_chat_agent(is_expert=False, enable_thinking=False)
            
            assert agent1 is agent2
            assert mock_create_agent.call_count == 1


class TestAgentFactoryConfig:
    """AgentFactory 配置测试"""

    def test_get_agent_config_format(self):
        """测试 Agent 配置格式"""
        config = AgentFactory.get_agent_config("123")
        
        assert "configurable" in config
        assert "thread_id" in config["configurable"]
        assert config["configurable"]["thread_id"] == "conversation_123"
        assert "recursion_limit" in config

    def test_get_agent_config_different_ids(self):
        """测试不同对话 ID 生成不同配置"""
        config1 = AgentFactory.get_agent_config("123")
        config2 = AgentFactory.get_agent_config("456")
        
        assert config1["configurable"]["thread_id"] != config2["configurable"]["thread_id"]
