
import pytest
from unittest.mock import patch, MagicMock
from app.agents.agent_factory import AgentFactory, AgentType, create_general_agent


class TestAgentFactory:
    @pytest.fixture
    def mock_llm(self):
        with patch('app.agents.agent_factory.QwenGeneralModel') as mock:
            mock_llm = MagicMock()
            mock.qwen_flash.return_value = mock_llm
            mock.qwen3_max.return_value = mock_llm
            yield mock

    @pytest.fixture
    def mock_agent_saver(self):
        with patch('app.agents.agent_factory.agent_saver_manager') as mock:
            mock_saver = MagicMock()
            mock.get_postgres_saver.return_value = mock_saver
            yield mock

    @pytest.fixture
    def mock_create_agent(self):
        with patch('app.agents.agent_factory.create_agent') as mock:
            mock_agent = MagicMock()
            mock.return_value = mock_agent
            yield mock

    def test_create_general_agent_qwen_flash(self, mock_llm, mock_agent_saver, mock_create_agent):
        agent = create_general_agent(
            model_name="qwen-flash",
            use_postgres_saver=False
        )
        mock_create_agent.assert_called_once()
        assert agent is not None

    def test_create_general_agent_qwen3_max(self, mock_llm, mock_agent_saver, mock_create_agent):
        agent = create_general_agent(
            model_name="qwen3-max",
            use_postgres_saver=False
        )
        mock_create_agent.assert_called_once()
        assert agent is not None

    def test_create_general_agent_invalid_model(self):
        with pytest.raises(ValueError):
            create_general_agent(model_name="invalid-model")

    def test_agent_factory_create_general(self, mock_llm, mock_agent_saver, mock_create_agent):
        agent = AgentFactory.create_agent(
            agent_type=AgentType.GENERAL,
            use_postgres_saver=False
        )
        mock_create_agent.assert_called_once()
        assert agent is not None

    def test_agent_factory_create_code(self, mock_llm, mock_agent_saver, mock_create_agent):
        agent = AgentFactory.create_agent(
            agent_type=AgentType.CODE,
            use_postgres_saver=False
        )
        assert agent is not None

    def test_agent_factory_create_translation(self, mock_llm, mock_agent_saver, mock_create_agent):
        agent = AgentFactory.create_agent(
            agent_type=AgentType.TRANSLATION,
            use_postgres_saver=False
        )
        assert agent is not None

    def test_agent_factory_create_image(self, mock_llm, mock_agent_saver, mock_create_agent):
        agent = AgentFactory.create_agent(
            agent_type=AgentType.IMAGE,
            use_postgres_saver=False
        )
        assert agent is not None

    def test_agent_factory_with_thinking(self, mock_llm, mock_agent_saver, mock_create_agent):
        agent = AgentFactory.create_agent(
            agent_type=AgentType.GENERAL,
            thinking=True,
            use_postgres_saver=False
        )
        assert agent is not None

    def test_agent_factory_with_postgres_saver(self, mock_llm, mock_agent_saver, mock_create_agent):
        agent = AgentFactory.create_agent(
            agent_type=AgentType.GENERAL,
            use_postgres_saver=True
        )
        assert agent is not None

