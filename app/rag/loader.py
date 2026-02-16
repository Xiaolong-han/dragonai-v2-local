
from pathlib import Path
from typing import List, Union
from langchain_core.documents import Document
from langchain_community.document_loaders import (
    PyPDFLoader,
    Docx2txtLoader,
    UnstructuredMarkdownLoader,
    TextLoader,
)


class DocumentLoader:
    SUPPORTED_EXTENSIONS = {".pdf", ".docx", ".md", ".markdown", ".txt"}

    @classmethod
    def load_file(cls, file_path: Union[str, Path]) -> List[Document]:
        file_path = Path(file_path)
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        
        ext = file_path.suffix.lower()
        if ext not in cls.SUPPORTED_EXTENSIONS:
            raise ValueError(f"Unsupported file format: {ext}")
        
        loader = cls._get_loader(file_path, ext)
        documents = loader.load()
        
        for doc in documents:
            if "source" not in doc.metadata:
                doc.metadata["source"] = str(file_path)
            if "file_name" not in doc.metadata:
                doc.metadata["file_name"] = file_path.name
        
        return documents

    @classmethod
    def load_directory(cls, dir_path: Union[str, Path], recursive: bool = False) -> List[Document]:
        dir_path = Path(dir_path)
        if not dir_path.exists():
            raise FileNotFoundError(f"Directory not found: {dir_path}")
        if not dir_path.is_dir():
            raise NotADirectoryError(f"Not a directory: {dir_path}")
        
        documents = []
        glob_pattern = "**/*" if recursive else "*"
        
        for file_path in dir_path.glob(glob_pattern):
            if file_path.is_file() and file_path.suffix.lower() in cls.SUPPORTED_EXTENSIONS:
                try:
                    docs = cls.load_file(file_path)
                    documents.extend(docs)
                except Exception as e:
                    print(f"Failed to load file {file_path}: {e}")
        
        return documents

    @classmethod
    def _get_loader(cls, file_path: Path, ext: str):
        if ext == ".pdf":
            return PyPDFLoader(str(file_path))
        elif ext == ".docx":
            return Docx2txtLoader(str(file_path))
        elif ext in (".md", ".markdown"):
            return UnstructuredMarkdownLoader(str(file_path))
        elif ext == ".txt":
            return TextLoader(str(file_path), encoding="utf-8")
        else:
            raise ValueError(f"Unsupported file format: {ext}")

