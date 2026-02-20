
import pytest
import asyncio
from unittest.mock import patch, MagicMock, AsyncMock
from app.agents.agent_factory import AgentFactory


class TestAgentFactory:
    @pytest.fixture(autouse=True)
    def reset_checkpointer(self):
        AgentFactory._checkpointer = None
        AgentFactory._context_manager = None
        AgentFactory._initialized = False
        yield
        AgentFactory._checkpointer = None
        AgentFactory._context_manager = None
        AgentFactory._initialized = False

    @pytest.fixture
    def mock_async_postgres_saver(self):
        with patch('app.agents.agent_factory.AsyncPostgresSaver') as mock:
            mock_saver = AsyncMock()
            mock_saver.setup = AsyncMock()
            mock_saver.adelete_thread = AsyncMock(return_value=None)
            
            mock_context_manager = AsyncMock()
            mock_context_manager.__aenter__ = AsyncMock(return_value=mock_saver)
            mock_context_manager.__aexit__ = AsyncMock(return_value=None)
            mock.from_conn_string.return_value = mock_context_manager
            yield mock, mock_saver, mock_context_manager

    @pytest.fixture
    def mock_inmemory_saver(self):
        with patch('app.agents.agent_factory.InMemorySaver') as mock:
            mock_saver = MagicMock()
            mock_saver.delete_thread = MagicMock(return_value=None)
            del mock_saver.adelete_thread
            mock.return_value = mock_saver
            yield mock, mock_saver

    @pytest.fixture
    def mock_create_agent(self):
        with patch('app.agents.agent_factory.create_agent') as mock:
            mock_agent = MagicMock()
            mock.return_value = mock_agent
            yield mock

    @pytest.fixture
    def mock_model_factory(self):
        with patch('app.agents.agent_factory.ModelFactory') as mock:
            mock_model = MagicMock()
            mock.get_general_model.return_value = mock_model
            yield mock

    @pytest.mark.asyncio
    async def test_init_checkpointer_with_postgres(self, mock_async_postgres_saver):
        mock_class, mock_saver, mock_cm = mock_async_postgres_saver
        
        with patch('app.agents.agent_factory.settings') as mock_settings:
            mock_settings.database_url = "postgresql://test:test@localhost:5432/test"
            result = await AgentFactory.init_checkpointer()
        
        assert result is True
        mock_class.from_conn_string.assert_called_once()
        mock_cm.__aenter__.assert_called_once()
        mock_saver.setup.assert_called_once()

    @pytest.mark.asyncio
    async def test_init_checkpointer_fallback_to_memory(self, mock_inmemory_saver):
        mock_class, mock_saver = mock_inmemory_saver
        
        with patch('app.agents.agent_factory.AsyncPostgresSaver') as mock_pg:
            mock_pg.from_conn_string.side_effect = Exception("Connection failed")
            
            with patch('app.agents.agent_factory.settings') as mock_settings:
                mock_settings.database_url = "postgresql://test:test@localhost:5432/test"
                result = await AgentFactory.init_checkpointer()
        
        assert result is False
        mock_class.assert_called_once()

    @pytest.mark.asyncio
    async def test_init_checkpointer_no_database_url(self, mock_inmemory_saver):
        mock_class, mock_saver = mock_inmemory_saver
        
        with patch('app.agents.agent_factory.settings') as mock_settings:
            mock_settings.database_url = None
            result = await AgentFactory.init_checkpointer()
        
        assert result is False
        mock_class.assert_called_once()

    @pytest.mark.asyncio
    async def test_close_checkpointer(self, mock_async_postgres_saver):
        mock_class, mock_saver, mock_cm = mock_async_postgres_saver
        
        with patch('app.agents.agent_factory.settings') as mock_settings:
            mock_settings.database_url = "postgresql://test:test@localhost:5432/test"
            await AgentFactory.init_checkpointer()
            await AgentFactory.close_checkpointer()
        
        mock_cm.__aexit__.assert_called_once()
        assert AgentFactory._checkpointer is None
        assert AgentFactory._context_manager is None

    @pytest.mark.asyncio
    async def test_create_chat_agent(self, mock_create_agent, mock_model_factory, mock_async_postgres_saver):
        mock_class, mock_saver, mock_cm = mock_async_postgres_saver
        
        with patch('app.agents.agent_factory.settings') as mock_settings:
            mock_settings.database_url = "postgresql://test:test@localhost:5432/test"
            await AgentFactory.init_checkpointer()
            agent = AgentFactory.create_chat_agent()
        
        assert agent is not None
        mock_create_agent.assert_called_once()
        mock_model_factory.get_general_model.assert_called_once_with(
            is_expert=False,
            thinking=False
        )

    @pytest.mark.asyncio
    async def test_create_chat_agent_with_expert(self, mock_create_agent, mock_model_factory, mock_async_postgres_saver):
        mock_class, mock_saver, mock_cm = mock_async_postgres_saver
        
        with patch('app.agents.agent_factory.settings') as mock_settings:
            mock_settings.database_url = "postgresql://test:test@localhost:5432/test"
            await AgentFactory.init_checkpointer()
            agent = AgentFactory.create_chat_agent(is_expert=True)
        
        assert agent is not None
        mock_model_factory.get_general_model.assert_called_once_with(
            is_expert=True,
            thinking=False
        )

    @pytest.mark.asyncio
    async def test_create_chat_agent_with_thinking(self, mock_create_agent, mock_model_factory, mock_async_postgres_saver):
        mock_class, mock_saver, mock_cm = mock_async_postgres_saver
        
        with patch('app.agents.agent_factory.settings') as mock_settings:
            mock_settings.database_url = "postgresql://test:test@localhost:5432/test"
            await AgentFactory.init_checkpointer()
            agent = AgentFactory.create_chat_agent(enable_thinking=True)
        
        assert agent is not None
        mock_model_factory.get_general_model.assert_called_once_with(
            is_expert=False,
            thinking=True
        )

    def test_get_agent_config(self):
        config = AgentFactory.get_agent_config("test-conversation-id")
        
        assert config == {
            "configurable": {
                "thread_id": "conversation_test-conversation-id"
            }
        }

    @pytest.mark.asyncio
    async def test_reset_conversation_state_with_delete_thread(self, mock_async_postgres_saver):
        mock_class, mock_saver, mock_cm = mock_async_postgres_saver
        
        with patch('app.agents.agent_factory.settings') as mock_settings:
            mock_settings.database_url = "postgresql://test:test@localhost:5432/test"
            await AgentFactory.init_checkpointer()
            result = await AgentFactory.reset_conversation_state("test-id")
        
        assert result is True
        mock_saver.adelete_thread.assert_called_once_with("conversation_test-id")

    @pytest.mark.asyncio
    async def test_reset_conversation_state_with_inmemory(self, mock_inmemory_saver):
        mock_class, mock_saver = mock_inmemory_saver
        mock_saver._storage = {"conversation_test-id": "some_data"}
        
        with patch('app.agents.agent_factory.AsyncPostgresSaver') as mock_pg:
            mock_pg.from_conn_string.side_effect = Exception("Connection failed")
            
            with patch('app.agents.agent_factory.settings') as mock_settings:
                mock_settings.database_url = "postgresql://test:test@localhost:5432/test"
                await AgentFactory.init_checkpointer()
                result = await AgentFactory.reset_conversation_state("test-id")
        
        assert result is True

    @pytest.mark.asyncio
    async def test_reset_conversation_state_not_found(self, mock_inmemory_saver):
        mock_class, mock_saver = mock_inmemory_saver
        mock_saver._storage = {}
        
        with patch('app.agents.agent_factory.AsyncPostgresSaver') as mock_pg:
            mock_pg.from_conn_string.side_effect = Exception("Connection failed")
            
            with patch('app.agents.agent_factory.settings') as mock_settings:
                mock_settings.database_url = "postgresql://test:test@localhost:5432/test"
                await AgentFactory.init_checkpointer()
                result = await AgentFactory.reset_conversation_state("nonexistent-id")
        
        assert result is True
        mock_saver.delete_thread.assert_called_once_with("conversation_nonexistent-id")
