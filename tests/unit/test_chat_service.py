
import pytest
import pytest_asyncio
from unittest.mock import patch, AsyncMock, MagicMock
from app.services.chat_service import chat_service
from app.services.user_service import UserService
from app.services.conversation_service import conversation_service
from app.schemas.message import MessageCreate
from app.schemas.user import UserCreate
from app.schemas.conversation import ConversationCreate
from app.models.user import User
from app.models.conversation import Conversation


@pytest_asyncio.fixture
async def user_service():
    return UserService()


@pytest_asyncio.fixture
async def test_user(db_session, user_service):
    user_create = UserCreate(
        username="testuser",
        email="test@example.com",
        password="testpassword123"
    )
    user = await user_service.create_user(db_session, user_create)
    return user


@pytest_asyncio.fixture
async def test_conversation(db_session, test_user, mock_redis):
    conv_create = ConversationCreate(title="Test Conversation")
    conv = await conversation_service.create_conversation(
        db_session, conv_create, test_user.id
    )
    return conv


@pytest.fixture
def mock_redis():
    mock_redis_client = AsyncMock()
    mock_redis_client.get = AsyncMock(return_value=None)
    mock_redis_client.set = AsyncMock(return_value=None)
    mock_redis_client.delete = AsyncMock(return_value=None)
    mock_redis_client.client = AsyncMock()
    mock_redis_client.client.scan = AsyncMock(return_value=(0, []))
    mock_redis_client.client.delete = AsyncMock(return_value=None)
    
    with patch('app.services.chat_service.redis_client', mock_redis_client), \
         patch('app.services.conversation_service.redis_client', mock_redis_client), \
         patch('app.core.redis.redis_client', mock_redis_client):
        yield mock_redis_client


class MockAgent:
    def __init__(self, responses):
        self.responses = responses
    
    async def astream(self, *args, **kwargs):
        for response in self.responses:
            yield response


@pytest.fixture
def mock_agent_factory():
    from langchain_core.messages.ai import AIMessage
    
    mock_message = AIMessage(content="This is a test response")
    return MockAgent([("updates", {"model": {"messages": [mock_message]}})])


@pytest.fixture
def mock_agent_factory_stream():
    from langchain_core.messages.ai import AIMessageChunk
    
    return MockAgent([
        ("messages", (AIMessageChunk(content="Hello"), {})),
        ("messages", (AIMessageChunk(content=" World"), {}))
    ])


@pytest.fixture
def mock_agent_factory_error():
    class ErrorMockAgent:
        async def astream(self, *args, **kwargs):
            raise Exception("Test error")
            yield
    
    return ErrorMockAgent()


class TestChatService:
    @pytest.mark.asyncio
    async def test_create_message(self, db_session, test_user, test_conversation, mock_redis):
        message_create = MessageCreate(
            role="user",
            content="Hello, world!"
        )
        message = await chat_service.create_message(
            db_session, test_conversation.id, message_create, test_user.id
        )
        assert message is not None
        assert message.id is not None
        assert message.role == "user"
        assert message.content == "Hello, world!"
        assert message.conversation_id == test_conversation.id

    @pytest.mark.asyncio
    async def test_create_message_wrong_conversation(self, db_session, test_user, mock_redis):
        message_create = MessageCreate(role="user", content="Test")
        message = await chat_service.create_message(
            db_session, 9999, message_create, test_user.id
        )
        assert message is None

    @pytest.mark.asyncio
    async def test_get_messages(self, db_session, test_user, test_conversation, mock_redis):
        message_create1 = MessageCreate(role="user", content="Hello")
        message_create2 = MessageCreate(role="assistant", content="Hi there")
        await chat_service.create_message(
            db_session, test_conversation.id, message_create1, test_user.id
        )
        await chat_service.create_message(
            db_session, test_conversation.id, message_create2, test_user.id
        )
        
        messages = await chat_service.get_messages(
            db_session, test_conversation.id, test_user.id
        )
        assert len(messages) == 2

    @pytest.mark.asyncio
    async def test_generate_response(self, db_session, test_user, test_conversation, mock_redis, mock_agent_factory):
        with patch('app.agents.agent_factory.AgentFactory') as mock_factory:
            mock_factory.create_chat_agent.return_value = mock_agent_factory
            mock_factory.get_agent_config.return_value = {"configurable": {"thread_id": "test"}}
            
            response = await chat_service.generate_response(
                conversation_id=test_conversation.id,
                user_id=test_user.id,
                content="Hello"
            )
            assert "This is a test response" in response

    @pytest.mark.asyncio
    async def test_generate_response_stream(self, db_session, test_user, test_conversation, mock_redis, mock_agent_factory_stream):
        with patch('app.agents.agent_factory.AgentFactory') as mock_factory:
            mock_factory.create_chat_agent.return_value = mock_agent_factory_stream
            mock_factory.get_agent_config.return_value = {"configurable": {"thread_id": "test"}}
            
            chunks = []
            async for chunk in chat_service.generate_response_stream(
                conversation_id=test_conversation.id,
                user_id=test_user.id,
                content="Hello"
            ):
                if isinstance(chunk, str):
                    chunks.append(chunk)
            
            assert len(chunks) >= 1

    @pytest.mark.asyncio
    async def test_generate_response_error(self, db_session, test_user, test_conversation, mock_redis, mock_agent_factory_error):
        with patch('app.agents.agent_factory.AgentFactory') as mock_factory:
            mock_factory.create_chat_agent.return_value = mock_agent_factory_error
            mock_factory.get_agent_config.return_value = {"configurable": {"thread_id": "test"}}
            
            response = await chat_service.generate_response(
                conversation_id=test_conversation.id,
                user_id=test_user.id,
                content="Hello"
            )
            assert "Error:" in response
