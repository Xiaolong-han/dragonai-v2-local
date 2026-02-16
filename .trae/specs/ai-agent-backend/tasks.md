# AI Agent 后端系统 - 实现计划

## 项目目录结构
```
dragonai-v2-local/
├── app/
│   ├── __init__.py
│   ├── main.py                 # FastAPI应用入口
│   ├── config.py               # 配置管理
│   ├── core/                   # 核心模块
│   │   ├── __init__.py
│   │   ├── database.py         # 数据库连接
│   │   ├── redis.py            # Redis连接
│   │   ├── security.py         # 安全相关（JWT等）
│   │   └── dependencies.py     # FastAPI依赖注入
│   ├── models/                 # 数据模型
│   │   ├── __init__.py
│   │   ├── user.py             # 用户模型
│   │   ├── conversation.py     # 会话模型
│   │   └── message.py          # 消息模型
│   ├── schemas/                # Pydantic模式
│   │   ├── __init__.py
│   │   ├── user.py
│   │   ├── conversation.py
│   │   └── message.py
│   ├── api/                    # API路由
│   │   ├── __init__.py
│   │   ├── v1/
│   │   │   ├── __init__.py
│   │   │   ├── auth.py         # 认证接口
│   │   │   ├── conversations.py # 会话接口
│   │   │   ├── chat.py         # 聊天接口
│   │   │   ├── skills.py       # 技能接口
│   │   │   └── knowledge.py    # 知识库接口
│   ├── services/               # 业务逻辑层
│   │   ├── __init__.py
│   │   ├── user_service.py
│   │   ├── conversation_service.py
│   │   ├── chat_service.py
│   │   └── knowledge_service.py
│   ├── agents/                 # Agent相关
│   │   ├── __init__.py
│   │   ├── base_agent.py       # 基础Agent
│   │   ├── general_agent.py    # 通用聊天Agent
│   │   └── agent_factory.py    # Agent工厂
│   ├── skills/                 # 技能模块（按LangChain官方方式实现）
│   │   ├── __init__.py
│   │   ├── definitions.py      # 技能定义（TypedDict格式）
│   │   ├── loader_tool.py      # load_skill工具
│   │   ├── middleware.py       # SkillMiddleware中间件
│   │   ├── image_generation.py # 图像生成技能实现
│   │   ├── image_editing.py    # 图像编辑技能实现
│   │   ├── coding.py           # 编程技能实现
│   │   └── translation.py      # 翻译技能实现
│   ├── tools/                  # 工具模块
│   │   ├── __init__.py
│   │   ├── rag_tool.py         # RAG检索工具
│   │   ├── web_search_tool.py  # 联网搜索工具
│   │   └── multimodal_tool.py  # 多模态处理工具
│   ├── rag/                    # RAG模块
│   │   ├── __init__.py
│   │   ├── loader.py           # 文档加载器
│   │   ├── splitter.py         # 文档分割器
│   │   ├── embedder.py         # 嵌入器
│   │   └── retriever.py        # 检索器
│   ├── llm/                    # 大模型封装
│   │   ├── __init__.py
│   │   ├── qwen_models.py      # 通义千问模型封装
│   │   └── model_factory.py    # 模型工厂
│   ├── storage/                # 存储模块
│   │   ├── __init__.py
│   │   └── file_storage.py     # 文件存储
│   └── utils/                  # 工具函数
│       ├── __init__.py
│       └── helpers.py
├── tests/                      # 测试
│   ├── __init__.py
│   ├── unit/                   # 单元测试
│   └── integration/            # 集成测试
├── alembic/                    # 数据库迁移
├── .env.example                # 环境变量示例
├── requirements.txt            # 依赖
└── README.md
```

---

## [x] Task 1: 项目初始化与基础架构搭建
- **Priority**: P0
- **Depends On**: None
- **Description**: 
  - 创建项目目录结构
  - 配置Python依赖（requirements.txt）
  - 设置环境变量配置
  - 初始化FastAPI应用
  - 配置日志系统
