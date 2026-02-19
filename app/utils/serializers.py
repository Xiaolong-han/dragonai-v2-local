from typing import Any
from datetime import datetime
import json


def is_sqlalchemy_model(obj: Any) -> bool:
    """检查对象是否为 SQLAlchemy 模型"""
    return hasattr(obj, '__table__')


def model_to_dict(obj: Any) -> Any:
    """将 SQLAlchemy 模型转换为字典"""
    if isinstance(obj, list):
        return [model_to_dict(item) for item in obj]
    
    if not is_sqlalchemy_model(obj):
        return obj
    
    data = {}
    for column in obj.__table__.columns:
        column_name = column.name
        try:
            value = None
            
            if column_name == 'metadata':
                if hasattr(obj, 'metadata_'):
                    value = getattr(obj, 'metadata_')
                else:
                    value = None
            else:
                try:
                    value = getattr(obj, column_name)
                except AttributeError:
                    value = None
            
            if isinstance(value, datetime):
                data[column_name] = value.isoformat()
            elif value is not None:
                if isinstance(value, (str, int, float, bool, list, dict)):
                    data[column_name] = value
                else:
                    try:
                        data[column_name] = json.dumps(value)
                    except (TypeError, ValueError):
                        data[column_name] = None
            else:
                data[column_name] = None
        except Exception:
            data[column_name] = None
    return data
