
import pytest
from app.services.user_service import user_service
from app.schemas.user import UserCreate, UserUpdate
from app.models.user import User


class TestUserService:
    def test_create_user(self, db_session):
        user_create = UserCreate(
            username="testuser",
            email="test@example.com",
            password="testpassword123"
        )
        user = user_service.create_user(db_session, user_create)
        assert user.id is not None
        assert user.username == "testuser"
        assert user.email == "test@example.com"
        assert user.hashed_password is not None
        assert user.hashed_password != "testpassword123"
        assert user.is_active is True
        assert user.is_superuser is False

    def test_get_user(self, db_session):
        user_create = UserCreate(
            username="testuser",
            email="test@example.com",
            password="testpassword123"
        )
        created_user = user_service.create_user(db_session, user_create)
        
        user = user_service.get_user(db_session, created_user.id)
        assert user is not None
        assert user.id == created_user.id
        assert user.username == "testuser"

    def test_get_user_not_found(self, db_session):
        user = user_service.get_user(db_session, 9999)
        assert user is None

    def test_get_user_by_username(self, db_session):
        user_create = UserCreate(
            username="testuser",
            email="test@example.com",
            password="testpassword123"
        )
        user_service.create_user(db_session, user_create)
        
        user = user_service.get_user_by_username(db_session, "testuser")
        assert user is not None
        assert user.username == "testuser"

    def test_get_user_by_username_not_found(self, db_session):
        user = user_service.get_user_by_username(db_session, "nonexistent")
        assert user is None

    def test_get_user_by_email(self, db_session):
        user_create = UserCreate(
            username="testuser",
            email="test@example.com",
            password="testpassword123"
        )
        user_service.create_user(db_session, user_create)
        
        user = user_service.get_user_by_email(db_session, "test@example.com")
        assert user is not None
        assert user.email == "test@example.com"

    def test_authenticate_user_success(self, db_session):
        user_create = UserCreate(
            username="testuser",
            email="test@example.com",
            password="testpassword123"
        )
        user_service.create_user(db_session, user_create)
        
        user = user_service.authenticate_user(db_session, "testuser", "testpassword123")
        assert user is not None
        assert user.username == "testuser"

    def test_authenticate_user_wrong_password(self, db_session):
        user_create = UserCreate(
            username="testuser",
            email="test@example.com",
            password="testpassword123"
        )
        user_service.create_user(db_session, user_create)
        
        user = user_service.authenticate_user(db_session, "testuser", "wrongpassword")
        assert user is None

    def test_authenticate_user_not_found(self, db_session):
        user = user_service.authenticate_user(db_session, "nonexistent", "password")
        assert user is None

    def test_update_user(self, db_session):
        user_create = UserCreate(
            username="testuser",
            email="test@example.com",
            password="testpassword123"
        )
        created_user = user_service.create_user(db_session, user_create)
        
        user_update = UserUpdate(email="newemail@example.com", is_active=False)
        updated_user = user_service.update_user(db_session, created_user.id, user_update)
        
        assert updated_user is not None
        assert updated_user.email == "newemail@example.com"
        assert updated_user.is_active is False

    def test_update_user_not_found(self, db_session):
        user_update = UserUpdate(email="newemail@example.com")
        updated_user = user_service.update_user(db_session, 9999, user_update)
        assert updated_user is None

    def test_delete_user(self, db_session):
        user_create = UserCreate(
            username="testuser",
            email="test@example.com",
            password="testpassword123"
        )
        created_user = user_service.create_user(db_session, user_create)
        
        result = user_service.delete_user(db_session, created_user.id)
        assert result is True
        
        user = user_service.get_user(db_session, created_user.id)
        assert user is None

    def test_delete_user_not_found(self, db_session):
        result = user_service.delete_user(db_session, 9999)
        assert result is False

