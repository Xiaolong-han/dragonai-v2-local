
from typing import List
from langchain_core.embeddings import Embeddings
from openai import AsyncOpenAI, OpenAI

from app.config import settings


class QwenEmbeddings(Embeddings):
    def __init__(
        self,
        model_name: str = "text-embedding-v3",
        api_key: str = None,
        base_url: str = None,
    ):
        self.model_name = model_name
        self.api_key = api_key or settings.qwen_api_key
        self.base_url = base_url or settings.qwen_base_url
        
        if not self.api_key:
            raise ValueError("Qwen API key is required")
        
        self._client = None
        self._async_client = None

    def _get_client(self):
        if self._client is None:
            self._client = OpenAI(
                api_key=self.api_key,
                base_url=self.base_url
            )
        return self._client

    def _get_async_client(self):
        if self._async_client is None:
            self._async_client = AsyncOpenAI(
                api_key=self.api_key,
                base_url=self.base_url
            )
        return self._async_client

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        client = self._get_client()
        response = client.embeddings.create(
            model=self.model_name,
            input=texts
        )
        return [data.embedding for data in response.data]

    async def aembed_documents(self, texts: List[str]) -> List[List[float]]:
        client = self._get_async_client()
        response = await client.embeddings.create(
            model=self.model_name,
            input=texts
        )
        return [data.embedding for data in response.data]

    def embed_query(self, text: str) -> List[float]:
        client = self._get_client()
        response = client.embeddings.create(
            model=self.model_name,
            input=[text]
        )
        return response.data[0].embedding

    async def aembed_query(self, text: str) -> List[float]:
        client = self._get_async_client()
        response = await client.embeddings.create(
            model=self.model_name,
            input=[text]
        )
        return response.data[0].embedding

