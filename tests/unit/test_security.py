
import pytest
from datetime import timedelta
from unittest.mock import patch
from app.core.security import (
    verify_password,
    get_password_hash,
    create_access_token,
    decode_access_token,
    generate_file_signature,
    verify_file_signature,
    generate_signed_url,
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


class TestFileSignature:
    """文件签名测试"""
    
    def test_generate_file_signature(self):
        """测试生成文件签名"""
        import time
        expires = int(time.time()) + 3600
        signature = generate_file_signature("test.txt", expires)
        assert signature is not None
        assert len(signature) > 0
    
    def test_verify_file_signature_valid(self):
        """测试验证有效签名"""
        import time
        expires = int(time.time()) + 3600
        signature = generate_file_signature("test.txt", expires)
        assert verify_file_signature("test.txt", expires, signature) is True
    
    def test_verify_file_signature_expired(self):
        """测试验证过期签名"""
        import time
        expires = int(time.time()) - 3600
        signature = generate_file_signature("test.txt", expires)
        assert verify_file_signature("test.txt", expires, signature) is False
    
    def test_verify_file_signature_invalid(self):
        """测试验证无效签名"""
        import time
        expires = int(time.time()) + 3600
        assert verify_file_signature("test.txt", expires, "invalid_signature") is False
    
    def test_verify_file_signature_path_traversal(self):
        """测试路径遍历攻击防护"""
        import time
        expires = int(time.time()) + 3600
        signature = generate_file_signature("../../../etc/passwd", expires)
        assert verify_file_signature("../../../etc/passwd", expires, signature) is False
    
    def test_generate_signed_url_valid_path(self):
        """测试生成有效路径的签名URL"""
        url = generate_signed_url("documents/test.txt")
        assert "/api/v1/files/serve/" in url
        assert "expires=" in url
        assert "signature=" in url
    
    def test_generate_signed_url_path_traversal(self):
        """测试生成路径遍历URL应抛出异常"""
        with pytest.raises(ValueError) as exc_info:
            generate_signed_url("../../../etc/passwd")
        assert "Access denied" in str(exc_info.value)
    
    def test_generate_signed_url_absolute_path_outside_sandbox(self):
        """测试生成沙箱外绝对路径URL应抛出异常"""
        with pytest.raises(ValueError) as exc_info:
            generate_signed_url("C:/Windows/System32/config/SAM")
        assert "Access denied" in str(exc_info.value)
