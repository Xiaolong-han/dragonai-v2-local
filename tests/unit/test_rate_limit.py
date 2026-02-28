"""请求限流中间件测试"""

import pytest
from fastapi import FastAPI, Request
from fastapi.testclient import TestClient
from app.core.rate_limit import limiter, get_client_identifier, get_storage_uri, CHAT_RATE_LIMIT, AUTH_RATE_LIMIT
from app.config import settings


class TestRateLimit:
    def test_get_client_identifier_with_user(self, mock_request):
        mock_request.state.user = type('User', (), {'id': 1})()
        identifier = get_client_identifier(mock_request)
        assert identifier == "user:1"
    
    def test_get_client_identifier_with_forwarded_header(self, mock_request):
        mock_request.headers = {"X-Forwarded-For": "192.168.1.1, 10.0.0.1"}
        identifier = get_client_identifier(mock_request)
        assert identifier == "ip:192.168.1.1"
    
    def test_get_client_identifier_with_remote_address(self, mock_request):
        identifier = get_client_identifier(mock_request)
        assert identifier == "ip:127.0.0.1"
    
    def test_limiter_initialization(self):
        assert limiter is not None
        assert limiter._key_func == get_client_identifier
    
    def test_storage_uri_redis(self, monkeypatch):
        monkeypatch.setattr(settings, 'rate_limit_storage', 'redis')
        uri = get_storage_uri()
        assert uri == settings.redis_url
    
    def test_storage_uri_memory(self, monkeypatch):
        monkeypatch.setattr(settings, 'rate_limit_storage', 'memory')
        uri = get_storage_uri()
        assert uri == "memory://"
    
    def test_rate_limit_constants_from_config(self):
        assert CHAT_RATE_LIMIT == settings.rate_limit_chat
        assert AUTH_RATE_LIMIT == settings.rate_limit_auth
