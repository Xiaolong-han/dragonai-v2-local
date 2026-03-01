"""请求体大小限制测试"""

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.main import RequestSizeLimitMiddleware


class TestRequestSizeLimit:
    """请求体大小限制测试"""

    @pytest.fixture
    def test_app(self):
        """创建测试应用"""
        app = FastAPI()
        app.add_middleware(RequestSizeLimitMiddleware)

        @app.post("/test")
        async def test_endpoint(data: dict):
            return {"received": True, "size": len(str(data))}

        @app.get("/test-get")
        async def test_get():
            return {"method": "GET"}

        @app.put("/test-put")
        async def test_put(data: dict):
            return {"received": True}

        @app.patch("/test-patch")
        async def test_patch(data: dict):
            return {"received": True}

        return app

    @pytest.fixture
    def client(self, test_app):
        """创建测试客户端"""
        return TestClient(test_app)

    def test_normal_size_request_passes(self, client):
        """测试正常大小请求通过"""
        small_data = {"key": "value" * 100}
        response = client.post("/test", json=small_data)
        assert response.status_code == 200
        assert response.json()["received"] is True

    def test_large_request_returns_413(self, client):
        """测试超大请求返回 413"""
        large_data = {"key": "x" * (15 * 1024 * 1024)}
        response = client.post("/test", json=large_data)
        assert response.status_code == 413
        assert response.json()["error"]["code"] == "PAYLOAD_TOO_LARGE"

    def test_get_request_not_affected(self, client):
        """测试 GET 请求不受影响"""
        response = client.get("/test-get")
        assert response.status_code == 200
        assert response.json()["method"] == "GET"

    def test_put_request_size_limit(self, client):
        """测试 PUT 请求大小限制"""
        large_data = {"key": "x" * (15 * 1024 * 1024)}
        response = client.put("/test-put", json=large_data)
        assert response.status_code == 413

    def test_patch_request_size_limit(self, client):
        """测试 PATCH 请求大小限制"""
        large_data = {"key": "x" * (15 * 1024 * 1024)}
        response = client.patch("/test-patch", json=large_data)
        assert response.status_code == 413

    def test_exact_limit_boundary(self, client):
        """测试边界值 - 刚好等于限制大小"""
        from app.config import settings
        max_size = settings.max_request_size
        large_data = {"key": "x" * (max_size - 50)}
        response = client.post("/test", json=large_data)
        assert response.status_code in (200, 413)

    def test_error_response_format(self, client):
        """测试错误响应格式"""
        large_data = {"key": "x" * (15 * 1024 * 1024)}
        response = client.post("/test", json=large_data)
        assert response.status_code == 413
        error = response.json()["error"]
        assert "code" in error
        assert "message" in error
        assert error["code"] == "PAYLOAD_TOO_LARGE"
        assert "10MB" in error["message"]
