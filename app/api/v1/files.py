
from typing import Optional, List
from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status,
    UploadFile,
    File,
    Query,
)
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.core.database import get_db
from app.core.dependencies import get_current_active_user
from app.models.user import User
from app.storage import file_storage
from app.tools import ocr_document, understand_image


router = APIRouter(prefix="/files", tags=["文件"])


class FileResponse(BaseModel):
    """文件响应模型"""
    filename: str
    original_filename: Optional[str]
    content_type: str
    relative_path: str
    file_size: int
    upload_time: str


class FileInfoResponse(BaseModel):
    """文件信息响应模型"""
    filename: str
    relative_path: str
    file_size: int
    created_time: str
    modified_time: str


class OCRRequest(BaseModel):
    """OCR请求模型"""
    relative_path: str
    prompt: Optional[str] = None


class OCRResponse(BaseModel):
    """OCR响应模型"""
    relative_path: str
    content: str


class ImageUnderstandRequest(BaseModel):
    """图片理解请求模型"""
    relative_path: str
    prompt: str = "请描述这张图片的内容"


class ImageUnderstandResponse(BaseModel):
    """图片理解响应模型"""
    relative_path: str
    content: str


@router.post("/upload", response_model=List[FileResponse], status_code=status.HTTP_201_CREATED)
async def upload_files(
    files: List[UploadFile] = File(..., description="要上传的文件列表"),
    current_user: User = Depends(get_current_active_user),
):
    """上传文件到本地文件系统"""
    results = []
    for file in files:
        file_info = await file_storage.save_file(file)
        results.append(FileResponse(**file_info))
    return results


@router.get("/{relative_path:path}", response_model=FileInfoResponse)
async def get_file_info(
    relative_path: str,
    current_user: User = Depends(get_current_active_user),
):
    """获取文件信息"""
    file_info = file_storage.get_file_info(relative_path)
    if not file_info:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File not found"
        )
    return FileInfoResponse(**file_info)


@router.delete("/{relative_path:path}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_file(
    relative_path: str,
    current_user: User = Depends(get_current_active_user),
):
    """删除文件"""
    success = file_storage.delete_file(relative_path)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File not found"
        )
    return None


@router.post("/ocr", response_model=OCRResponse)
async def process_ocr(
    request: OCRRequest,
    current_user: User = Depends(get_current_active_user),
):
    """使用OCR识别文档内容"""
    if not file_storage.file_exists(request.relative_path):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File not found"
        )
    
    content = ocr_document.invoke({"image_path": request.relative_path, "prompt": request.prompt})
    return OCRResponse(
        relative_path=request.relative_path,
        content=content
    )


@router.post("/understand-image", response_model=ImageUnderstandResponse)
async def process_image_understanding(
    request: ImageUnderstandRequest,
    current_user: User = Depends(get_current_active_user),
):
    """理解并分析图片内容"""
    if not file_storage.file_exists(request.relative_path):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File not found"
        )
    
    content = understand_image.invoke({"image_path": request.relative_path, "prompt": request.prompt})
    return ImageUnderstandResponse(
        relative_path=request.relative_path,
        content=content
    )

