"""Token 黑名单测试"""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from datetime import datetime, timedelta, UTC

from app.core.token_blacklist import TokenBlacklist


class TestTokenBlacklist:
    """TokenBlacklist 类测试"""
    
    @pytest.fixture
    def mock_redis_client(self):
        """模拟 Redis 客户端"""
        with patch('app.core.token_blacklist.redis_client') as mock:
            mock.set = AsyncMock()
            mock.get = AsyncMock(return_value=None)
            mock.delete = AsyncMock()
            mock.exists = AsyncMock(return_value=False)
            mock.client = MagicMock()
            mock.client.ttl = AsyncMock(return_value=-2)
            yield mock
    
    @pytest.fixture
    def valid_token(self):
        """生成有效的测试 Token"""
        from app.core.security import create_access_token
        return create_access_token(data={"sub": "testuser"})
    
    @pytest.mark.asyncio
    async def test_add_token_to_blacklist(self, mock_redis_client, valid_token):
        """测试将 Token 加入黑名单"""
        mock_redis_client.set = AsyncMock()
        
        result = await TokenBlacklist.add(valid_token)
        
        assert result is True
        mock_redis_client.set.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_add_invalid_token(self, mock_redis_client):
        """测试添加无效 Token"""
        result = await TokenBlacklist.add("invalid.token.here")
        
        assert result is False
    
    @pytest.mark.asyncio
    async def test_is_blacklisted_true(self, mock_redis_client, valid_token):
        """测试检查 Token 是否在黑名单中 - 是"""
        mock_redis_client.exists = AsyncMock(return_value=True)
        
        result = await TokenBlacklist.is_blacklisted(valid_token)
        
        assert result is True
        mock_redis_client.exists.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_is_blacklisted_false(self, mock_redis_client, valid_token):
        """测试检查 Token 是否在黑名单中 - 否"""
        mock_redis_client.exists = AsyncMock(return_value=False)
        
        result = await TokenBlacklist.is_blacklisted(valid_token)
        
        assert result is False
    
    @pytest.mark.asyncio
    async def test_is_blacklisted_invalid_token(self, mock_redis_client):
        """测试检查无效 Token - 应返回 True"""
        result = await TokenBlacklist.is_blacklisted("invalid.token.here")
        
        assert result is True
    
    @pytest.mark.asyncio
    async def test_remove_token_from_blacklist(self, mock_redis_client, valid_token):
        """测试从黑名单移除 Token"""
        mock_redis_client.delete = AsyncMock()
        
        result = await TokenBlacklist.remove(valid_token)
        
        assert result is True
        mock_redis_client.delete.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_remove_invalid_token(self, mock_redis_client):
        """测试移除无效 Token"""
        result = await TokenBlacklist.remove("invalid.token.here")
        
        assert result is False
    
    @pytest.mark.asyncio
    async def test_get_ttl(self, mock_redis_client, valid_token):
        """测试获取 TTL"""
        mock_redis_client.client.ttl = AsyncMock(return_value=1800)
        
        ttl = await TokenBlacklist.get_ttl(valid_token)
        
        assert ttl == 1800
    
    @pytest.mark.asyncio
    async def test_get_ttl_not_in_blacklist(self, mock_redis_client, valid_token):
        """测试获取不在黑名单中的 Token TTL"""
        mock_redis_client.client.ttl = AsyncMock(return_value=-2)
        
        ttl = await TokenBlacklist.get_ttl(valid_token)
        
        assert ttl is None
    
    @pytest.mark.asyncio
    async def test_get_ttl_expired(self, mock_redis_client, valid_token):
        """测试获取已过期的 TTL"""
        mock_redis_client.client.ttl = AsyncMock(return_value=-1)
        
        ttl = await TokenBlacklist.get_ttl(valid_token)
        
        assert ttl is None
    
    @pytest.mark.asyncio
    async def test_each_token_has_unique_jti(self):
        """测试每个 Token 都有唯一的 jti"""
        from app.core.security import create_access_token, decode_access_token
        
        token1 = create_access_token(data={"sub": "testuser"})
        token2 = create_access_token(data={"sub": "testuser"})
        
        payload1 = decode_access_token(token1)
        payload2 = decode_access_token(token2)
        
        assert payload1["jti"] != payload2["jti"], "每个 token 应该有唯一的 jti"
        assert payload1["sub"] == payload2["sub"], "sub 应该相同"
    
    @pytest.mark.asyncio
    async def test_logout_does_not_affect_new_token(self, mock_redis_client):
        """测试登出后重新登录的新 Token 不受影响"""
        from app.core.security import create_access_token, decode_access_token
        
        token1 = create_access_token(data={"sub": "testuser"})
        token2 = create_access_token(data={"sub": "testuser"})
        
        payload1 = decode_access_token(token1)
        payload2 = decode_access_token(token2)
        
        jti1 = payload1["jti"]
        jti2 = payload2["jti"]
        
        assert jti1 != jti2, "两个 token 的 jti 应该不同"
        
        blacklisted_keys = set()
        
        async def mock_exists(key):
            return key in blacklisted_keys
        
        async def mock_set(key, value, ttl=None):
            blacklisted_keys.add(key)
        
        mock_redis_client.exists = mock_exists
        mock_redis_client.set = mock_set
        
        await TokenBlacklist.add(token1)
        
        assert await TokenBlacklist.is_blacklisted(token1) is True
        assert await TokenBlacklist.is_blacklisted(token2) is False, "新 token 不应该在黑名单中"