- **Acceptance Criteria Addressed**: AC-15
- **Test Requirements**:
  - `programmatic` TR-1.1: 项目目录结构符合规范
  - `programmatic` TR-1.2: requirements.txt包含所有必要依赖
  - `programmatic` TR-1.3: FastAPI应用可以正常启动
  - `programmatic` TR-1.4: 健康检查接口返回200
- **Notes**: 确保使用LangChain 1.0+版本

## [x] Task 2: 数据库与缓存层实现
- **Priority**: P0
- **Depends On**: Task 1
- **Description**: 
  - 配置PostgreSQL连接（SQLAlchemy）
  - 配置Redis连接
  - 实现Cache Aside缓存模式
  - 配置PostgresSaver用于Agent状态持久化
  - 配置ChromaDB向量存储
  - 实现数据模型（User、Conversation、Message）
- **Acceptance Criteria Addressed**: AC-13, AC-14
- **Test Requirements**:
  - `programmatic` TR-2.1: PostgreSQL连接正常
  - `programmatic` TR-2.2: Redis连接正常
  - `programmatic` TR-2.3: Cache Aside模式正确实现
  - `programmatic` TR-2.4: PostgresSaver配置正确
  - `programmatic` TR-2.5: ChromaDB初始化成功
  - `programmatic` TR-2.6: 数据模型可以正常创建表

## [x] Task 3: 用户认证与会话管理API
- **Priority**: P0
- **Depends On**: Task 2
- **Description**: 
  - 实现用户名密码认证（配合JWT）
  - 实现用户注册接口（用户名+密码）
  - 实现用户登录接口（用户名+密码）
  - 实现会话CRUD接口（创建、删除、重命名、置顶）
  - 实现会话列表查询接口
  - 实现缓存策略
- **Acceptance Criteria Addressed**: AC-1, AC-2
- **Test Requirements**:
  - `programmatic` TR-3.1: 用户注册（用户名+密码）成功返回200
  - `programmatic` TR-3.2: 用户登录（用户名+密码）成功返回JWT token
  - `programmatic` TR-3.3: 创建会话接口正常工作
  - `programmatic` TR-3.4: 删除/重命名/置顶会话接口正常工作
  - `programmatic` TR-3.5: 会话列表按正确顺序返回
  - `programmatic` TR-3.6: 缓存正确更新

## [x] Task 4: 通义千问模型封装
- **Priority**: P0
- **Depends On**: Task 1
- **Description**: 
  - 封装qwen-flash和qwen3-max通用模型
  - 封装qwen-vl-ocr和qwen3-vl-plus视觉模型
  - 封装z-image-turbo/qwen-image图像生成模型
  - 封装qwen3-coder-flash/qwen3-coder-plus编程模型
  - 封装qwen-mt-flash/qwen-mt-plus翻译模型
  - 实现模型工厂
  - 支持专家模型深度思考功能
- **Acceptance Criteria Addressed**: AC-3, AC-4
- **Test Requirements**:
  - `programmatic` TR-4.1: 通用模型可以正常调用
  - `programmatic` TR-4.2: 视觉模型可以处理图片
  - `programmatic` TR-4.3: 图像生成模型可以生成图片
  - `programmatic` TR-4.4: 编程模型可以生成代码
  - `programmatic` TR-4.5: 翻译模型可以翻译文本
  - `programmatic` TR-4.6: 深度思考功能正常工作

## [x] Task 5: RAG模块实现
- **Priority**: P0
- **Depends On**: Task 2
- **Description**: 
  - 实现文档加载器（支持PDF、WORD、MARKDOWN格式）
  - 实现文档分割器
  - 实现嵌入器（使用通义千问嵌入模型）
  - 实现向量存储到ChromaDB
  - 实现检索器
  - 实现开发者知识库上传接口
  - 实现RAG工具
