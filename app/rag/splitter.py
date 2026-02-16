
from typing import List
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter


class DocumentSplitter:
    def __init__(
        self,
        chunk_size: int = 1000,
        chunk_overlap: int = 200,
        separators: List[str] = None,
    ):
        if separators is None:
            separators = ["\n\n", "\n", ".", "!", "?", ",", " ", ""]
        
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            separators=separators,
            length_function=len,
        )

    def split_documents(self, documents: List[Document]) -> List[Document]:
        return self.text_splitter.split_documents(documents)

    def split_text(self, text: str, metadata: dict = None) -> List[Document]:
        if metadata is None:
            metadata = {}
        
        doc = Document(page_content=text, metadata=metadata)
        return self.text_splitter.split_documents([doc])

