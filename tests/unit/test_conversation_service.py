
import pytest
import pytest_asyncio
from unittest.mock import patch, AsyncMock
from app.services.conversation_service import conversation_service
from app.schemas.conversation import ConversationCreate, ConversationUpdate
from app.models.user import User
from app.models.conversation import Conversation


class TestConversationService:
    @pytest.fixture(autouse=True)
    def setup_user(self, db_session):
        from app.services.user_service import user_service
        from app.schemas.user import UserCreate
        user_create = UserCreate(
            username="testuser",
            email="test@example.com",
            password="testpassword123"
        )
        self.user = user_service.create_user(db_session, user_create)
        self.user_id = self.user.id

    @pytest.fixture
    def mock_redis(self):
        with patch('app.services.conversation_service.redis_client') as mock:
            mock.get = AsyncMock(return_value=None)
            mock.set = AsyncMock(return_value=None)
            mock.delete = AsyncMock(return_value=None)
            mock.scan = AsyncMock(return_value=(0, []))
            yield mock

    @pytest.mark.asyncio
    async def test_create_conversation(self, db_session, mock_redis):
        conv_create = ConversationCreate(
            title="Test Conversation",
            model_name="qwen-flash"
        )
        conv = await conversation_service.create_conversation(
            db_session, conv_create, self.user_id
        )
        assert conv.id is not None
        assert conv.title == "Test Conversation"
        assert conv.user_id == self.user_id
        assert conv.model_name == "qwen-flash"
        assert conv.is_pinned is False

    @pytest.mark.asyncio
    async def test_get_conversation(self, db_session, mock_redis):
        conv_create = ConversationCreate(title="Test Conversation")
        created_conv = await conversation_service.create_conversation(
            db_session, conv_create, self.user_id
        )
        
        conv = await conversation_service.get_conversation(
            db_session, created_conv.id, self.user_id
        )
        assert conv is not None
        assert conv.id == created_conv.id
        assert conv.title == "Test Conversation"

    @pytest.mark.asyncio
    async def test_get_conversation_not_found(self, db_session, mock_redis):
        conv = await conversation_service.get_conversation(
            db_session, 9999, self.user_id
        )
        assert conv is None

    @pytest.mark.asyncio
    async def test_get_conversation_wrong_user(self, db_session, mock_redis):
        conv_create = ConversationCreate(title="Test Conversation")
        created_conv = await conversation_service.create_conversation(
            db_session, conv_create, self.user_id
        )
        
        conv = await conversation_service.get_conversation(
            db_session, created_conv.id, 9999
        )
        assert conv is None

    @pytest.mark.asyncio
    async def test_get_conversations(self, db_session, mock_redis):
        conv1 = ConversationCreate(title="Conv 1")
        conv2 = ConversationCreate(title="Conv 2")
        await conversation_service.create_conversation(db_session, conv1, self.user_id)
        await conversation_service.create_conversation(db_session, conv2, self.user_id)
        
        conversations = await conversation_service.get_conversations(
            db_session, self.user_id
        )
        assert len(conversations) == 2

    @pytest.mark.asyncio
    async def test_update_conversation(self, db_session, mock_redis):
        conv_create = ConversationCreate(title="Old Title")
        created_conv = await conversation_service.create_conversation(
            db_session, conv_create, self.user_id
        )
        
        conv_update = ConversationUpdate(title="New Title", is_pinned=True)
        updated_conv = await conversation_service.update_conversation(
            db_session, created_conv.id, conv_update, self.user_id
        )
        
        assert updated_conv is not None
        assert updated_conv.title == "New Title"
        assert updated_conv.is_pinned is True

    @pytest.mark.asyncio
    async def test_update_conversation_not_found(self, db_session, mock_redis):
        conv_update = ConversationUpdate(title="New Title")
        updated_conv = await conversation_service.update_conversation(
            db_session, 9999, conv_update, self.user_id
        )
        assert updated_conv is None

    @pytest.mark.asyncio
    async def test_delete_conversation(self, db_session, mock_redis):
        conv_create = ConversationCreate(title="Test Conversation")
        created_conv = await conversation_service.create_conversation(
            db_session, conv_create, self.user_id
        )
        
        result = await conversation_service.delete_conversation(
            db_session, created_conv.id, self.user_id
        )
        assert result is True
        
        conv = await conversation_service.get_conversation(
            db_session, created_conv.id, self.user_id
        )
        assert conv is None

    @pytest.mark.asyncio
    async def test_delete_conversation_not_found(self, db_session, mock_redis):
        result = await conversation_service.delete_conversation(
            db_session, 9999, self.user_id
        )
        assert result is False

    @pytest.mark.asyncio
    async def test_pin_conversation(self, db_session, mock_redis):
        conv_create = ConversationCreate(title="Test Conversation")
        created_conv = await conversation_service.create_conversation(
            db_session, conv_create, self.user_id
        )
        
        pinned_conv = await conversation_service.pin_conversation(
            db_session, created_conv.id, self.user_id, True
        )
        assert pinned_conv is not None
        assert pinned_conv.is_pinned is True

    @pytest.mark.asyncio
    async def test_pin_conversation_not_found(self, db_session, mock_redis):
        pinned_conv = await conversation_service.pin_conversation(
            db_session, 9999, self.user_id, True
        )
        assert pinned_conv is None

