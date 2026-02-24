
import pytest
import pytest_asyncio
from unittest.mock import patch, AsyncMock
from app.services.conversation_service import conversation_service
from app.services.user_service import UserService
from app.schemas.conversation import ConversationCreate, ConversationUpdate
from app.schemas.user import UserCreate
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


@pytest.fixture
def mock_redis():
    mock_redis_client = AsyncMock()
    mock_redis_client.get = AsyncMock(return_value=None)
    mock_redis_client.set = AsyncMock(return_value=None)
    mock_redis_client.delete = AsyncMock(return_value=None)
    mock_redis_client.client = AsyncMock()
    mock_redis_client.client.scan = AsyncMock(return_value=(0, []))
    mock_redis_client.client.delete = AsyncMock(return_value=None)
    
    with patch('app.services.conversation_service.redis_client', mock_redis_client), \
         patch('app.services.chat_service.redis_client', mock_redis_client), \
         patch('app.core.redis.redis_client', mock_redis_client):
        yield mock_redis_client


class TestConversationService:
    @pytest.mark.asyncio
    async def test_create_conversation(self, db_session, test_user, mock_redis):
        conv_create = ConversationCreate(
            title="Test Conversation",
            model_name="qwen-flash"
        )
        conv = await conversation_service.create_conversation(
            db_session, conv_create, test_user.id
        )
        assert conv.id is not None
        assert conv.title == "Test Conversation"
        assert conv.user_id == test_user.id
        assert conv.model_name == "qwen-flash"
        assert conv.is_pinned is False

    @pytest.mark.asyncio
    async def test_get_conversation(self, db_session, test_user, mock_redis):
        conv_create = ConversationCreate(title="Test Conversation")
        created_conv = await conversation_service.create_conversation(
            db_session, conv_create, test_user.id
        )
        
        conv = await conversation_service.get_conversation(
            db_session, created_conv.id, test_user.id
        )
        assert conv is not None
        assert conv.id == created_conv.id
        assert conv.title == "Test Conversation"

    @pytest.mark.asyncio
    async def test_get_conversation_not_found(self, db_session, test_user, mock_redis):
        conv = await conversation_service.get_conversation(
            db_session, 9999, test_user.id
        )
        assert conv is None

    @pytest.mark.asyncio
    async def test_get_conversation_wrong_user(self, db_session, test_user, mock_redis):
        conv_create = ConversationCreate(title="Test Conversation")
        created_conv = await conversation_service.create_conversation(
            db_session, conv_create, test_user.id
        )
        
        conv = await conversation_service.get_conversation(
            db_session, created_conv.id, 9999
        )
        assert conv is None

    @pytest.mark.asyncio
    async def test_get_conversations(self, db_session, test_user, mock_redis):
        conv1 = ConversationCreate(title="Conv 1")
        conv2 = ConversationCreate(title="Conv 2")
        await conversation_service.create_conversation(db_session, conv1, test_user.id)
        await conversation_service.create_conversation(db_session, conv2, test_user.id)
        
        conversations = await conversation_service.get_conversations(
            db_session, test_user.id
        )
        assert len(conversations) == 2

    @pytest.mark.asyncio
    async def test_update_conversation(self, db_session, test_user, mock_redis):
        conv_create = ConversationCreate(title="Old Title")
        created_conv = await conversation_service.create_conversation(
            db_session, conv_create, test_user.id
        )
        
        conv_update = ConversationUpdate(title="New Title", is_pinned=True)
        updated_conv = await conversation_service.update_conversation(
            db_session, created_conv.id, conv_update, test_user.id
        )
        
        assert updated_conv is not None
        assert updated_conv.title == "New Title"
        assert updated_conv.is_pinned is True

    @pytest.mark.asyncio
    async def test_update_conversation_not_found(self, db_session, test_user, mock_redis):
        conv_update = ConversationUpdate(title="New Title")
        updated_conv = await conversation_service.update_conversation(
            db_session, 9999, conv_update, test_user.id
        )
        assert updated_conv is None

    @pytest.mark.asyncio
    async def test_delete_conversation(self, db_session, test_user, mock_redis):
        conv_create = ConversationCreate(title="Test Conversation")
        created_conv = await conversation_service.create_conversation(
            db_session, conv_create, test_user.id
        )
        
        result = await conversation_service.delete_conversation(
            db_session, created_conv.id, test_user.id
        )
        assert result is True
        
        conv = await conversation_service.get_conversation(
            db_session, created_conv.id, test_user.id
        )
        assert conv is None

    @pytest.mark.asyncio
    async def test_delete_conversation_not_found(self, db_session, test_user, mock_redis):
        result = await conversation_service.delete_conversation(
            db_session, 9999, test_user.id
        )
        assert result is False

    @pytest.mark.asyncio
    async def test_pin_conversation(self, db_session, test_user, mock_redis):
        conv_create = ConversationCreate(title="Test Conversation")
        created_conv = await conversation_service.create_conversation(
            db_session, conv_create, test_user.id
        )
        
        pinned_conv = await conversation_service.pin_conversation(
            db_session, created_conv.id, test_user.id, True
        )
        assert pinned_conv is not None
        assert pinned_conv.is_pinned is True

    @pytest.mark.asyncio
    async def test_pin_conversation_not_found(self, db_session, test_user, mock_redis):
        pinned_conv = await conversation_service.pin_conversation(
            db_session, 9999, test_user.id, True
        )
        assert pinned_conv is None
