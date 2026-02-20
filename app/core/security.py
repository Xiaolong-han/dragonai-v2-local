
from datetime import datetime, timedelta, UTC
from typing import Optional
from jose import JWTError, jwt
import bcrypt
import hashlib
import hmac
import base64
import urllib.parse

from app.config import settings


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(
        plain_password[:72].encode("utf-8"),
        hashed_password.encode("utf-8")
    )


def get_password_hash(password: str) -> str:
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password[:72].encode("utf-8"), salt).decode("utf-8")


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(UTC) + expires_delta
    else:
        expire = datetime.now(UTC) + timedelta(minutes=settings.access_token_expire_minutes)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.secret_key, algorithm=settings.algorithm)
    return encoded_jwt


def decode_access_token(token: str) -> Optional[dict]:
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
        return payload
    except JWTError:
        return None


def generate_file_signature(relative_path: str, expires_timestamp: int) -> str:
    """生成文件访问签名
    
    Args:
        relative_path: 文件相对路径
        expires_timestamp: 过期时间戳
        
    Returns:
        签名字符串
    """
    message = f"{relative_path}:{expires_timestamp}"
    signature = hmac.new(
        settings.secret_key.encode("utf-8"),
        message.encode("utf-8"),
        hashlib.sha256
    ).digest()
    return base64.urlsafe_b64encode(signature).decode("utf-8").rstrip("=")


def verify_file_signature(relative_path: str, expires_timestamp: int, signature: str) -> bool:
    """验证文件访问签名
    
    Args:
        relative_path: 文件相对路径
        expires_timestamp: 过期时间戳
        signature: 签名字符串
        
    Returns:
        签名是否有效
    """
    expected_signature = generate_file_signature(relative_path, expires_timestamp)
    if not hmac.compare_digest(expected_signature, signature):
        return False
    
    if datetime.now(UTC).timestamp() > expires_timestamp:
        return False
    
    return True


def generate_signed_url(relative_path: str, expires_in_seconds: int = 3600) -> str:
    """生成带签名的文件访问URL
    
    Args:
        relative_path: 文件相对路径
        expires_in_seconds: 过期时间（秒），默认1小时
        
    Returns:
        带签名的相对URL路径
    """
    expires_timestamp = int((datetime.now(UTC) + timedelta(seconds=expires_in_seconds)).timestamp())
    signature = generate_file_signature(relative_path, expires_timestamp)
    
    encoded_path = urllib.parse.quote(relative_path, safe="")
    return f"/api/v1/files/serve/{encoded_path}?expires={expires_timestamp}&signature={signature}"

