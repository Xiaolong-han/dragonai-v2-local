
from pathlib import Path
from typing import List, Optional
from datetime import datetime
import hashlib
import logging
import aiofiles

from langchain_core.documents import Document
from langchain_chroma import Chroma
from langchain_community.embeddings import DashScopeEmbeddings

from app.config import settings
from app.rag import (
    DocumentLoader,
    DocumentSplitter,
    HybridRetriever,
    get_reranker,
    BaseReranker,
)
from app.storage.vector_store import vector_store_manager

logger = logging.getLogger(__name__)


def get_embeddings(model_name: str = None, **kwargs) -> DashScopeEmbeddings:
    """获取 Embedding 模型
    
    Args:
        model_name: 模型名称，默认使用配置中的 model_embedding
    """
    return DashScopeEmbeddings(
        model=model_name or settings.model_embedding,
        dashscope_api_key=settings.qwen_api_key,
        **kwargs
    )

_knowledge_service_instance: Optional["KnowledgeService"] = None


class KnowledgeService:
    DEFAULT_COLLECTION = "developer_knowledge_base"

    def __init__(
        self,
        collection_name: str = None,
        chunk_size: int = None,
        chunk_overlap: int = None,
    ):
        self.collection_name = collection_name or self.DEFAULT_COLLECTION
        self.embeddings = get_embeddings()
        self.document_loader = DocumentLoader()
        self.document_splitter = DocumentSplitter(
            chunk_size=chunk_size or 1000,
            chunk_overlap=chunk_overlap or 200,
        )
        self._vector_store = None
        
        self.enable_hybrid = settings.rag_enable_hybrid
        self.hybrid_alpha = settings.rag_hybrid_alpha
        self._hybrid_retriever = None
        
        self.enable_rerank = settings.rag_enable_rerank
        self.rerank_provider = settings.rag_rerank_provider
        self.rerank_model = settings.rag_rerank_model
        self._reranker = None

    @property
    def vector_store(self) -> Chroma:
        if self._vector_store is None:
            self._vector_store = vector_store_manager.get_chroma_vector_store(
                collection_name=self.collection_name,
                embedding_function=self.embeddings,
            )
        return self._vector_store

    @property
    def hybrid_retriever(self) -> Optional[HybridRetriever]:
        if not self.enable_hybrid:
            return None
        if self._hybrid_retriever is None:
            self._hybrid_retriever = HybridRetriever(
                vector_store=self.vector_store,
                alpha=self.hybrid_alpha,
            )
            self._init_bm25_index()
        return self._hybrid_retriever
    
    def _init_bm25_index(self):
        """初始化 BM25 索引，从 ChromaDB 加载已有文档"""
        if self._hybrid_retriever is None:
            return
        try:
            collection = self.vector_store._collection
            result = collection.get()
            if result and result.get("ids"):
                documents = [
                    Document(page_content=doc, metadata=meta or {})
                    for doc, meta in zip(result["documents"], result["metadatas"])
                ]
                if documents:
                    self._hybrid_retriever.index_documents(documents)
                    logger.info(f"[RAG] BM25 indexed {len(documents)} existing documents")
        except Exception as e:
            logger.warning(f"[RAG] Failed to init BM25 index: {e}")
    
    @property
    def reranker(self) -> Optional[BaseReranker]:
        if not self.enable_rerank:
            return None
        if self._reranker is None:
            self._reranker = get_reranker(
                provider=self.rerank_provider,
                model_name=self.rerank_model,
            )
        return self._reranker

    def _generate_doc_id(self, content: str, source: str, chunk_index: int) -> str:
        """生成文档块唯一 ID
        
        Args:
            content: 文档内容
            source: 文件来源
            chunk_index: 块索引
            
        Returns:
            唯一 ID 字符串
        """
        source_hash = hashlib.md5(source.encode()).hexdigest()[:8]
        content_hash = hashlib.md5(content.encode()).hexdigest()[:12]
        return f"{source_hash}_{content_hash}_{chunk_index}"

    async def upload_document(
        self,
        file_path: str,
        metadata: Optional[dict] = None,
        mode: str = "upsert",
    ) -> dict:
        """上传文档
        
        Args:
            file_path: 文件路径
            metadata: 元数据
            mode: 上传模式
                - "upsert": 增量更新（默认），相同 ID 的 chunk 会被更新
                - "append": 追加模式，不检查重复
                
        Returns:
            {
                "chunks": int,      # 处理的文档块数
                "added": int,       # 新增数量
                "updated": int,     # 更新数量
                "doc_ids": list,    # 文档 ID 列表
            }
        """
        if metadata is None:
            metadata = {}
        
        now = datetime.now().isoformat()
        metadata["uploaded_at"] = now
        metadata["updated_at"] = now
        
        path_obj = Path(file_path)
        if "doc_type" not in metadata and path_obj.suffix:
            metadata["doc_type"] = path_obj.suffix.lower().lstrip(".")
        
        # 加载文档
        documents = self.document_loader.load_file(file_path)
        
        for doc in documents:
            doc.metadata.update(metadata)
        # 分割文档
        split_docs = self.document_splitter.split_documents(documents)
        
        if not split_docs:
            return {"chunks": 0, "added": 0, "updated": 0, "doc_ids": []}
        
        ids = [
            self._generate_doc_id(doc.page_content, file_path, i)
            for i, doc in enumerate(split_docs)
        ]
        
        added = len(split_docs)
        updated = 0
        
        if mode == "upsert":
            try:
                existing = self.vector_store._collection.get(ids=ids)
                existing_ids = set(existing.get("ids", []))
                added = len([id for id in ids if id not in existing_ids])
                updated = len(existing_ids)
            except Exception as e:
                logger.warning(f"[RAG] Failed to check existing docs: {e}")
        # 上传文档块
        self.vector_store.add_documents(split_docs, ids=ids)
        
        logger.info(f"[RAG] Uploaded {len(split_docs)} chunks from {file_path} (added: {added}, updated: {updated})")
        
        return {
            "chunks": len(split_docs),
            "added": added,
            "updated": updated,
            "doc_ids": ids,
        }

    async def asearch(
        self,
        query: str,
        k: int = 4,
    ) -> List[Document]:
        """搜索文档
        
        Args:
            query: 查询文本
            k: 返回数量
            
        Returns:
            检索结果文档列表
        """
        retrieve_k = k * 3 if self.enable_rerank else k
        
        if self.enable_hybrid and self.hybrid_retriever:
            docs = await self.hybrid_retriever.aretrieve(query, k=retrieve_k)
        else:
            docs = await self.vector_store.asimilarity_search(query, k=retrieve_k)
        
        if self.enable_rerank and self.reranker and docs:
            docs = await self.reranker.rerank(query, docs, top_k=k)
        
        return docs[:k]

    async def delete_document(self, filename: str) -> int:
        """根据文件名删除文档
        
        Args:
            filename: 文件名（与上传时的 source 一致）
            
        Returns:
            删除的文档块数量
        """
        collection = self.vector_store._collection
        try:
            result = collection.get(where={"source": filename})
            if result is None or not result.get("ids"):
                logger.info(f"[RAG] No documents found to delete for {filename}")
                return 0
            
            ids_to_delete = result.get("ids", [])
            deleted_count = len(ids_to_delete)
            
            collection.delete(ids=ids_to_delete)
            logger.info(f"[RAG] Deleted {deleted_count} chunks from {filename}")
            return deleted_count
        except Exception as e:
            logger.error(f"[RAG] Failed to delete document {filename}: {e}")
            return 0

    async def delete_collection(self):
        """删除整个 collection"""
        vector_store_manager.delete_collection(self.collection_name)
        self._vector_store = None
        logger.info(f"[RAG] Deleted collection {self.collection_name}")

    async def get_collection_stats(self) -> dict:
        collection = self.vector_store._collection
        return {
            "collection_name": self.collection_name,
            "document_count": collection.count(),
        }

    async def save_uploaded_file(self, file, filename: str) -> str:
        """保存上传的文件
        
        Args:
            file: 上传的文件对象
            filename: 文件名
            
        Returns:
            物理路径
        """
        storage_dir = Path(settings.storage_dir) / "knowledge_base"
        storage_dir.mkdir(parents=True, exist_ok=True)
        
        file_path = storage_dir / filename
        
        content = await file.read()
        async with aiofiles.open(file_path, "wb") as f:
            await f.write(content)
        
        return str(file_path)


def get_knowledge_service() -> KnowledgeService:
    global _knowledge_service_instance
    if _knowledge_service_instance is None:
        _knowledge_service_instance = KnowledgeService()
    return _knowledge_service_instance
