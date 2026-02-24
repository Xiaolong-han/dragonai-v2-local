from typing import Any, List, Dict
from datetime import datetime
import json


def is_sqlalchemy_model(obj: Any) -> bool:
    """检查对象是否为 SQLAlchemy 模型"""
    return hasattr(obj, '__table__') and hasattr(obj, '_sa_instance_state')


def model_to_dict(obj: Any) -> Any:
    """将 SQLAlchemy 模型或模型列表转换为字典或字典列表
    
    只处理数据库表中定义的列，忽略 SQLAlchemy 内部属性
    """
    if isinstance(obj, list):
        return [model_to_dict(item) for item in obj]
    
    if is_sqlalchemy_model(obj):
        result = {}
        for column in obj.__table__.columns:
            column_name = column.name
            try:
                value = getattr(obj, column_name, None)
                if isinstance(value, datetime):
                    value = value.isoformat()
                elif value is not None and not isinstance(value, (str, int, float, bool, list, dict, type(None))):
                    try:
                        value = json.dumps(value)
                    except (TypeError, ValueError):
                        value = str(value)
                result[column_name] = value
            except Exception:
                result[column_name] = None
        return result
    
    return obj


def models_to_list(objects: List[Any]) -> List[Dict]:
    """将 SQLAlchemy 模型列表转换为字典列表，保留顺序"""
    return [model_to_dict(obj) for obj in objects]
