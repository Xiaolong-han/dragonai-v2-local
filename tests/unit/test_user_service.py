
import pytest
import pytest_asyncio
from app.services.user_service import UserService
from app.schemas.user import UserCreate, UserUpdate
from app.models.user import User


@pytest_asyncio.fixture
async def user_service():
    return UserService()


class TestUserService:
    @pytest.mark.asyncio
    async def test_create_user(self, db_session, user_service):
        user_create = UserCreate(
            username="testuser",
            email="test@example.com",
            password="testpassword123"
        )
        user = await user_service.create_user(db_session, user_create)
        assert user.id is not None
        assert user.username == "testuser"
        assert user.email == "test@example.com"
        assert user.hashed_password is not None
        assert user.hashed_password != "testpassword123"
        assert user.is_active is True
        assert user.is_superuser is False

    @pytest.mark.asyncio
    async def test_get_user(self, db_session, user_service):
        user_create = UserCreate(
            username="testuser",
            email="test@example.com",
            password="testpassword123"
        )
        created_user = await user_service.create_user(db_session, user_create)
        
        user = await user_service.get_user(db_session, created_user.id)
        assert user is not None
        assert user.id == created_user.id
        assert user.username == "testuser"

    @pytest.mark.asyncio
    async def test_get_user_not_found(self, db_session, user_service):
        user = await user_service.get_user(db_session, 9999)
        assert user is None

    @pytest.mark.asyncio
    async def test_get_user_by_username(self, db_session, user_service):
        user_create = UserCreate(
            username="testuser",
            email="test@example.com",
            password="testpassword123"
        )
        await user_service.create_user(db_session, user_create)
        
        user = await user_service.get_user_by_username(db_session, "testuser")
        assert user is not None
        assert user.username == "testuser"

    @pytest.mark.asyncio
    async def test_get_user_by_username_not_found(self, db_session, user_service):
        user = await user_service.get_user_by_username(db_session, "nonexistent")
        assert user is None

    @pytest.mark.asyncio
    async def test_get_user_by_email(self, db_session, user_service):
        user_create = UserCreate(
            username="testuser",
            email="test@example.com",
            password="testpassword123"
        )
        await user_service.create_user(db_session, user_create)
        
        user = await user_service.get_user_by_email(db_session, "test@example.com")
        assert user is not None
        assert user.email == "test@example.com"

    @pytest.mark.asyncio
    async def test_authenticate_user_success(self, db_session, user_service):
        user_create = UserCreate(
            username="testuser",
            email="test@example.com",
            password="testpassword123"
        )
        await user_service.create_user(db_session, user_create)
        
        user = await user_service.authenticate_user(db_session, "testuser", "testpassword123")
        assert user is not None
        assert user.username == "testuser"

    @pytest.mark.asyncio
    async def test_authenticate_user_wrong_password(self, db_session, user_service):
        user_create = UserCreate(
            username="testuser",
            email="test@example.com",
            password="testpassword123"
        )
        await user_service.create_user(db_session, user_create)
        
        user = await user_service.authenticate_user(db_session, "testuser", "wrongpassword")
        assert user is None

    @pytest.mark.asyncio
    async def test_authenticate_user_not_found(self, db_session, user_service):
        user = await user_service.authenticate_user(db_session, "nonexistent", "password")
        assert user is None

    @pytest.mark.asyncio
    async def test_update_user(self, db_session, user_service):
        user_create = UserCreate(
            username="testuser",
            email="test@example.com",
            password="testpassword123"
        )
        created_user = await user_service.create_user(db_session, user_create)
        
        user_update = UserUpdate(email="newemail@example.com", is_active=False)
        updated_user = await user_service.update_user(db_session, created_user.id, user_update)
        
        assert updated_user is not None
        assert updated_user.email == "newemail@example.com"
        assert updated_user.is_active is False

    @pytest.mark.asyncio
    async def test_update_user_not_found(self, db_session, user_service):
        user_update = UserUpdate(email="newemail@example.com")
        updated_user = await user_service.update_user(db_session, 9999, user_update)
        assert updated_user is None

    @pytest.mark.asyncio
    async def test_delete_user(self, db_session, user_service):
        user_create = UserCreate(
            username="testuser",
            email="test@example.com",
            password="testpassword123"
        )
        created_user = await user_service.create_user(db_session, user_create)
        
        result = await user_service.delete_user(db_session, created_user.id)
        assert result is True
        
        user = await user_service.get_user(db_session, created_user.id)
        assert user is None

    @pytest.mark.asyncio
    async def test_delete_user_not_found(self, db_session, user_service):
        result = await user_service.delete_user(db_session, 9999)
        assert result is False
