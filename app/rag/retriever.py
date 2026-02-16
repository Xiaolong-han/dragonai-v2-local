
from typing import List, Optional
from langchain_core.documents import Document
from langchain_core.vectorstores import VectorStore
from langchain_core.retrievers import BaseRetriever


class VectorStoreRetriever:
    def __init__(
        self,
        vector_store: VectorStore,
        search_type: str = "similarity",
        search_kwargs: dict = None,
    ):
        self.vector_store = vector_store
        self.search_type = search_type
        self.search_kwargs = search_kwargs or {}

    def get_retriever(self) -> BaseRetriever:
        return self.vector_store.as_retriever(
            search_type=self.search_type,
            search_kwargs=self.search_kwargs
        )

    def retrieve(self, query: str, k: int = 4) -> List[Document]:
        retriever = self.get_retriever()
        if k != 4:
            retriever.search_kwargs["k"] = k
        return retriever.invoke(query)

    async def aretrieve(self, query: str, k: int = 4) -> List[Document]:
        retriever = self.get_retriever()
        if k != 4:
            retriever.search_kwargs["k"] = k
        return await retriever.ainvoke(query)

    def similarity_search(
        self,
        query: str,
        k: int = 4,
        filter: Optional[dict] = None,
    ) -> List[Document]:
        return self.vector_store.similarity_search(
            query=query,
            k=k,
            filter=filter
        )

    def similarity_search_with_score(
        self,
        query: str,
        k: int = 4,
        filter: Optional[dict] = None,
    ) -> List[tuple[Document, float]]:
        return self.vector_store.similarity_search_with_score(
            query=query,
            k=k,
            filter=filter
        )

    def max_marginal_relevance_search(
        self,
        query: str,
        k: int = 4,
        fetch_k: int = 20,
        lambda_mult: float = 0.5,
        filter: Optional[dict] = None,
    ) -> List[Document]:
        return self.vector_store.max_marginal_relevance_search(
            query=query,
            k=k,
            fetch_k=fetch_k,
            lambda_mult=lambda_mult,
            filter=filter
        )

