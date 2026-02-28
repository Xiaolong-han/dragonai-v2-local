
from pathlib import Path
from typing import List, Optional
from datetime import datetime

from langchain_core.documents import Document
from langchain_chroma import Chroma

from app.config import settings
from app.rag import (
    DocumentLoader,
    DocumentSplitter,
    ModelFactory,
    VectorStoreRetriever,
)
from app.storage.vector_store import vector_store_manager


class KnowledgeService:
    DEFAULT_COLLECTION = "developer_knowledge_base"

    def __init__(
        self,
        collection_name: str = DEFAULT_COLLECTION,
        chunk_size: int = 1000,
        chunk_overlap: int = 200,
    ):
        self.collection_name = collection_name
        self.embeddings = ModelFactory.get_embedding()
        self.document_loader = DocumentLoader()
        self.document_splitter = DocumentSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
        )
        self._vector_store = None

    @property
    def vector_store(self) -> Chroma:
        if self._vector_store is None:
            self._vector_store = vector_store_manager.get_chroma_vector_store(
                collection_name=self.collection_name,
                embedding_function=self.embeddings,
            )
        return self._vector_store

    @property
    def retriever(self) -> VectorStoreRetriever:
        return VectorStoreRetriever(self.vector_store)

    async def upload_document(
        self,
        file_path: str,
        metadata: Optional[dict] = None,
    ) -> int:
        if metadata is None:
            metadata = {}
        
        metadata["uploaded_at"] = datetime.now().isoformat()
        
        documents = self.document_loader.load_file(file_path)
        
        for doc in documents:
            doc.metadata.update(metadata)
        
        split_docs = self.document_splitter.split_documents(documents)
        
        if split_docs:
            self.vector_store.add_documents(split_docs)
        
        return len(split_docs)

    async def upload_directory(
        self,
        dir_path: str,
        recursive: bool = False,
        metadata: Optional[dict] = None,
    ) -> int:
        if metadata is None:
            metadata = {}
        
        metadata["uploaded_at"] = datetime.now().isoformat()
        
        documents = self.document_loader.load_directory(dir_path, recursive=recursive)
        
        for doc in documents:
            doc.metadata.update(metadata)
        
        split_docs = self.document_splitter.split_documents(documents)
        
        if split_docs:
            self.vector_store.add_documents(split_docs)
        
        return len(split_docs)

    async def add_documents(self, documents: List[Document]) -> int:
        for doc in documents:
            if "uploaded_at" not in doc.metadata:
                doc.metadata["uploaded_at"] = datetime.now().isoformat()
        
        split_docs = self.document_splitter.split_documents(documents)
        
        if split_docs:
            self.vector_store.add_documents(split_docs)
        
        return len(split_docs)

    async def search(self, query: str, k: int = 4) -> List[Document]:
        return await self.retriever.aretrieve(query, k=k)

    async def search_with_score(
        self,
        query: str,
        k: int = 4,
    ) -> List[tuple[Document, float]]:
        return self.retriever.similarity_search_with_score(query, k=k)

    async def delete_collection(self):
        vector_store_manager.delete_collection(self.collection_name)
        self._vector_store = None

    async def get_collection_stats(self) -> dict:
        collection = self.vector_store._collection
        return {
            "collection_name": self.collection_name,
            "document_count": collection.count(),
        }

    async def save_uploaded_file(self, file, filename: str) -> str:
        storage_dir = Path(settings.storage_dir) / "knowledge_base"
        storage_dir.mkdir(parents=True, exist_ok=True)
        
        file_path = storage_dir / filename
        
        content = await file.read()
        with open(file_path, "wb") as f:
            f.write(content)
        
        return f"/storage/knowledge_base/{filename}"


def get_knowledge_service() -> KnowledgeService:
    return KnowledgeService()
