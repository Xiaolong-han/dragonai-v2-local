"""监控 API 路由"""

from fastapi import APIRouter, Depends
from app.core.dependencies import get_current_active_user
from app.models.user import User
from app.core.cache_metrics import get_cache_stats

router = APIRouter(prefix="/monitoring", tags=["监控"])


@router.get("/cache/stats")
async def get_cache_statistics(current_user: User = Depends(get_current_active_user)):
    """获取缓存统计信息（需要认证）"""
    return await get_cache_stats()


@router.get("/health/detailed")
async def detailed_health_check():
    """详细健康检查"""
    from app.core.redis import redis_client
    from app.core.database import engine
    
    health = {
        "status": "healthy",
        "services": {}
    }
    
    try:
        await redis_client.client.ping()
        health["services"]["redis"] = {"status": "healthy"}
    except Exception as e:
        health["services"]["redis"] = {"status": "unhealthy", "error": str(e)}
        health["status"] = "degraded"
    
    try:
        async with engine.connect() as conn:
            await conn.execute("SELECT 1")
        health["services"]["database"] = {"status": "healthy"}
    except Exception as e:
        health["services"]["database"] = {"status": "unhealthy", "error": str(e)}
        health["status"] = "degraded"
    
    return health
