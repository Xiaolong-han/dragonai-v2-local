## Qwen 模型集成架构优化计划

### 架构设计原则
| 模型类型 | 集成方式 | 调用方式 | 原因 |
|---------|---------|---------|------|
| Agent核心模型 | `ChatOpenAI` | **仅异步** | LangGraph集成、工具调用、支持`extra_body`传递`enable_thinking` |
| 技能模型(视觉/OCR/编程/翻译) | 原生`OpenAI` SDK | **仅异步** | 简单直接，无需LangChain抽象层 |
| Embedding | `DashScopeEmbeddings` | **仅异步** | 官方集成，支持text-embedding-v4 |
| 图像生成/编辑 | HTTP (httpx) | **仅异步** | 耗时操作，避免阻塞 |

### 统一异步设计
- 所有模型方法统一使用 `async/await`
- 方法命名统一：`ainvoke()`, `agenerate()`, `aembed_documents()` 等
- 项目基于 FastAPI，异步避免阻塞，提高并发性能

### 实施步骤

**1. 更新 `config.py`**
- 添加 Embedding 模型配置项 `model_embedding`

**2. 重构 `model_factory.py`**
- `get_general_model()` → 使用 `extra_body` 传递 `enable_thinking`
- `get_vision_model()` → 返回异步模型封装
- `get_coder_model()` → 返回异步模型封装
- `get_translation_model()` → 返回异步模型封装
- `get_image_model()` / `get_image_edit_model()` → 仅异步方法
- 新增 `get_embedding()` → 使用 `DashScopeEmbeddings`

**3. 简化 `qwen_models.py`**
- 删除 `BaseSkillModel`, `QwenVisionModel`, `QwenCoderModel`, `QwenTranslationModel`
- 重构 `QwenImageModel`：仅保留异步方法

**4. 简化 `embedder.py`**
- 删除自定义 `QwenEmbeddings` 类
- 直接从 `ModelFactory.get_embedding()` 获取

**5. 更新工具文件**
- 适配新的异步模型接口

**6. 验证测试**
- 运行类型检查和测试