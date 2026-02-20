# 将 InMemorySaver 替换为 PostgresSaver 实现计划

## 一、背景分析

### 当前状态

* 当前 `AgentFactory` 使用 `InMemorySaver` 作为 checkpointer

* 内存存储在服务重启后会丢失对话状态

* 项目已配置 PostgreSQL 数据库连接 (`settings.database_url`)

### 目标

将 `InMemorySaver` 替换为 `PostgresSaver`，实现会话记忆的持久化存储，确保服务重启后对话状态不丢失。

## 二、技术方案

### 2.1 依赖变更

根据 LangChain 官方文档，需要安装以下依赖：

```
langgraph-checkpoint-postgres>=2.0.0
psycopg[binary,pool]>=3.0.0
```

### 2.2 上下文管理器模式

根据 LangChain 官方文档，`PostgresSaver.from_conn_string()` 返回一个上下文管理器：

```python
from langgraph.checkpoint.postgres import PostgresSaver

DB_URI = "postgresql://postgres:postgres@localhost:5432/dbname"
with PostgresSaver.from_conn_string(DB_URI) as checkpointer:
    checkpointer.setup()  # 首次使用需要初始化表结构
    graph = builder.compile(checkpointer=checkpointer)
```

**关键问题**：当前 `AgentFactory` 使用单例模式管理 checkpointer，但 `PostgresSaver` 需要使用上下文管理器来管理连接生命周期。

### 2.3 解决方案：应用生命周期管理

由于 FastAPI 应用有明确的生命周期，我们可以：

1. **在应用启动时初始化 checkpointer**
2. **在应用关闭时清理连接**
3. **使用 FastAPI 的 lifespan 上下文管理器**

#### 方案架构

```
FastAPI App
    ├── lifespan (启动/关闭)
    │   ├── 启动时: 创建 PostgresSaver 连接
    │   └── 关闭时: 关闭连接
    │
    └── AgentFactory
        └── get_checkpointer() -> 获取已初始化的 checkpointer
```

### 2.4 代码修改

#### 文件：`app/agents/agent_factory.py`

**重构方案：**

```python
from typing import Optional, Union
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.checkpoint.postgres import PostgresSaver
from contextlib import contextmanager

from app.config import settings

class AgentFactory:
    _checkpointer: Optional[Union[PostgresSaver, InMemorySaver]] = None
    _use_postgres: bool = True  # 默认使用 PostgreSQL

    @classmethod
    def init_checkpointer(cls) -> None:
        """初始化 checkpointer - 在应用启动时调用"""
        if cls._use_postgres and settings.database_url:
            cls._checkpointer = PostgresSaver.from_conn_string(settings.database_url)
            cls._checkpointer.setup()
        else:
            cls._checkpointer = InMemorySaver()

    @classmethod
    def close_checkpointer(cls) -> None:
        """关闭 checkpointer - 在应用关闭时调用"""
        if cls._checkpointer and hasattr(cls._checkpointer, '__exit__'):
            cls._checkpointer.__exit__(None, None, None)
        cls._checkpointer = None

    @classmethod
    def get_checkpointer(cls) -> Union[PostgresSaver, InMemorySaver]:
        """获取 checkpointer 实例"""
        if cls._checkpointer is None:
            cls.init_checkpointer()
        return cls._checkpointer
```

#### 文件：`app/main.py`

**添加生命周期管理：**

```python
from contextlib import asynccontextmanager
from app.agents.agent_factory import AgentFactory

@asynccontextmanager
async def lifespan(app: FastAPI):
    # 启动时初始化
    AgentFactory.init_checkpointer()
    yield
    # 关闭时清理
    AgentFactory.close_checkpointer()

app = FastAPI(lifespan=lifespan)
```

#### 文件：`requirements.txt`

**添加依赖：**

```
langgraph-checkpoint-postgres>=2.0.0
psycopg[binary,pool]>=3.0.0
```

### 2.5 备选方案：使用连接池

如果需要更精细的连接控制，可以使用 `psycopg_pool.ConnectionPool`：

```python
from psycopg_pool import ConnectionPool
from langgraph.checkpoint.postgres import PostgresSaver

pool = ConnectionPool(settings.database_url)
checkpointer = PostgresSaver(pool)
```

## 三、详细实现步骤

### 步骤 1：更新 requirements.txt

添加必要的依赖包。

### 步骤 2：修改 agent\_factory.py

* 添加 `init_checkpointer()` 和 `close_checkpointer()` 方法

* 重构 `get_checkpointer()` 方法

* 添加降级逻辑（PostgreSQL 连接失败时使用 InMemorySaver）

### 步骤 3：修改 main.py

* 添加 FastAPI lifespan 管理

* 在启动时初始化 checkpointer

* 在关闭时清理连接

### 步骤 4：更新测试文件

* 更新 `tests/unit/test_agent_factory.py` 中的 mock 逻辑

* 确保测试通过

### 步骤 5：验证功能

* 运行现有测试确保不破坏功能

* 验证对话状态持久化

## 四、关键代码示例

### 完整的 AgentFactory 重构

