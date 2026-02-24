"""请求限流中间件测试"""

import pytest
from fastapi import FastAPI, Request
from fastapi.testclient import TestClient
from app.core.rate_limit import limiter, get_client_identifier


class TestRateLimit:
    def test_get_client_identifier_with_user(self, mock_request):
        mock_request.state.user = type('User', (), {'id': 1})()
        identifier = get_client_identifier(mock_request)
        assert identifier == "user:1"
    
    def test_get_client_identifier_with_forwarded_header(self, mock_request):
        mock_request.headers = {"X-Forwarded-For": "192.168.1.1, 10.0.0.1"}
        identifier = get_client_identifier(mock_request)
        assert identifier == "192.168.1.1"
    
    def test_get_client_identifier_with_remote_address(self, mock_request):
        identifier = get_client_identifier(mock_request)
        assert identifier == "127.0.0.1"
    
    def test_limiter_initialization(self):
        assert limiter is not None
        assert limiter._key_func == get_client_identifier
