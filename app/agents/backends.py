"""Backend 管理模块 - 统一管理 CompositeBackend 和子后端"""

import logging
from pathlib import Path
from typing import Optional, Union, Callable

from deepagents.backends import CompositeBackend, StateBackend, StoreBackend
from deepagents.backends.filesystem import FilesystemBackend
from langgraph.store.postgres import AsyncPostgresStore
from langgraph.store.memory import InMemoryStore

from app.config import settings

logger = logging.getLogger(__name__)


class BackendManager:
    """Backend 管理器 - 统一管理所有后端实例

    架构:
    - CompositeBackend: 统一路由入口 (通过工厂函数创建)
      ├─ default: StateBackend (运行时实例化)
      ├─ /skills/ -> FilesystemBackend (技能文件)
      └─ /memories/ -> StoreBackend (长期记忆，使用 PostgresStore)

    - PostgresStore: LangGraph 的 BaseStore 实现
      └─ 数据持久化到 PostgreSQL 的 store 表
    """

    _composite_factory: Optional[Callable] = None
    _store: Optional[Union[AsyncPostgresStore, InMemoryStore]] = None
    _store_context_manager: Optional[object] = None
    _filesystem: Optional[FilesystemBackend] = None
    _initialized: bool = False

    @classmethod
    async def initialize(cls) -> bool:
        """初始化所有后端

        Returns:
            bool: 是否成功使用 PostgreSQL 持久化
        """
        try:
            # 1. 初始化 PostgresStore (长期记忆存储)
            # StoreBackend 内部使用这个 store 实例
            if settings.database_url:
                # 使用 from_conn_string 创建 PostgresStore
                cls._store_context_manager = AsyncPostgresStore.from_conn_string(settings.database_url)
                cls._store = await cls._store_context_manager.__aenter__()
                await cls._store.setup()
                logger.info("[BACKEND] AsyncPostgresStore initialized for long-term memory")
            else:
                cls._store = InMemoryStore()
                logger.warning("[BACKEND] Using InMemoryStore for store (non-persistent)")

            # 2. 初始化 FilesystemBackend (技能文件)
            storage_dir = Path(settings.storage_dir).resolve()
            skills_dir = storage_dir / "skills"
            skills_dir.mkdir(parents=True, exist_ok=True)

            cls._filesystem = FilesystemBackend(
                root_dir=storage_dir,
                virtual_mode=True,
            )
            logger.info(f"[BACKEND] FilesystemBackend initialized: {storage_dir}")

            # 3. 创建 CompositeBackend 工厂函数
            # 工厂函数在每次工具调用时创建新的 CompositeBackend 实例
            # 这样可以正确传递 runtime 参数给 StateBackend 和 StoreBackend
            filesystem_backend = cls._filesystem

            def make_composite_backend(runtime):
                return CompositeBackend(
                    default=StateBackend(runtime),
                    routes={
                        "/skills/": filesystem_backend,
                        "/memories/": StoreBackend(
                            runtime=runtime,
                            namespace=lambda ctx: (
                                "users",
                                str(getattr(ctx.runtime.context, "user_id", "anonymous")),
                                "memories"
                            )
                        ),
                    }
                )

            cls._composite_factory = make_composite_backend
            logger.info("[BACKEND] CompositeBackend factory created with routes: /skills/, /memories/ (user-isolated)")

            cls._initialized = True
            return isinstance(cls._store, AsyncPostgresStore)

        except Exception as e:
            logger.error(f"[BACKEND] Failed to initialize: {e}")
            # 降级到内存模式
            cls._store = InMemoryStore()
            cls._initialized = True
            return False

    @classmethod
    def get_composite_factory(cls) -> Callable:
        """获取 CompositeBackend 工厂函数

        用于:
        - SkillsMiddleware (路由到 /skills/)
        - Agent 工具调用 (路由到 /memories/ 或 /skills/)

        Returns:
            工厂函数，接受 runtime 参数返回 CompositeBackend 实例
        """
        if cls._composite_factory is None:
            raise RuntimeError("BackendManager not initialized")
        return cls._composite_factory

    @classmethod
    def get_store(cls) -> Union[AsyncPostgresStore, InMemoryStore]:
        """获取 PostgresStore 实例

        用于:
        - create_agent 的 store 参数
        - StoreBackend 内部使用 (通过 runtime.store)
        """
        if cls._store is None:
            raise RuntimeError("BackendManager not initialized")
        return cls._store

    @classmethod
    def get_filesystem(cls) -> FilesystemBackend:
        """获取 FilesystemBackend 实例"""
        if cls._filesystem is None:
            raise RuntimeError("BackendManager not initialized")
        return cls._filesystem

    @classmethod
    async def close(cls) -> None:
        """关闭所有后端连接"""
        if cls._store_context_manager and cls._store and isinstance(cls._store, AsyncPostgresStore):
            await cls._store_context_manager.__aexit__(None, None, None)
            logger.info("[BACKEND] AsyncPostgresStore connection closed")

        cls._composite_factory = None
        cls._store = None
        cls._store_context_manager = None
        cls._filesystem = None
        cls._initialized = False
