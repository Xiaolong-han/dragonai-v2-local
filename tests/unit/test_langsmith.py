"""LangSmith 集成测试"""

import os
import pytest
from unittest.mock import patch


class TestLangSmithEnvVars:
    def test_langsmith_env_vars_loaded(self):
        from dotenv import load_dotenv
        load_dotenv()
        
        if os.environ.get("LANGSMITH_API_KEY"):
            assert os.environ.get("LANGSMITH_TRACING") == "true"
            assert os.environ.get("LANGSMITH_PROJECT") is not None


class TestLangSmithTracing:
    def test_tracing_context(self):
        from langsmith import tracing_context
        
        with tracing_context(enabled=True):
            pass
    
    def test_langsmith_client_initialization(self):
        from langsmith import Client
        
        api_key = os.environ.get("LANGSMITH_API_KEY", "test-key")
        client = Client(
            api_key=api_key,
            api_url="https://api.smith.langchain.com"
        )
        
        assert client is not None


class TestLangSmithIntegration:
    @pytest.mark.asyncio
    async def test_model_invoke_with_tracing(self):
        api_key = os.environ.get("LANGSMITH_API_KEY")
        if not api_key:
            pytest.skip("LANGSMITH_API_KEY not set")
        
        from langsmith import tracing_context
        from app.llm.model_factory import ModelFactory
        
        with tracing_context(enabled=True):
            model = ModelFactory.get_general_model()
            assert model is not None
