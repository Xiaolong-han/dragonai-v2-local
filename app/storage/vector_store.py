
import chromadb
from chromadb.config import Settings
from langchain_core.embeddings import Embeddings
from langchain_chroma import Chroma

from app.config import settings


class VectorStoreManager:
    def __init__(self):
        self.persist_dir = settings.chroma_persist_dir
        self._client = None
        self._chroma_clients = {}

    @property
    def client(self):
        if self._client is None:
            self._client = chromadb.PersistentClient(
                path=self.persist_dir,
                settings=Settings(anonymized_telemetry=False)
            )
        return self._client

    def get_chroma_vector_store(
        self,
        collection_name: str,
        embedding_function: Embeddings
    ) -&gt; Chroma:
        key = collection_name
        if key not in self._chroma_clients:
            self._chroma_clients[key] = Chroma(
                collection_name=collection_name,
                embedding_function=embedding_function,
                client=self.client,
                persist_directory=self.persist_dir
            )
        return self._chroma_clients[key]

    def delete_collection(self, collection_name: str):
        try:
            self.client.delete_collection(collection_name)
            if collection_name in self._chroma_clients:
                del self._chroma_clients[collection_name]
        except Exception:
            pass


vector_store_manager = VectorStoreManager()