```python
"""Agent工厂 - 使用LangChain 1.0+推荐的create_agent"""

import logging
from typing import Optional, Union

from langchain.agents import create_agent
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.checkpoint.postgres import PostgresSaver

from app.config import settings
from app.tools import ALL_TOOLS
from app.llm.model_factory import ModelFactory

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """..."""  # 保持不变


class AgentFactory:
    """Agent工厂类 - 使用LangChain 1.0+推荐的create_agent"""

    _checkpointer: Optional[Union[PostgresSaver, InMemorySaver]] = None
    _initialized: bool = False

    @classmethod
    def init_checkpointer(cls) -> bool:
        """初始化 checkpointer
        
        在应用启动时调用，创建数据库连接并初始化表结构。
        
        Returns:
            bool: 是否成功使用 PostgreSQL
        """
        try:
            if settings.database_url:
                cls._checkpointer = PostgresSaver.from_conn_string(settings.database_url)
                if not cls._initialized:
                    cls._checkpointer.setup()
                    cls._initialized = True
                logger.info("[AGENT] PostgresSaver 初始化成功")
                return True
        except Exception as e:
            logger.warning(f"[AGENT] PostgresSaver 初始化失败，降级使用 InMemorySaver: {e}")
        
        cls._checkpointer = InMemorySaver()
        return False

    @classmethod
    def close_checkpointer(cls) -> None:
        """关闭 checkpointer 连接
        
        在应用关闭时调用，清理数据库连接。
        """
        if cls._checkpointer and hasattr(cls._checkpointer, '__exit__'):
            try:
                cls._checkpointer.__exit__(None, None, None)
                logger.info("[AGENT] PostgresSaver 连接已关闭")
            except Exception as e:
                logger.error(f"[AGENT] 关闭 PostgresSaver 连接失败: {e}")
        cls._checkpointer = None

    @classmethod
    def get_checkpointer(cls) -> Union[PostgresSaver, InMemorySaver]:
        """获取 checkpointer 实例
        
        如果尚未初始化，会自动初始化。
        
        Returns:
            PostgresSaver 或 InMemorySaver 实例
        """
        if cls._checkpointer is None:
            cls.init_checkpointer()
        return cls._checkpointer

    @classmethod
    def create_chat_agent(cls, is_expert: bool = False, enable_thinking: bool = False):
        """创建聊天Agent (LangChain 1.0+ 推荐方式)"""
        model = ModelFactory.get_general_model(is_expert=is_expert, thinking=enable_thinking)
        checkpointer = cls.get_checkpointer()

        agent = create_agent(
            model=model,
            tools=ALL_TOOLS,
            system_prompt=SYSTEM_PROMPT,
            checkpointer=checkpointer,
        )
        return agent

    @classmethod
    def get_agent_config(cls, conversation_id: str) -> dict:
        """获取Agent配置 - 用于区分不同对话线程"""
        return {
            "configurable": {
                "thread_id": f"conversation_{conversation_id}"
            }
        }

    @classmethod
    def reset_conversation_state(cls, conversation_id: str) -> bool:
        """重置对话状态"""
        try:
            checkpointer = cls.get_checkpointer()
            thread_id = f"conversation_{conversation_id}"
            
            if hasattr(checkpointer, 'delete_thread'):
                checkpointer.delete_thread(thread_id)
                return True
            elif hasattr(checkpointer, 'delete'):
                config = {"configurable": {"thread_id": thread_id}}
                checkpointer.delete(config)
                return True
            elif hasattr(checkpointer, '_storage'):
                if thread_id in checkpointer._storage:
                    del checkpointer._storage[thread_id]
                    return True
            return False
        except Exception as e:
            logger.error(f"[AGENT] 重置对话状态失败: {e}")
            return False
```

### FastAPI Lifespan 集成

```python
# app/main.py
# 在现有 lifespan 函数中添加 checkpointer 管理

from app.agents.agent_factory import AgentFactory

@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_logging()
    logger = logging.getLogger()
    logger.info("Starting DragonAI...")

    # 初始化 checkpointer（新增）
    AgentFactory.init_checkpointer()
    logger.info("Checkpointer initialized")

    await redis_client.connect()
    logger.info("Redis connected")

    await cache_warmup.warmup_all()

    yield

    # 关闭 checkpointer（新增）
    AgentFactory.close_checkpointer()
    
    await redis_client.close()
    logger.info("Shutting down DragonAI")
```

## 五、风险评估

| 风险项             | 影响                      | 缓解措施                       |
| --------------- | ----------------------- | -------------------------- |
| PostgreSQL 连接失败 | 服务无法启动                  | 添加异常处理，自动降级到 InMemorySaver |
| 数据库表结构变更        | 现有数据丢失                  | 文档说明迁移注意事项                 |
| Windows 环境兼容性   | psycopg 在 Windows 可能有问题 | 使用 psycopg\[binary] 确保兼容   |
| 连接泄漏            | 资源耗尽                    | 使用 lifespan 确保正确关闭连接       |

## 六、回滚方案

如果 PostgresSaver 出现问题，可以快速回滚到 InMemorySaver：

1. 设置环境变量 `DATABASE_URL=` 或修改配置
2. 系统会自动降级到 InMemorySaver

## 七、验收标准

1. ✅ 服务正常启动
2. ✅ 对话功能正常工作
3. ✅ 服务重启后对话状态保留
4. ✅ 现有测试全部通过
5. ✅ `reset_conversation_state` 方法正常工作
6. ✅ 连接正确关闭，无资源泄漏

