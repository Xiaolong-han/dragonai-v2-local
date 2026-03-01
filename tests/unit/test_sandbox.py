"""文件沙箱测试"""

import pytest
from pathlib import Path
from unittest.mock import patch

from app.core.sandbox import FileSandbox


class TestFileSandbox:
    """FileSandbox 类测试"""
    
    @pytest.fixture
    def temp_storage(self, tmp_path):
        """创建临时存储目录"""
        storage = tmp_path / "storage"
        storage.mkdir()
        return storage
    
    def test_sandbox_dir_resolution(self):
        """测试沙箱目录解析"""
        sandbox_dir = FileSandbox.get_sandbox_dir()
        assert sandbox_dir.is_absolute()
    
    def test_validate_path_relative(self, temp_storage):
        """测试相对路径验证"""
        with patch.object(FileSandbox, 'SANDBOX_DIR', temp_storage):
            resolved = FileSandbox.validate_path('documents/test.txt')
            assert resolved.is_absolute()
            assert 'documents' in str(resolved) or 'test.txt' in str(resolved)
    
    def test_validate_path_with_leading_slash(self, temp_storage):
        """测试带前导斜杠的路径验证"""
        with patch.object(FileSandbox, 'SANDBOX_DIR', temp_storage):
            resolved = FileSandbox.validate_path('/documents/test.txt')
            assert resolved.is_absolute()
    
    def test_validate_path_traversal_attack(self, temp_storage):
        """测试路径遍历攻击防护"""
        with patch.object(FileSandbox, 'SANDBOX_DIR', temp_storage):
            with pytest.raises(PermissionError) as exc_info:
                FileSandbox.validate_path('../../../etc/passwd')
            assert "outside sandbox" in str(exc_info.value)
    
    def test_validate_path_absolute_outside_sandbox(self, temp_storage):
        """测试绝对路径在沙箱外"""
        with patch.object(FileSandbox, 'SANDBOX_DIR', temp_storage):
            with pytest.raises(PermissionError) as exc_info:
                FileSandbox.validate_path('C:/Windows/System32/config/SAM')
            assert "outside sandbox" in str(exc_info.value)
    
    def test_validate_path_blocked_pattern_env(self, temp_storage):
        """测试阻止模式 - .env 文件"""
        with patch.object(FileSandbox, 'SANDBOX_DIR', temp_storage):
            with pytest.raises(PermissionError) as exc_info:
                FileSandbox.validate_path('.env')
            assert "blocked pattern" in str(exc_info.value) or "outside sandbox" in str(exc_info.value)
    
    def test_validate_path_blocked_pattern_ssh_key(self, temp_storage):
        """测试阻止模式 - SSH 密钥"""
        with patch.object(FileSandbox, 'SANDBOX_DIR', temp_storage):
            with pytest.raises(PermissionError) as exc_info:
                FileSandbox.validate_path('id_rsa')
            assert "blocked pattern" in str(exc_info.value) or "outside sandbox" in str(exc_info.value)
    
    def test_validate_path_for_write_allowed_extension(self, temp_storage):
        """测试写入路径验证 - 允许的扩展名"""
        with patch.object(FileSandbox, 'SANDBOX_DIR', temp_storage):
            resolved = FileSandbox.validate_path_for_write('test.txt')
            assert resolved.suffix == '.txt'
    
    def test_validate_path_for_write_blocked_extension(self, temp_storage):
        """测试写入路径验证 - 阻止的扩展名"""
        with patch.object(FileSandbox, 'SANDBOX_DIR', temp_storage):
            with pytest.raises(PermissionError) as exc_info:
                FileSandbox.validate_path_for_write('test.exe')
            assert "not allowed" in str(exc_info.value)
    
    def test_is_safe_path_valid(self, temp_storage):
        """测试 is_safe_path - 有效路径"""
        with patch.object(FileSandbox, 'SANDBOX_DIR', temp_storage):
            assert FileSandbox.is_safe_path('test.txt') is True
    
    def test_is_safe_path_invalid(self, temp_storage):
        """测试 is_safe_path - 无效路径"""
        with patch.object(FileSandbox, 'SANDBOX_DIR', temp_storage):
            assert FileSandbox.is_safe_path('../../../etc/passwd') is False
    
    def test_is_allowed_extension(self):
        """测试扩展名检查"""
        assert FileSandbox.is_allowed_extension('test.txt') is True
        assert FileSandbox.is_allowed_extension('test.py') is True
        assert FileSandbox.is_allowed_extension('test.md') is True
        assert FileSandbox.is_allowed_extension('test.exe') is False
        assert FileSandbox.is_allowed_extension('test.dll') is False
    
    def test_to_virtual_path(self, temp_storage):
        """测试虚拟路径转换"""
        with patch.object(FileSandbox, 'SANDBOX_DIR', temp_storage):
            path = temp_storage / 'documents' / 'test.txt'
            virtual = FileSandbox.to_virtual_path(path)
            assert 'storage' in virtual or 'documents' in virtual
    
    def test_to_virtual_path_outside_sandbox(self, temp_storage):
        """测试沙箱外路径的虚拟路径转换"""
        with patch.object(FileSandbox, 'SANDBOX_DIR', temp_storage):
            path = Path('/etc/passwd')
            virtual = FileSandbox.to_virtual_path(path)
            assert 'etc' in virtual or 'passwd' in virtual
