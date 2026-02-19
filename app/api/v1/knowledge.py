
from typing import List
from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from pydantic import BaseModel

from app.services.knowledge_service import KnowledgeService, get_knowledge_service

router = APIRouter()


class SearchRequest(BaseModel):
    query: str
    k: int = 4


class DocumentResponse(BaseModel):
    content: str
    metadata: dict


class SearchResult(BaseModel):
    results: List[DocumentResponse]


class UploadResponse(BaseModel):
    success: bool
    message: str
    chunk_count: int


class StatsResponse(BaseModel):
    collection_name: str
    document_count: int


@router.post("/upload", response_model=UploadResponse)
async def upload_document(
    file: UploadFile = File(...),
    service: KnowledgeService = Depends(get_knowledge_service),
):
    try:
        file_path = await service.save_uploaded_file(file, file.filename)
        chunk_count = await service.upload_document(file_path)
        
        return UploadResponse(
            success=True,
            message=f"Document uploaded successfully",
            chunk_count=chunk_count,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")


@router.post("/search", response_model=SearchResult)
async def search_knowledge(
    request: SearchRequest,
    service: KnowledgeService = Depends(get_knowledge_service),
):
    try:
        documents = await service.search(request.query, k=request.k)
        results = [
            DocumentResponse(content=doc.page_content, metadata=doc.metadata)
            for doc in documents
        ]
        return SearchResult(results=results)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")


@router.get("/stats", response_model=StatsResponse)
async def get_stats(
    service: KnowledgeService = Depends(get_knowledge_service),
):
    try:
        stats = await service.get_collection_stats()
        return StatsResponse(**stats)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get stats: {str(e)}")


@router.delete("/collection")
async def delete_collection(
    service: KnowledgeService = Depends(get_knowledge_service),
):
    try:
        await service.delete_collection()
        return {"success": True, "message": "Knowledge base deleted"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Delete failed: {str(e)}")
