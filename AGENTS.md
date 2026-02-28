# DragonAI v2 - AI Agent 开发指南

**Version 2.0.0**
DragonAI Team
February 2026

> **Note:**
> 本文档主要供 AI Agent 和 LLM 在维护、生成或重构 DragonAI 代码库时遵循。人类开发者也可参考，但指导原则针对自动化工作流进行了优化。

---

## 目录

1. [项目概述](#1-项目概述)
2. [技术栈](#2-技术栈)
3. [项目结构](#3-项目结构)
4. [代码规范](#4-代码规范)
5. [核心模块指南](#5-核心模块指南)
6. [最佳实践](#6-最佳实践)
7. [常见任务](#7-常见任务)
8. [测试指南](#8-测试指南)

---

## 1. 项目概述

DragonAI v2 是一个基于 LangChain 1.0+ 构建的智能 AI 助手系统，支持多模态交互、工具调用、知识库检索等功能。

### 核心特性

- **多模型支持**: 通义千问 (Qwen) 系列模型，支持通用、视觉、编程、翻译等场景
- **Agent 架构**: 基于 LangGraph 的 ReAct Agent，支持工具调用和状态持久化
- **多模态能力**: 图像生成、图像编辑、OCR、图像理解
- **RAG 支持**: 基于 ChromaDB 的知识库检索
- **流式输出**: SSE 实时流式响应

---

## 2. 技术栈

### 后端

| 组件 | 版本 | 用途 |
|------|------|------|
| Python | 3.10+ | 主要开发语言 |
| FastAPI | 0.115+ | Web 框架 |
| LangChain | 1.0+ | LLM 框架 |
| LangGraph | 最新 | Agent 状态管理 |
| PostgreSQL | - | 主数据库 + Checkpointer |
| Redis | 5.0+ | 缓存 + 限流 |
| ChromaDB | 0.5+ | 向量数据库 |

### 前端

| 组件 | 版本 | 用途 |
|------|------|------|
| Vue 3 | 最新 | 前端框架 |
| TypeScript | 最新 | 类型安全 |
| Pinia | 最新 | 状态管理 |
| Vite | 最新 | 构建工具 |

---

## 3. 项目结构

```
dragonai-v2-local/
├── app/                      # 后端主目录
│   ├── agents/               # Agent 相关
│   │   └── agent_factory.py  # Agent 工厂类
│   ├── api/v1/               # API 路由
│   │   ├── auth.py           # 认证
│   │   ├── chat.py           # 聊天
│   │   ├── conversations.py  # 会话管理
│   │   ├── files.py          # 文件上传
│   │   ├── knowledge.py      # 知识库
│   │   ├── models.py         # 模型配置
│   │   ├── monitoring.py     # 监控
│   │   └── tools.py          # 工具管理
│   ├── core/                 # 核心模块
│   │   ├── database.py       # 数据库连接
│   │   ├── dependencies.py   # 依赖注入
│   │   ├── exceptions.py     # 异常定义
│   │   ├── logging_config.py # 日志配置
│   │   ├── rate_limit.py     # 限流
│   │   ├── redis.py          # Redis 客户端
│   │   ├── security.py       # 安全相关
│   │   └── tracing.py        # 链路追踪
│   ├── llm/                  # LLM 相关
│   │   ├── model_factory.py  # 模型工厂
│   │   └── qwen_models.py    # Qwen 模型封装
│   ├── models/               # SQLAlchemy 模型
│   ├── schemas/              # Pydantic 模型
│   ├── services/             # 业务逻辑层
│   ├── tools/                # Agent 工具
│   │   ├── code_tools.py     # 编程工具
│   │   ├── filesystem_tools.py # 文件系统工具
│   │   ├── image_tools.py    # 图像生成/编辑
│   │   ├── multimodal_tool.py # 多模态工具
│   │   ├── rag_tool.py       # 知识库检索
│   │   ├── translation_tools.py # 翻译工具
│   │   └── web_search_tool.py # 网络搜索
│   ├── utils/                # 工具函数
│   ├── config.py             # 配置管理
│   └── main.py               # 应用入口
├── frontend/                 # 前端目录
│   └── src/
│       ├── components/       # Vue 组件
│       ├── views/            # 页面视图
│       ├── stores/           # Pinia 状态
│       ├── router/           # 路由配置
│       └── utils/            # 工具函数
├── tests/                    # 测试目录
│   ├── unit/                 # 单元测试
│   └── integration/          # 集成测试
├── storage/                  # 存储目录
│   └── skills/               # Skills 目录
├── logs/                     # 日志目录
├── alembic/                  # 数据库迁移
├── requirements.txt          # Python 依赖
├── pytest.ini               # Pytest 配置
└── docker-compose.yml       # Docker 配置
```

---

## 4. 代码规范

### 4.1 Python 后端规范

#### 导入顺序

```python
# 1. 标准库
import asyncio
import logging
from typing import Optional, List

# 2. 第三方库
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from langchain.agents import create_agent

# 3. 本地模块
from app.config import settings
from app.core.database import get_db
from app.models.user import User
```

#### 异步函数命名

```python
# 正确: 异步函数使用 async def
async def get_user(db: AsyncSession, user_id: int) -> Optional[User]:
    ...

# 正确: 异步方法调用使用 await
user = await db.get(User, user_id)

# 错误: 不要在异步函数中使用同步 IO
def get_user_sync(user_id: int):  # 错误
    return session.query(User).get(user_id)
```

#### 类型注解

```python
# 正确: 使用类型注解
async def create_message(
    db: AsyncSession,
    conversation_id: int,
    content: str,
    metadata_: Optional[dict] = None
) -> Message:
    ...

# 正确: 使用 Union 和 Optional
from typing import Union, Optional

def get_checkpointer() -> Union[AsyncPostgresSaver, InMemorySaver]:
    ...
```

#### 异常处理

```python
# 正确: 使用自定义异常
from app.core.exceptions import DragonAIException

raise DragonAIException(
    code="CONVERSATION_NOT_FOUND",
    message="会话不存在",
    status_code=404
)

# 正确: 在服务层捕获并转换异常
try:
    result = await some_operation()
except ExternalAPIError as e:
    raise DragonAIException(
        code="EXTERNAL_API_ERROR",
        message=f"外部 API 调用失败: {e}",
        status_code=502
    )
```

### 4.2 Vue 前端规范

#### 组件结构

```vue
<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useChatStore } from '@/stores/chat'

const store = useChatStore()
const inputValue = ref('')

const formattedMessages = computed(() => {
  return store.messages.map(msg => ({
    ...msg,
    timestamp: new Date(msg.createdAt).toLocaleString()
  }))
})

onMounted(() => {
  store.fetchMessages()
})
</script>

<template>
  <div class="chat-container">
    <ChatMessageList :messages="formattedMessages" />
  </div>
</template>

<style scoped>
.chat-container {
  /* 样式 */
}
</style>
```

#### API 调用

```typescript
import { request } from '@/utils/request'

export async function sendMessage(data: ChatRequest): Promise<void> {
  return request.post('/api/v1/chat/send', data)
}

export async function getChatHistory(
  conversationId: number,
  params?: { skip?: number; limit?: number }
): Promise<ChatHistoryResponse> {
  return request.get(`/api/v1/chat/conversations/${conversationId}/history`, { params })
}
```

---

## 5. 核心模块指南

### 5.1 配置管理 (config.py)

所有配置通过 `Settings` 类管理，使用 Pydantic Settings 从环境变量或 `.env` 文件加载。

```python
from app.config import settings

# 访问配置
api_key = settings.qwen_api_key
model_name = settings.model_general_fast
log_level = settings.log_level
```

**重要**: 不要硬编码任何配置值，始终从 `settings` 获取。

### 5.2 模型工厂 (model_factory.py)

使用 `ModelFactory` 创建各类模型实例。

```python
from app.llm.model_factory import ModelFactory

# 通用模型 (用于 Agent)
model = ModelFactory.get_general_model(is_expert=False, thinking=True)

# 视觉模型
vision_model = ModelFactory.get_vision_model(is_ocr=True)

# 图像生成模型
image_model = ModelFactory.get_image_model(is_turbo=True)

# 编程模型
coder_model = ModelFactory.get_coder_model(is_plus=False)

# 翻译模型
translation_model = ModelFactory.get_translation_model()

# Embedding 模型
embedding = ModelFactory.get_embedding()
```

### 5.3 Agent 工厂 (agent_factory.py)

使用 `AgentFactory` 创建和管理 Agent 实例。

```python
from app.agents.agent_factory import AgentFactory

# 创建 Agent
agent = AgentFactory.create_chat_agent(
    is_expert=False,
    enable_thinking=True
)

# 获取配置 (用于区分对话线程)
config = AgentFactory.get_agent_config(conversation_id="123")

# 调用 Agent
result = await agent.ainvoke(
    {"messages": [{"role": "user", "content": "你好"}]},
    config=config
)

# 流式调用
async for event in agent.astream(
    {"messages": [{"role": "user", "content": "你好"}]},
    config=config
):
    print(event)
```

### 5.4 工具定义 (tools/)

所有工具定义在 `app/tools/` 目录，使用 `@tool` 装饰器。

```python
from langchain_core.tools import tool
from typing import Optional

@tool
def my_custom_tool(query: str, option: Optional[str] = None) -> str:
    """工具描述 - 这会显示给 LLM 用于判断何时使用

    Args:
        query: 查询内容
        option: 可选参数

    Returns:
        工具执行结果
    """
    result = do_something(query, option)
    return result
```

**工具定义规则**:
1. 每个工具必须有清晰的 docstring
2. 参数必须有类型注解
3. 返回值必须是字符串
4. 新工具需要在 `__init__.py` 中注册到 `ALL_TOOLS`

### 5.5 API 路由 (api/v1/)

API 路由使用 FastAPI Router。

```python
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import get_current_active_user
from app.core.rate_limit import limiter
from app.models.user import User
from app.schemas.message import MessageResponse, MessageCreate

router = APIRouter(prefix="/messages", tags=["消息"])

@router.get("/{message_id}", response_model=MessageResponse)
@limiter.limit("30/minute")
async def get_message(
    request: Request,
    message_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
) -> MessageResponse:
    message = await message_service.get_message(db, message_id, current_user.id)
    if not message:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Message not found"
        )
    return message
```

### 5.6 服务层 (services/)

业务逻辑封装在服务层。

```python
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.message import Message
from app.schemas.message import MessageCreate

class MessageService:
    async def create_message(
        self,
        db: AsyncSession,
        conversation_id: int,
        message_create: MessageCreate,
        user_id: int
    ) -> Message:
        message = Message(
            conversation_id=conversation_id,
            user_id=user_id,
            role=message_create.role,
            content=message_create.content,
            metadata_=message_create.metadata_
        )
        db.add(message)
        await db.commit()
        await db.refresh(message)
        return message

message_service = MessageService()
```

---

## 6. 最佳实践

### 6.1 LangChain 1.0+ 规范

**使用 `create_agent` 创建 Agent**:

```python
from langchain.agents import create_agent

agent = create_agent(
    model=model,
    tools=tools,
    system_prompt=system_prompt,
    checkpointer=checkpointer,
)
```

**不要使用已废弃的 API**:
- ❌ `AgentExecutor` (已废弃)
- ❌ `initialize_agent` (已废弃)
- ❌ `langchain.agents.load_tools` (已废弃)

### 6.2 异步编程规范

**正确使用异步**:

```python
# 正确: 并发执行多个异步操作
results = await asyncio.gather(
    fetch_user(user_id),
    fetch_conversations(user_id),
    fetch_settings(user_id)
)

# 正确: 流式处理
async for chunk in agent.astream(input, config):
    yield chunk

# 错误: 在异步上下文中使用同步 IO
def sync_database_query():  # 错误
    return session.query(User).all()
```

### 6.3 数据库操作

**使用 SQLAlchemy 2.0 异步风格**:

```python
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

# 正确: 使用 select() 和 await
async def get_user(db: AsyncSession, user_id: int) -> Optional[User]:
    result = await db.execute(select(User).where(User.id == user_id))
    return result.scalar_one_or_none()

# 正确: 使用关系加载
async def get_conversation_with_messages(db: AsyncSession, conv_id: int):
    result = await db.execute(
        select(Conversation)
        .options(selectinload(Conversation.messages))
        .where(Conversation.id == conv_id)
    )
    return result.scalar_one_or_none()
```

### 6.4 错误处理

**统一异常格式**:

```python
# 正确: 使用 DragonAIException
raise DragonAIException(
    code="VALIDATION_ERROR",
    message="参数验证失败",
    details={"field": "email", "error": "无效的邮箱格式"},
    status_code=400
)

# 正确: API 错误响应格式
{
    "error": {
        "code": "VALIDATION_ERROR",
        "message": "参数验证失败",
        "details": {"field": "email", "error": "无效的邮箱格式"}
    }
}
```

### 6.5 日志规范

**使用结构化日志**:

```python
import logging

logger = logging.getLogger(__name__)

# 正确: 使用 f-string 和结构化信息
logger.info(f"[CHAT] User {user_id} sent message to conversation {conv_id}")
logger.error(f"[AGENT] Tool call failed: {tool_name}, error: {e}")

# 正确: 调试日志使用 debug 级别
logger.debug(f"[SSE] Sending chunk: {len(chunk)} chars")
```

### 6.6 流式输出 (SSE)

**SSE 响应格式**:

```python
from fastapi.responses import StreamingResponse

async def generate():
    async for chunk in stream:
        yield f"data: {json.dumps({'type': 'content', 'data': {'content': chunk}}, ensure_ascii=False)}\n\n"
    yield "data: [DONE]\n\n"

return StreamingResponse(
    generate(),
    media_type="text/event-stream",
    headers={
        "Cache-Control": "no-cache",
        "Connection": "keep-alive",
        "X-Accel-Buffering": "no",
    }
)
```

---

## 7. 常见任务

### 7.1 添加新工具

1. 在 `app/tools/` 创建新文件或编辑现有文件:

```python
from langchain_core.tools import tool

@tool
def new_tool(param: str) -> str:
    """工具描述

    Args:
        param: 参数描述

    Returns:
        结果描述
    """
    return f"处理结果: {param}"
```

2. 在 `app/tools/__init__.py` 中注册:

```python
from .new_tool import new_tool

ALL_TOOLS = [
    # ... 现有工具
    new_tool,
]
```

### 7.2 添加新 API 端点

1. 在 `app/schemas/` 定义请求/响应模型:

```python
from pydantic import BaseModel

class NewFeatureRequest(BaseModel):
    param: str

class NewFeatureResponse(BaseModel):
    result: str
```

2. 在 `app/api/v1/` 添加路由:

```python
@router.post("/new-feature", response_model=NewFeatureResponse)
async def new_feature(
    request: NewFeatureRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    result = await service.do_something(request.param)
    return NewFeatureResponse(result=result)
```

3. 在 `app/main.py` 中注册路由 (如果新文件):

```python
from app.api.v1 import new_router
app.include_router(new_router.router, prefix="/api/v1")
```

### 7.3 添加新模型配置

1. 在 `app/config.py` 的 `Settings` 类中添加:

```python
class Settings(BaseSettings):
    # ... 现有配置
    model_new_feature: str = "default-model-name"
```

2. 在 `app/llm/model_factory.py` 中添加工厂方法:

```python
@classmethod
def get_new_feature_model(cls, **kwargs):
    return AsyncToolModel(
        model_name=settings.model_new_feature,
        api_key=settings.qwen_api_key,
        **kwargs
    )
```

### 7.4 添加数据库迁移

```bash
# 创建迁移
alembic revision --autogenerate -m "描述变更内容"

# 应用迁移
alembic upgrade head

# 回滚
alembic downgrade -1
```

---

## 8. 测试指南

### 8.1 运行测试

```bash
# 运行所有测试
pytest

# 运行特定测试文件
pytest tests/unit/test_chat_service.py

# 运行带覆盖率
pytest --cov=app tests/

# 运行详细输出
pytest -v tests/
```

### 8.2 测试规范

**单元测试**:

```python
import pytest
from unittest.mock import AsyncMock, patch

@pytest.mark.asyncio
async def test_create_message():
    with patch('app.services.message_service.get_db') as mock_db:
        mock_db.add = AsyncMock()
        mock_db.commit = AsyncMock()
        mock_db.refresh = AsyncMock()

        result = await message_service.create_message(
            db=mock_db,
            conversation_id=1,
            message_create=MessageCreate(role="user", content="test"),
            user_id=1
        )

        assert result is not None
```

**集成测试**:

```python
import pytest
from httpx import AsyncClient
from app.main import create_app

@pytest.fixture
async def client():
    app = create_app()
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac

@pytest.mark.asyncio
async def test_chat_endpoint(client: AsyncClient, auth_headers: dict):
    response = await client.post(
        "/api/v1/chat/send",
        json={"conversation_id": 1, "content": "hello"},
        headers=auth_headers
    )
    assert response.status_code == 200
```

---

## 附录

### A. 环境变量

| 变量名 | 说明 | 默认值 |
|--------|------|--------|
| `APP_ENV` | 运行环境 | `development` |
| `DATABASE_URL` | PostgreSQL 连接串 | - |
| `REDIS_URL` | Redis 连接串 | `redis://localhost:6379/0` |
| `QWEN_API_KEY` | 通义千问 API Key | - |
| `TAVILY_API_KEY` | Tavily 搜索 API Key | - |
| `SECRET_KEY` | JWT 密钥 | - |

### B. 常用命令

```bash
# 启动开发服务器
python run.py

# 启动前端开发服务器
cd frontend && npm run dev

# 运行测试
pytest

# 数据库迁移
alembic upgrade head

# 查看日志
tail -f logs/app.log
```

### C. 相关文档

- [LangChain 官方文档](https://python.langchain.com/)
- [FastAPI 官方文档](https://fastapi.tiangolo.com/)
- [Vue 3 官方文档](https://vuejs.org/)
- [项目规则](.trae/rules/project_rules.md)
