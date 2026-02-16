# AI Agent 后端系统 - 产品需求文档

## Overview
- **Summary**: 本项目旨在构建一个类似豆包网站的AI Agent后端系统，支持多种技能和本地轻量部署。系统将使用FastAPI作为后端框架，LangChain 1.0作为AI Agent开发框架，集成多种通义千问模型，实现通用聊天、RAG检索、联网搜索、多模态输入、以及多种专项技能（编程、翻译、图像生成等）。
- **Purpose**: 提供一个功能完整、架构清晰的AI Agent后端系统，支持灵活扩展多种技能，同时保证本地部署的便捷性。
- **Target Users**: AI应用开发者、需要本地部署AI服务的企业和个人用户。

## Goals
- 构建基于FastAPI和LangChain 1.0的后端系统架构
- 实现通用大模型聊天功能，支持快速模型(qwen-flash)和专家模型(qwen3-max)切换
- 集成多模态输入处理（文本、文档、图片）
- 实现RAG检索和联网搜索功能
- 开发多种专项技能：编程、翻译、图像生成与编辑
- 实现用户认证与会话管理
- 提供完整的单元测试和集成测试
- 支持本地轻量部署

## Non-Goals (Out of Scope)
- 前端界面的开发（当前版本不考虑）
- Docker容器化部署（后续版本考虑）
- 图生视频功能（预留扩展接口）
- 多租户企业级部署（当前版本仅支持单用户或简单多用户）

## Background & Context
- 技术栈已明确：FastAPI + LangChain 1.0 + Python 3.13
- 数据库方案：PostgreSQL（业务数据）+ Redis（会话缓存，Cache Aside模式）+ ChromaDB（向量存储）
- Agent记忆使用LangChain自带的PostgresSaver
- 所有AI模型均使用阿里云通义千问系列模型
- 项目需遵循LangChain官方最佳实践

## Functional Requirements
- **FR-1**: 用户认证与会话管理
  - 用户登录/注册
  - 会话列表展示
  - 会话创建、删除、重命名、置顶
- **FR-2**: 通用聊天功能
  - 支持快速模型(qwen-flash)和专家模型(qwen3-max)选择
  - 专家模型支持深度思考，显示思考过程
  - 纯文本对话
  - 多模态输入（文档、图片）
- **FR-3**: RAG检索与联网搜索
  - 开发者可上传知识库文档
  - 通用模型可自主决定是否调用RAG或联网搜索
  - RAG结果与联网搜索结果整合
- **FR-4**: 技能系统（按LangChain官方方式实现）
  - 使用Skill TypedDict结构定义技能（name、description、content）
  - 实现load_skill工具按需加载技能完整内容
  - 实现SkillMiddleware向系统提示词注入技能描述
  - 图像生成与编辑技能（使用z-image-turbo/qwen-image）
  - 编程技能（使用qwen3-coder-flash/qwen3-coder-plus）
  - 翻译技能（使用qwen-mt-flash/qwen-mt-plus）
  - 技能可通过load_skill工具被通用模型调用
  - 预留技能扩展接口，支持动态添加新技能
- **FR-5**: 多模态处理
  - 文档理解（使用qwen-vl-ocr）
  - 图片理解（使用qwen3-vl-plus）
  - 图片生成与编辑
- **FR-6**: 数据持久化
  - 业务数据存储到PostgreSQL
  - Agent状态使用PostgresSaver持久化
  - 会话缓存使用Redis（Cache Aside模式）
  - 向量数据存储到ChromaDB

## Non-Functional Requirements
- **NFR-1**: 系统响应时间：普通文本对话响应时间<3秒
- **NFR-2**: 可扩展性：技能模块支持热插拔，无需重启服务
- **NFR-3**: 可靠性：关键数据双重备份（DB + Redis）
- **NFR-4**: 可测试性：代码覆盖率>80%，单元测试和集成测试完整
- **NFR-5**: 部署便捷性：本地部署步骤简单，配置清晰

## Constraints
- **Technical**: 
  - Python 3.13
  - FastAPI
  - LangChain 1.0+ (不使用0.x版本)
  - PostgreSQL
  - Redis
  - ChromaDB
