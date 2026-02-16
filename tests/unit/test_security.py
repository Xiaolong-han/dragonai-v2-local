
import pytest
from datetime import timedelta
from app.core.security import (
    verify_password,
    get_password_hash,
    create_access_token,
    decode_access_token,
)


class TestSecurity:
    def test_password_hashing(self):
        password = "testpassword123"
        hashed = get_password_hash(password)
        assert hashed != password
        assert len(hashed) > 0

    def test_verify_password_success(self):
        password = "testpassword123"
        hashed = get_password_hash(password)
        assert verify_password(password, hashed) is True

    def test_verify_password_failure(self):
        password = "testpassword123"
        hashed = get_password_hash(password)
        assert verify_password("wrongpassword", hashed) is False

    def test_create_access_token(self, test_settings):
        data = {"sub": "testuser"}
        token = create_access_token(data=data)
        assert token is not None
        assert len(token) > 0

    def test_create_access_token_with_expiration(self, test_settings):
        data = {"sub": "testuser"}
        expires_delta = timedelta(minutes=15)
        token = create_access_token(data=data, expires_delta=expires_delta)
        assert token is not None
        assert len(token) > 0

    def test_decode_access_token(self, test_settings):
        data = {"sub": "testuser"}
        token = create_access_token(data=data)
        payload = decode_access_token(token)
        assert payload is not None
        assert payload["sub"] == "testuser"

    def test_decode_access_token_invalid(self, test_settings):
        payload = decode_access_token("invalid.token.here")
        assert payload is None

