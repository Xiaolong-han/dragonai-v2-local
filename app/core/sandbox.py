"""文件系统沙箱 - 限制文件访问范围"""

import logging
from pathlib import Path
from typing import Set, Optional

from app.config import settings

logger = logging.getLogger(__name__)


class FileSandbox:
    """文件系统沙箱
    
    限制文件访问范围，防止路径遍历攻击。
    """
    
    SANDBOX_DIR: Path = Path(settings.storage_dir).resolve()
    
    ALLOWED_EXTENSIONS: Set[str] = {
        '.txt', '.md', '.py', '.js', '.ts', '.json', '.yaml', '.yml',
        '.csv', '.xml', '.html', '.css', '.sql', '.sh',
        '.pdf', '.docx', '.doc', '.xlsx', '.xls', '.pptx',
        '.png', '.jpg', '.jpeg', '.gif', '.webp', '.svg', '.ico',
        '.zip', '.tar', '.gz',
        '.log', '.ini', '.cfg', '.conf', '.env.example',
        '.toml', '.rst', '.tex',
    }
    
    BLOCKED_EXTENSIONS: Set[str] = {
        '.exe', '.dll', '.bat', '.cmd', '.com', '.scr',
        '.msi', '.ps1', '.vbs', '.jar',
    }
    
    BLOCKED_PATTERNS: Set[str] = {
        '.env', '.git', '.ssh', '.htaccess', '.htpasswd',
        'id_rsa', 'id_ed25519', '.pem', '.key',
    }
    
    @classmethod
    def validate_path(cls, file_path: str) -> Path:
        """验证并解析文件路径
        
        Args:
            file_path: 相对路径或绝对路径
            
        Returns:
            解析后的绝对路径
            
        Raises:
            PermissionError: 路径不合法或在沙箱外
        """
        path = Path(file_path)
        
        if path.is_absolute():
            resolved = path.resolve()
        else:
            relative = file_path.lstrip("/")
            resolved = (cls.SANDBOX_DIR / relative).resolve()
        
        if not cls._is_subpath(resolved, cls.SANDBOX_DIR):
            raise PermissionError(f"Access denied: path outside sandbox")
        
        cls._check_blocked_patterns(resolved)
        
        return resolved
    
    @classmethod
    def validate_path_for_write(cls, file_path: str) -> Path:
        """验证写入路径（包含文件类型检查）
        
        Args:
            file_path: 相对路径或绝对路径
            
        Returns:
            解析后的绝对路径
            
        Raises:
            PermissionError: 路径不合法、在沙箱外或文件类型不允许
        """
        resolved = cls.validate_path(file_path)
        
        ext = resolved.suffix.lower()
        if ext and ext not in cls.ALLOWED_EXTENSIONS:
            raise PermissionError(f"File type not allowed: {ext}")
        
        return resolved
    
    @classmethod
    def is_safe_path(cls, file_path: str) -> bool:
        """检查路径是否安全（不抛异常）
        
        Args:
            file_path: 文件路径
            
        Returns:
            是否安全
        """
        try:
            cls.validate_path(file_path)
            return True
        except PermissionError:
            return False
    
    @classmethod
    def is_allowed_extension(cls, file_path: str) -> bool:
        """检查文件扩展名是否允许
        
        Args:
            file_path: 文件路径
            
        Returns:
            是否允许
        """
        ext = Path(file_path).suffix.lower()
        if not ext:
            return True
        if ext in cls.BLOCKED_EXTENSIONS:
            return False
        return ext in cls.ALLOWED_EXTENSIONS
    
    @classmethod
    def get_sandbox_dir(cls) -> Path:
        """获取沙箱根目录"""
        return cls.SANDBOX_DIR
    
    @classmethod
    def to_virtual_path(cls, path: Path) -> str:
        """将物理路径转换为虚拟路径
        
        Args:
            path: 物理路径
            
        Returns:
            虚拟路径字符串
        """
        path = path.resolve()
        
        try:
            relative = path.relative_to(cls.SANDBOX_DIR)
            return f"/storage/{relative.as_posix()}"
        except ValueError:
            pass
        
        return str(path)
    
    @classmethod
    def _is_subpath(cls, path: Path, parent: Path) -> bool:
        """检查 path 是否是 parent 的子路径"""
        try:
            path.relative_to(parent)
            return True
        except ValueError:
            return False
    
    @classmethod
    def _check_blocked_patterns(cls, path: Path) -> None:
        """检查是否匹配阻止模式"""
        path_str = str(path).lower()
        name = path.name.lower()
        
        for pattern in cls.BLOCKED_PATTERNS:
            if pattern.lower() in path_str or name == pattern.lower():
                raise PermissionError(f"Access denied: blocked pattern '{pattern}'")