- **Business**: 
  - 本地部署，暂不考虑云服务
  - v1版本完成周期：需按计划分阶段交付
- **Dependencies**: 
  - 阿里云通义千问API服务
  - LangChain官方文档和最佳实践

## Assumptions
- 用户已配置好阿里云API Key
- 本地已安装PostgreSQL、Redis和Python 3.13
- 用户有基本的Python后端开发经验
- 阿里云通义千问API服务可用

## Acceptance Criteria

### AC-1: 用户认证与会话管理
- **Given**: 系统已启动且数据库连接正常
- **When**: 用户发起登录/注册请求
- **Then**: 系统验证用户身份并返回认证令牌
- **Verification**: `programmatic`
- **Notes**: 使用JWT令牌认证

### AC-2: 会话操作功能
- **Given**: 用户已登录
- **When**: 用户创建/删除/重命名/置顶会话
- **Then**: 会话列表正确更新并持久化到数据库
- **Verification**: `programmatic`

### AC-3: 通用聊天功能
- **Given**: 用户已选择模型（快速/专家）
- **When**: 用户发送纯文本消息
- **Then**: 系统返回对应模型生成的回复
- **Verification**: `programmatic`

### AC-4: 专家模型深度思考
- **Given**: 用户选择专家模型并开启深度思考
- **When**: 用户发送需要思考的问题
- **Then**: 系统返回完整的思考过程和最终答案
- **Verification**: `programmatic`

### AC-5: 文档理解
- **Given**: 用户上传文档文件
- **When**: 用户发送与文档相关的问题
- **Then**: 系统结合文档内容给出回答
- **Verification**: `programmatic`

### AC-6: 图片理解
- **Given**: 用户上传图片
- **When**: 用户询问图片内容
- **Then**: 系统正确理解并描述图片内容
- **Verification**: `human-judgment`

### AC-7: RAG检索功能
- **Given**: 开发者已上传知识库文档
- **When**: 用户询问与知识库相关的问题
- **Then**: 系统从知识库检索相关内容并整合到回答中
- **Verification**: `programmatic`

### AC-8: 联网搜索功能
- **Given**: 用户询问需要实时信息的问题
- **When**: 通用模型决定调用联网搜索
- **Then**: 系统执行搜索并将结果整合到回答中
- **Verification**: `programmatic`

### AC-9: 图像生成技能
- **Given**: 用户选择图像生成技能或通用模型调用该技能
- **When**: 用户输入图像描述
- **Then**: 系统生成并返回图片
- **Verification**: `human-judgment`

### AC-10: 图像编辑技能
- **Given**: 用户上传图片并选择图像编辑技能
- **When**: 用户输入编辑指令
- **Then**: 系统编辑图片并返回结果
- **Verification**: `human-judgment`

### AC-11: 编程技能
- **Given**: 用户选择编程技能
- **When**: 用户输入编程需求
- **Then**: 系统使用编程模型生成代码
- **Verification**: `programmatic`

### AC-12: 翻译技能
- **Given**: 用户选择翻译技能
- **When**: 用户输入待翻译文本
- **Then**: 系统使用翻译模型返回翻译结果
- **Verification**: `human-judgment`

### AC-13: 数据持久化
- **Given**: 系统正在运行
- **When**: 发生任何数据变更（会话、消息等）
- **Then**: 数据正确保存到PostgreSQL，Redis缓存保持一致
- **Verification**: `programmatic`

### AC-14: Agent状态持久化
- **Given**: 用户正在进行多轮对话
- **When**: 对话中断后重新开始
- **Then**: Agent状态从PostgresSaver正确恢复
- **Verification**: `programmatic`

### AC-15: 测试覆盖
- **Given**: 代码开发完成
- **When**: 运行完整测试套件
- **Then**: 所有测试用例100%通过
- **Verification**: `programmatic`

## Open Questions
- [x] 用户认证的具体实现方式：用户名密码认证
- [x] RAG知识库的文档格式支持：PDF、WORD、MARKDOWN
- [x] 联网搜索使用：langchain-community中的Tavily
- [x] 图片和文档的存储方式：本地文件系统
