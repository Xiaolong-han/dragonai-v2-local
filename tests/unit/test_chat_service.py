
import pytest
import pytest_asyncio
from unittest.mock import patch, AsyncMock, MagicMock
from app.services.chat_service import chat_service
from app.schemas.message import MessageCreate
from app.models.user import User
from app.models.conversation import Conversation


class TestChatService:
    @pytest_asyncio.fixture(autouse=True)
    async def setup_data(self, db_session, mock_redis):
        from app.services.user_service import user_service
        from app.services.conversation_service import conversation_service
        from app.schemas.user import UserCreate
        from app.schemas.conversation import ConversationCreate
        
        user_create = UserCreate(
            username="testuser",
            email="test@example.com",
            password="testpassword123"
        )
        self.user = user_service.create_user(db_session, user_create)
        self.user_id = self.user.id
        
        conv_create = ConversationCreate(title="Test Conversation")
        self.conv = await conversation_service.create_conversation(
            db_session, conv_create, self.user_id
        )
        self.conversation_id = self.conv.id

    @pytest.fixture(autouse=True)
    def mock_redis(self):
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

    @pytest.fixture
    def mock_model_factory(self):
        with patch('app.services.chat_service.ModelFactory') as mock:
            mock_model = MagicMock()
            mock_model.astream = AsyncMock()
            mock_model.ainvoke = AsyncMock()
            mock.get_general_model.return_value = mock_model
            mock.get_vision_model.return_value = mock_model
            yield mock

    @pytest.mark.asyncio
    async def test_create_message(self, db_session, mock_redis):
        message_create = MessageCreate(
            role="user",
            content="Hello, world!"
        )
        message = await chat_service.create_message(
            db_session, self.conversation_id, message_create, self.user_id
        )
        assert message is not None
        assert message.id is not None
        assert message.role == "user"
        assert message.content == "Hello, world!"
        assert message.conversation_id == self.conversation_id

    @pytest.mark.asyncio
    async def test_create_message_wrong_conversation(self, db_session, mock_redis):
        message_create = MessageCreate(role="user", content="Test")
        message = await chat_service.create_message(
            db_session, 9999, message_create, self.user_id
        )
        assert message is None

    @pytest.mark.asyncio
    async def test_get_messages(self, db_session, mock_redis):
        message_create1 = MessageCreate(role="user", content="Hello")
        message_create2 = MessageCreate(role="assistant", content="Hi there")
        await chat_service.create_message(
            db_session, self.conversation_id, message_create1, self.user_id
        )
        await chat_service.create_message(
            db_session, self.conversation_id, message_create2, self.user_id
        )
        
        messages = await chat_service.get_messages(
            db_session, self.conversation_id, self.user_id
        )
        assert len(messages) == 2

    @pytest.mark.asyncio
    async def test_generate_response(self, db_session, mock_model_factory):
        mock_response = MagicMock()
        mock_response.content = "This is a test response"
        mock_model_factory.get_general_model.return_value.ainvoke.return_value = mock_response
        
        response = await chat_service.generate_response(
            conversation_id=self.conversation_id,
            user_id=self.user_id,
            content="Hello"
        )
        assert response == "This is a test response"

    @pytest.mark.asyncio
    async def test_generate_response_stream(self, db_session, mock_model_factory):
        mock_chunk1 = MagicMock()
        mock_chunk1.content = "Hello"
        mock_chunk2 = MagicMock()
        mock_chunk2.content = " World"
        
        async def mock_astream(messages):
            yield mock_chunk1
            yield mock_chunk2
        
        mock_model_factory.get_general_model.return_value.astream = mock_astream
        
        chunks = []
        async for chunk in chat_service.generate_response_stream(
            conversation_id=self.conversation_id,
            user_id=self.user_id,
            content="Hello"
        ):
            chunks.append(chunk)
        
        assert chunks == ["Hello", " World"]

    @pytest.mark.asyncio
    async def test_generate_response_error(self, db_session, mock_model_factory):
        mock_model_factory.get_general_model.return_value.ainvoke.side_effect = Exception("Test error")
        
        response = await chat_service.generate_response(
            conversation_id=self.conversation_id,
            user_id=self.user_id,
            content="Hello"
        )
        assert "Error: Test error" in response

