
from typing import List
from langchain_core.tools import tool
from langchain_core.documents import Document

from app.services import KnowledgeService


def format_documents(documents: List[Document]) -> str:
    if not documents:
        return "No relevant documents found."
    
    formatted = []
    for i, doc in enumerate(documents, 1):
        source = doc.metadata.get("source", "Unknown")
        file_name = doc.metadata.get("file_name", source)
        formatted.append(
            f"[Document {i}]\n"
            f"Source: {file_name}\n"
            f"Content:\n{doc.page_content}\n"
        )
    
    return "\n".join(formatted)


@tool
def search_knowledge_base(query: str, k: int = 4) -> str:
    """
    Search the developer knowledge base for relevant documents.
    
    Use this tool when you need to answer questions about project documentation,
    technical specifications, API documentation, etc.
    
    Args:
        query: The question or keywords to search for
        k: Number of documents to return, default is 4
        
    Returns:
        Formatted content of relevant documents
    """
    try:
        service = KnowledgeService()
        documents = service.search(query, k=k)
        return format_documents(documents)
    except Exception as e:
        return f"Error searching knowledge base: {str(e)}"


@tool
def search_knowledge_base_with_score(query: str, k: int = 4) -> str:
    """
    Search the developer knowledge base with similarity scores.
    
    Similar to search_knowledge_base, but returns similarity scores for each document
    to help judge relevance.
    
    Args:
        query: The question or keywords to search for
        k: Number of documents to return, default is 4
        
    Returns:
        Formatted content with similarity scores
    """
    try:
        service = KnowledgeService()
        results = service.search_with_score(query, k=k)
        
        if not results:
            return "No relevant documents found."
        
        formatted = []
        for i, (doc, score) in enumerate(results, 1):
            source = doc.metadata.get("source", "Unknown")
            file_name = doc.metadata.get("file_name", source)
            formatted.append(
                f"[Document {i}] (Similarity: {score:.4f})\n"
                f"Source: {file_name}\n"
                f"Content:\n{doc.page_content}\n"
            )
        
        return "\n".join(formatted)
    except Exception as e:
        return f"Error searching knowledge base: {str(e)}"


__all__ = ["search_knowledge_base", "search_knowledge_base_with_score"]

