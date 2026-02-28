
import os
import uuid
from datetime import datetime
from pathlib import Path
from typing import Optional
from fastapi import UploadFile

from app.config import settings


class FileStorage:
    """本地文件系统存储管理器"""

    def __init__(self, base_dir: Optional[str] = None):
        self.base_dir = Path(base_dir or settings.storage_dir)
        self._ensure_directories()

    def _ensure_directories(self):
        """确保必要的目录存在"""
        (self.base_dir / "uploads").mkdir(parents=True, exist_ok=True)
        (self.base_dir / "images").mkdir(parents=True, exist_ok=True)
        (self.base_dir / "documents").mkdir(parents=True, exist_ok=True)

    def _get_subdirectory(self, file_type: str) -> str:
        """根据文件类型获取子目录"""
        if file_type.startswith("image/"):
            return "images"
        elif file_type.startswith("application/") or file_type in [
            "text/plain",
            "text/markdown",
        ]:
            return "documents"
        return "uploads"

    def _generate_filename(self, original_filename: str) -> str:
        """生成唯一文件名"""
        ext = Path(original_filename).suffix
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        unique_id = str(uuid.uuid4())[:8]
        return f"{timestamp}_{unique_id}{ext}"

    async def save_file(
        self,
        file: UploadFile,
        file_type: Optional[str] = None,
    ) -> dict:
        """
        保存上传的文件到本地文件系统

        Args:
            file: FastAPI UploadFile对象
            file_type: 可选的文件类型，用于确定存储目录

        Returns:
            包含文件信息的字典
        """
        content_type = file_type or file.content_type or "application/octet-stream"
        subdir = self._get_subdirectory(content_type)
        filename = self._generate_filename(file.filename or "unknown")
        file_path = self.base_dir / subdir / filename

        content = await file.read()
        with open(file_path, "wb") as f:
            f.write(content)

        file_size = len(content)
        relative_path = f"{subdir}/{filename}"
        virtual_path = f"/storage/{subdir}/{filename}"

        return {
            "filename": filename,
            "original_filename": file.filename,
            "content_type": content_type,
            "file_path": str(file_path),
            "relative_path": relative_path,
            "virtual_path": virtual_path,
            "file_size": file_size,
            "upload_time": datetime.now().isoformat(),
        }

    def get_file_path(self, relative_path: str) -> Optional[Path]:
        """
        根据相对路径获取文件的完整路径

        Args:
            relative_path: 相对路径

        Returns:
            文件完整路径，如果文件不存在则返回None
        """
        file_path = self.base_dir / relative_path
        if file_path.exists():
            return file_path
        return None

    def file_exists(self, relative_path: str) -> bool:
        """检查文件是否存在"""
        return (self.base_dir / relative_path).exists()

    def delete_file(self, relative_path: str) -> bool:
        """
        删除文件

        Args:
            relative_path: 相对路径

        Returns:
            是否删除成功
        """
        file_path = self.base_dir / relative_path
        if file_path.exists():
            file_path.unlink()
            return True
        return False

    def get_file_info(self, relative_path: str) -> Optional[dict]:
        """
        获取文件信息

        Args:
            relative_path: 相对路径

        Returns:
            文件信息字典，如果文件不存在则返回None
        """
        file_path = self.base_dir / relative_path
        if not file_path.exists():
            return None

        stat = file_path.stat()
        return {
            "filename": file_path.name,
            "file_path": str(file_path),
            "relative_path": relative_path,
            "file_size": stat.st_size,
            "created_time": datetime.fromtimestamp(stat.st_ctime).isoformat(),
            "modified_time": datetime.fromtimestamp(stat.st_mtime).isoformat(),
        }


file_storage = FileStorage()