- **Acceptance Criteria Addressed**: AC-7
- **Test Requirements**:
  - `programmatic` TR-5.1: PDF文档可以正确加载和分割
  - `programmatic` TR-5.2: WORD文档可以正确加载和分割
  - `programmatic` TR-5.3: MARKDOWN文档可以正确加载和分割
  - `programmatic` TR-5.4: 文档可以正确嵌入并存储到ChromaDB
  - `programmatic` TR-5.5: 检索器可以返回相关文档片段
  - `programmatic` TR-5.6: 知识库上传接口正常工作
  - `programmatic` TR-5.7: RAG工具可以被调用

## [x] Task 6: 联网搜索工具实现（使用Tavily）
- **Priority**: P1
- **Depends On**: Task 1
- **Description**: 
  - 集成langchain-community中的TavilySearchResults
  - 实现搜索工具
  - 封装为LangChain工具格式
- **Acceptance Criteria Addressed**: AC-8
- **Test Requirements**:
  - `programmatic` TR-6.1: Tavily搜索工具可以正常调用
  - `programmatic` TR-6.2: 搜索结果格式正确

## [x] Task 7: 技能系统框架（按LangChain官方方式）
- **Priority**: P0
- **Depends On**: Task 4
- **Description**: 
  - 定义Skill TypedDict结构（name、description、content）
  - 实现load_skill工具（使用@tool装饰器）
  - 实现SkillMiddleware中间件，向系统提示词注入技能描述
  - 中间件注册load_skill工具
  - 在before_agent hook中支持技能动态刷新
- **Acceptance Criteria Addressed**: AC-9, AC-10, AC-11, AC-12
- **Test Requirements**:
  - `programmatic` TR-7.1: Skill TypedDict定义正确
  - `programmatic` TR-7.2: load_skill工具可以正常调用并返回技能内容
  - `programmatic` TR-7.3: SkillMiddleware正确向系统提示词注入技能描述
  - `programmatic` TR-7.4: load_skill工具被正确注册到中间件
  - `programmatic` TR-7.5: 技能可以按需加载（仅在需要时加载完整内容）

## [x] Task 8: 专项技能定义与实现
- **Priority**: P0
- **Depends On**: Task 7
- **Description**: 
  - 定义图像生成技能（name、简短description、详细content）
  - 定义图像编辑技能（name、简短description、详细content）
  - 定义编程技能（name、简短description、详细content）
  - 定义翻译技能（name、简短description、详细content）
  - 实现各技能对应的执行逻辑（调用相应的通义千问模型）
  - 为每个技能提供API接口
- **Acceptance Criteria Addressed**: AC-9, AC-10, AC-11, AC-12
- **Test Requirements**:
  - `programmatic` TR-8.1: 图像生成技能定义正确
  - `human-judgment` TR-8.2: 图像生成技能可以生成符合要求的图片
  - `programmatic` TR-8.3: 图像编辑技能定义正确
  - `human-judgment` TR-8.4: 图像编辑技能可以按要求编辑图片
  - `programmatic` TR-8.5: 编程技能定义正确
  - `programmatic` TR-8.6: 编程技能可以生成正确的代码
  - `programmatic` TR-8.7: 翻译技能定义正确
  - `human-judgment` TR-8.8: 翻译技能返回准确的翻译结果

## [x] Task 9: 多模态处理实现
- **Priority**: P0
- **Depends On**: Task 4
- **Description**: 
  - 实现文档理解（OCR）
  - 实现图片理解
  - 实现文件上传处理
  - 实现文件存储到本地文件系统
- **Acceptance Criteria Addressed**: AC-5, AC-6
- **Test Requirements**:
  - `programmatic` TR-9.1: 文档可以正确上传和存储到本地文件系统
  - `programmatic` TR-9.2: 图片可以正确上传和存储到本地文件系统
  - `programmatic` TR-9.3: OCR可以正确提取文档内容
  - `human-judgment` TR-9.4: 图片理解结果准确

