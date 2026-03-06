# 🐉 DragonAI v1

智能AI助手系统 - 基于LangChain和LangGraph构建的多功能AI助手平台。

## ✨ 功能特性

- 🤖 **多模型支持**: 集成通义千问系列模型，支持对话、代码、翻译、图像等多种任务
- ⚡ **流式响应**: 基于SSE的实时流式输出，支持心跳保活
- 🔧 **工具调用**: 支持代码执行、文件操作、网络搜索、图像处理等工具
- 📚 **RAG知识库**: 混合检索 + 重排序，支持文档上传和智能问答
- 💬 **多会话管理**: 会话持久化存储，支持历史对话恢复
- 🔐 **安全认证**: JWT令牌认证 + 令牌黑名单机制
- 🛡️ **限流保护**: 可配置的API限流，支持Redis存储
- 🔥 **缓存预热**: Agent缓存预热，减少首次请求延迟
- 📊 **可观测性**: 集成LangSmith追踪，支持请求链路追踪

## 🛠️ 技术栈

### 后端
| 技术 | 说明 |
|------|------|
| 🚀 FastAPI + Uvicorn | 高性能异步Web框架 |
| 🧠 LangChain + LangGraph | AI应用开发框架 |
| 🐘 PostgreSQL + SQLAlchemy | 异步数据库 |
| 📦 Redis | 缓存与限流 |
| 🔍 ChromaDB | 向量数据库 |
| ☁️ 通义千问 | LLM服务 |

### 前端
| 技术 | 说明 |
|------|------|
| 💚 Vue 3 + TypeScript | 渐进式框架 |
| ⚡ Vite | 下一代构建工具 |
| 🍍 Pinia | 状态管理 |
| 🧭 Vue Router | 路由管理 |
| 🎨 自定义组件 | 深色主题支持 |

## 📁 项目结构

```
dragonai-v1/
├── 📂 app/                    # 后端应用
│   ├── 🤖 agents/            # Agent工厂和配置
│   ├── 🌐 api/               # API路由和中间件
│   ├── 💾 cache/             # Redis缓存
│   ├── ⚙️ core/              # 核心模块(数据库、安全等)
│   ├── 🧠 llm/               # LLM模型工厂
│   ├── 📊 models/            # 数据库模型
│   ├── 📖 rag/               # RAG检索模块
│   ├── 📝 schemas/           # Pydantic模型
│   ├── 🔒 security/          # 安全认证
│   ├── 💼 services/          # 业务服务层
│   ├── 🔧 tools/             # 工具模块
│   └── 📦 utils/             # 工具函数
├── 🖥️ frontend/              # 前端应用
│   ├── 📂 src/
│   │   ├── 🧩 components/   # Vue组件
│   │   ├── 📄 views/        # 页面视图
│   │   ├── 🗃️ stores/       # Pinia状态
│   │   └── 🔀 router/       # 路由配置
│   └── ...
├── 🧪 tests/                 # 测试用例
├── 📜 scripts/               # 脚本文件
├── 🔄 alembic/               # 数据库迁移
└── 🌍 nginx/                 # Nginx配置
```

## 🚀 快速开始

### 📋 环境要求

| 依赖 | 版本 |
|------|------|
| 🐍 Python | 3.12+ |
| 💚 Node.js | 18+ |
| 🐘 PostgreSQL | 15+ |
| 📦 Redis | 7+ |

### 🔧 后端配置

1️⃣ 创建虚拟环境并安装依赖:
```bash
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
.venv\Scripts\activate     # Windows
pip install -r requirements.txt
```

2️⃣ 配置环境变量:
```bash
cp .env.example .env
# 编辑 .env 文件，填入必要的配置
```

3️⃣ 初始化数据库:
```bash
alembic upgrade head
python scripts/init_db.py
```

4️⃣ 启动服务:
```bash
python run.py
# 或
uvicorn app.main:app --reload
```

### 🖥️ 前端配置

1️⃣ 安装依赖:
```bash
cd frontend
npm install
```

2️⃣ 启动开发服务器:
```bash
npm run dev
```

3️⃣ 构建生产版本:
```bash
npm run build
```

## ⚙️ 环境变量

| 变量名 | 说明 | 默认值 |
|--------|------|--------|
| `APP_ENV` | 🌍 运行环境 | development |
| `SECRET_KEY` | 🔑 JWT密钥 | - |
| `DATABASE_URL` | 🐘 数据库连接 | - |
| `REDIS_URL` | 📦 Redis连接 | redis://localhost:6379/0 |
| `QWEN_API_KEY` | ☁️ 通义千问API Key | - |
| `TAVILY_API_KEY` | 🔍 Tavily搜索API Key | - |

完整配置参见 [.env.example](.env.example)

## 📖 API文档

启动服务后访问:
- 📚 Swagger UI: http://localhost:8000/docs
- 📑 ReDoc: http://localhost:8000/redoc

## 🐳 Docker部署

```bash
# 构建并启动
docker-compose up -d

# 查看日志
docker-compose logs -f
```

## 🧪 测试

```bash
# 运行所有测试
pytest

# 带覆盖率报告
pytest --cov=app tests/
```

## 📄 许可证

MIT License