## [x] Task 10: Agent系统实现（使用create_agent）
- **Priority**: P0
- **Depends On**: Task 4, Task 5, Task 6, Task 7
- **Description**: 
  - 使用langchain.agents.create_agent创建Agent
  - 配置系统提示词
  - 添加SkillMiddleware中间件
  - 配置PostgresSaver作为checkpointer
  - 集成所有工具（RAG、搜索、多模态）
  - 实现Agent工厂
  - 遵循LangChain官方最佳实践
- **Acceptance Criteria Addressed**: AC-3, AC-4, AC-5, AC-6, AC-7, AC-8, AC-14
- **Test Requirements**:
  - `programmatic` TR-10.1: 使用create_agent成功创建Agent
  - `programmatic` TR-10.2: SkillMiddleware正确加载
  - `programmatic` TR-10.3: PostgresSaver正确配置
  - `programmatic` TR-10.4: Agent可以调用RAG工具
  - `programmatic` TR-10.5: Agent可以调用搜索工具
  - `programmatic` TR-10.6: Agent可以调用load_skill工具加载技能
  - `programmatic` TR-10.7: Agent状态可以正确持久化和恢复
  - `programmatic` TR-10.8: 完全遵循LangChain 1.0官方最佳实践

## [x] Task 11: 聊天API实现
- **Priority**: P0
- **Depends On**: Task 3, Task 10
- **Description**: 
  - 实现聊天发送接口
  - 实现消息历史查询接口
  - 支持模型选择（快速/专家）
  - 支持多模态输入
  - 实现流式响应（SSE）
  - 集成缓存策略
- **Acceptance Criteria Addressed**: AC-1, AC-2, AC-3, AC-4, AC-5, AC-6
- **Test Requirements**:
  - `programmatic` TR-11.1: 聊天接口可以正常发送消息
  - `programmatic` TR-11.2: 消息历史可以正确查询
  - `programmatic` TR-11.3: 模型选择功能正常
  - `programmatic` TR-11.4: 多模态输入可以正确处理
  - `programmatic` TR-11.5: 流式响应正常工作
  - `programmatic` TR-11.6: 缓存正确更新

## [x] Task 12: 单元测试编写
- **Priority**: P0
- **Depends On**: Task 1-11
- **Description**: 
  - 为所有Service层编写单元测试
  - 为所有工具函数编写单元测试
  - 为所有Agent和技能编写单元测试
  - 确保代码覆盖率>80%
- **Acceptance Criteria Addressed**: AC-15
- **Test Requirements**:
  - `programmatic` TR-12.1: 所有单元测试可以独立运行
  - `programmatic` TR-12.2: 单元测试通过率100%
  - `programmatic` TR-12.3: 代码覆盖率>80%

## [x] Task 13: 集成测试编写
- **Priority**: P0
- **Depends On**: Task 1-12
- **Description**: 
  - 为API接口编写集成测试
  - 为完整聊天流程编写集成测试
  - 为技能调用编写集成测试
  - 为数据持久化编写集成测试
- **Acceptance Criteria Addressed**: AC-15
- **Test Requirements**:
  - `programmatic` TR-13.1: 所有集成测试可以正常运行
  - `programmatic` TR-13.2: 集成测试通过率100%

## [x] Task 14: 部署文档与配置
- **Priority**: P1
- **Depends On**: Task 1-13
- **Description**: 
  - 编写部署文档
  - 提供.env.example配置文件
  - 编写数据库初始化脚本
  - 提供启动脚本
- **Acceptance Criteria Addressed**: （部署相关）
- **Test Requirements**:
  - `human-judgement` TR-14.1: 部署文档清晰易懂
  - `programmatic` TR-14.2: 配置文件示例完整
  - `programmatic` TR-14.3: 启动脚本可以正常工作
