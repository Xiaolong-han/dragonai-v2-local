# DragonAI V2 系统性优化方案

## 一、项目现状分析

### 1.1 当前架构概览

**后端 (FastAPI + Python 3.13)**
- 主框架: FastAPI 0.115.0+
- AI框架: LangChain 1.0.0+ (符合项目规则)
- 数据库: PostgreSQL + SQLAlchemy 2.0 + Alembic
- 缓存: Redis
- 向量存储: ChromaDB
- 模型: 通义千问(Qwen)系列模型

**前端 (Vue 3 + TypeScript)**
- 框架: Vue 3 + Vite
- UI库: Element Plus
- 状态管理: Pinia
- HTTP客户端: Axios

### 1.2 当前功能模块

| 模块 | 状态 | 问题 |
|------|------|------|
| 通用聊天 | ✅ 基础可用 | 未使用Agent架构，缺少工具调用 |
| 模型选择 | ✅ 基础可用 | 仅支持快速/专家切换 |
| 图像生成 | ✅ 基础可用 | 未接入Agent工具链 |
| 图像编辑 | ✅ 基础可用 | 未接入Agent工具链 |
| 编程 | ✅ 基础可用 | 未接入Agent工具链 |
| 翻译 | ✅ 基础可用 | 未接入Agent工具链 |
| RAG检索 | ✅ 基础可用 | 未接入Agent工具链 |
| 联网搜索 | ✅ 基础可用 | 未接入Agent工具链 |
| 多模态输入 | ⚠️ 部分支持 | 图片理解已实现，文档处理待完善 |
| 深度思考 | ⚠️ 部分支持 | 后端支持，前端未展示思考过程 |

### 1.3 核心问题识别

1. **架构层面**
   - Agent架构不完整：使用了`create_agent`但工具调用机制未正确配置
   - 技能中间件复杂化：使用了`SkillMiddleware`和`load_skill`，不符合项目规则要求
   - 工具未统一封装：RAG、搜索、技能等工具未以Function Calling方式提供给Agent

2. **功能层面**
   - 主聊天未触发技能调用：用户输入无法自动触发图像生成、编程等技能
   - 深度思考过程未展示：前端缺少思考过程UI
   - 模型配置不够灵活：模型名称硬编码，开发者配置能力有限

3. **代码结构层面**
   - 模型类职责不单一：`QwenChatModel`混合了同步/异步/流式逻辑
   - 工具定义分散：工具分布在多个文件，缺乏统一管理

4. **用户体验层面**
   - 缺少思考过程展示
   - 技能调用结果展示不统一
   - 流式响应处理不够完善

---

## 二、优化目标

### 2.1 总体目标
构建一个以通用大模型为核心的AI Agent智能体，支持：
- 多模态问答（文本、图片、文档）
- 智能工具调用（RAG、联网搜索、图像生成、编程、翻译等）
- 快速/专家模型切换
- 深度思考过程展示
- 统一的前后端交互体验

### 2.2 具体目标

| 目标 | 优先级 | 验收标准 |
|------|--------|----------|
| 重构Agent架构 | P0 | 使用LangChain 1.0+推荐的create_agent，无需AgentExecutor |
| 统一工具封装 | P0 | 所有工具使用@tool装饰器，直接传递给create_agent |
| 主聊天触发技能 | P0 | 用户输入自动识别意图，调用对应技能工具 |
| 专项技能直接触发 | P0 | 支持用户单独点击专有功能，直接使用专用模型完成 |
| 深度思考展示 | P1 | 前端展示思考过程，支持展开/收起 |
| 模型配置化 | P1 | 开发者可通过配置自定义模型映射 |
| 代码结构优化 | P1 | 单一职责原则，降低耦合度 |
| 前端体验优化 | P2 | 消息展示优化，加载状态完善 |

---

## 三、优化方案详述

### 3.1 架构重构方案

#### 3.1.1 新架构设计

```
┌─────────────────────────────────────────────────────────────────┐
│                         前端 (Vue 3)                             │
├─────────────────────────────────────────────────────────────────┤
│  ChatView → ChatInput → ModelSelector → SkillIndicator          │
│       ↓                                                           │
│  ChatStore (Pinia) → API Client → SSE Stream Handler            │
│       ↓                                                           │
│  SkillPage (图像/编程/翻译) → Direct Skill API                  │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                      FastAPI Backend                             │
├─────────────────────────────────────────────────────────────────┤
│  /api/v1/chat/send → ChatService → create_agent                 │
│       ↓                              ↓                          │
│  ConversationService              tools=[...]                   │
│                              /          \                       │
│                    Core Tools    Skill Tools                    │
│                    (RAG/搜索)   (图像/编程/翻译)                 │
├─────────────────────────────────────────────────────────────────┤
│  /api/v1/skills/direct/* → DirectSkillService → 专用模型        │
│       ↓                                                           │
│  图像生成: QwenImageModel (qwen-image/z-image-turbo)            │
│  图像编辑: QwenImageModel                                       │
│  编程: QwenCoderModel (qwen3-coder-flash/qwen3-coder-plus)      │
│  翻译: QwenTranslationModel (qwen-mt-flash/qwen-mt-plus)        │
└─────────────────────────────────────────────────────────────────┘
```

#### 3.1.2 两种触发模式说明

**模式一：主聊天Agent触发（智能识别）**
- 用户通过主聊天界面输入自然语言
- Agent根据意图自动选择并调用工具
- 适用于：用户不明确指定功能，由Agent智能判断

**模式二：专项技能直接触发（专用模型）**
- 用户点击前端专项功能入口（如"图像生成"、"编程助手"）
- 前端直接调用专用API，使用对应专用模型
- 不经过Agent，直接调用tool函数
- 适用于：用户明确知道需要什么功能

### 3.2 Agent架构改造 (主聊天模式)

#### 3.2.1 Agent架构改造 (LangChain 1.0+ 推荐方式)

```python
# 新实现 - 使用LangChain 1.0+推荐的create_agent
# 参考: https://python.langchain.com/docs/how_to/agent/
from langchain.agents import create_agent
from langchain_core.tools import tool
from langgraph.checkpoint.postgres import PostgresSaver

# 1. 定义工具 - 使用@tool装饰器即可
@tool
def search_knowledge_base(query: str) -> str:
    """从本地知识库搜索信息."""
    ...

@tool
def generate_image(prompt: str) -> str:
    """根据描述生成图像."""
    ...

# 2. 创建PostgresSaver用于对话状态持久化
checkpointer = PostgresSaver.from_conn_string(
    "postgresql://user:password@localhost:5432/dbname"
)

# 3. 创建Agent (无需AgentExecutor)
agent = create_agent(
    model="qwen-flash",  # 或传入model实例
    tools=[search_knowledge_base, generate_image, ...],
    system_prompt="你是一个强大的AI助手...",
    checkpointer=checkpointer,  # 传入checkpointer实现对话状态持久化
)

# 4. 调用时传入config指定会话ID
config = {"configurable": {"thread_id": "conversation_123"}}
response = agent.invoke(
    {"messages": [{"role": "user", "content": "生成一张猫咪图片"}]},
    config
)

# 5. 流式调用
for event in agent.stream(
    {"messages": [{"role": "user", "content": "生成一张猫咪图片"}]},
    config,
    stream_mode="values"
):
    print(event["messages"][-1])
```

### 3.3 专项技能直接触发方案

#### 3.3.1 直接触发架构

```python
# app/api/v1/skills_direct.py

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from typing import Optional, List, Literal
import json

from app.llm.model_factory import ModelFactory
from app.tools.image_tools import generate_image, edit_image
from app.tools.code_tools import code_assist
from app.tools.translation_tools import translate_text

router = APIRouter()


class ImageGenerateRequest(BaseModel):
    """图像生成请求"""
    prompt: str = Field(..., description="图像描述")
    size: str = Field("1024*1024", description="图像尺寸")
    n: int = Field(1, description="生成数量")
    model_mode: Literal["fast", "expert"] = Field("fast", description="模型模式")


class ImageEditRequest(BaseModel):
    """图像编辑请求"""
    image_url: str = Field(..., description="原图URL")
    prompt: str = Field(..., description="编辑指令")
    model_mode: Literal["fast", "expert"] = Field("fast", description="模型模式")


class CodeAssistRequest(BaseModel):
    """编程协助请求"""
    prompt: str = Field(..., description="编程需求")
    language: str = Field("python", description="编程语言")
    model_mode: Literal["fast", "expert"] = Field("fast", description="模型模式")


class TranslateRequest(BaseModel):
    """翻译请求"""
    text: str = Field(..., description="待翻译文本")
    target_lang: str = Field(..., description="目标语言")
    source_lang: Optional[str] = Field(None, description="源语言")
    model_mode: Literal["fast", "expert"] = Field("fast", description="模型模式")


@router.post("/image/generate")
async def direct_image_generate(
    request: ImageGenerateRequest,
    current_user: User = Depends(get_current_active_user)
):
    """
    直接触发图像生成 - 不经过Agent
    
    使用专用图像生成模型（qwen-image 或 z-image-turbo）
    适用于用户明确需要图像生成的场景
    """
    # 直接使用专用模型，不经过Agent
    model = ModelFactory.get_image_model(
        is_turbo=request.model_mode == "fast"
    )
    
    urls = model.generate(
        prompt=request.prompt,
        size=request.size,
        n=request.n
    )
    
    return {
        "success": True,
        "data": {
            "urls": urls,
            "prompt": request.prompt
        }
    }


@router.post("/image/edit")
async def direct_image_edit(
    request: ImageEditRequest,
    current_user: User = Depends(get_current_active_user)
):
    """
    直接触发图像编辑 - 不经过Agent
    
    使用专用图像编辑模型
    """
    model = ModelFactory.get_image_model(
        is_turbo=request.model_mode == "fast"
    )
    
    url = model.edit(
        image_url=request.image_url,
        prompt=request.prompt
    )
    
    return {
        "success": True,
        "data": {
            "url": url,
            "prompt": request.prompt
        }
    }


@router.post("/code/assist")
async def direct_code_assist(
    request: CodeAssistRequest,
    current_user: User = Depends(get_current_active_user)
):
    """
    直接触发编程协助 - 不经过Agent
    
    使用专用编程模型（qwen3-coder-flash 或 qwen3-coder-plus）
    支持流式输出
    """
    if request.stream:
        async def event_generator():
            model = ModelFactory.get_coder_model(
                is_plus=request.model_mode == "expert"
            )
            
            messages = [
                {"role": "system", "content": f"你是一个专业的{request.language}编程助手。"},
                {"role": "user", "content": request.prompt}
            ]
            
            async for chunk in model.astream(messages):
                yield f"data: {json.dumps({'type': 'content', 'data': chunk.content})}\n\n"
            
            yield "data: [DONE]\n\n"
        
        return StreamingResponse(
            event_generator(),
            media_type="text/event-stream"
        )
    else:
        model = ModelFactory.get_coder_model(
            is_plus=request.model_mode == "expert"
        )
        
        messages = [
            {"role": "system", "content": f"你是一个专业的{request.language}编程助手。"},
            {"role": "user", "content": request.prompt}
        ]
        
        result = model.invoke(messages)
        
        return {
            "success": True,
            "data": {
                "content": result.content
            }
        }


@router.post("/translate")
async def direct_translate(
    request: TranslateRequest,
    current_user: User = Depends(get_current_active_user)
):
    """
    直接触发翻译 - 不经过Agent
    
    使用专用翻译模型（qwen-mt-flash 或 qwen-mt-plus）
    """
    model = ModelFactory.get_translation_model(
        is_plus=request.model_mode == "expert"
    )
    
    result = model.translate(
        text=request.text,
        source_lang=request.source_lang,
        target_lang=request.target_lang
    )
    
    return {
        "success": True,
        "data": {
            "original": request.text,
            "translated": result,
            "source_lang": request.source_lang or "auto",
            "target_lang": request.target_lang
        }
    }
```

#### 3.3.2 前端专项技能页面

```vue
<!-- frontend/src/views/ImageGeneration.vue -->
<template>
  <div class="skill-page">
    <div class="skill-header">
      <h2>图像生成</h2>
      <p>使用AI生成高质量图像</p>
    </div>
    
    <div class="skill-content">
      <!-- 模型选择 -->
      <ModelSelector v-model="modelMode" type="image" />
      
      <!-- 输入区域 -->
      <div class="input-section">
        <el-input
          v-model="prompt"
          type="textarea"
          :rows="4"
          placeholder="描述你想要生成的图像..."
        />
        
        <div class="options">
          <el-select v-model="size" placeholder="图像尺寸">
            <el-option label="1024×1024" value="1024*1024" />
            <el-option label="1024×768" value="1024*768" />
            <el-option label="768×1024" value="768*1024" />
          </el-select>
          
          <el-input-number v-model="n" :min="1" :max="4" label="数量" />
        </div>
        
        <el-button
          type="primary"
          :loading="loading"
          @click="generate"
        >
          生成图像
        </el-button>
      </div>
      
      <!-- 结果展示 -->
      <div v-if="result" class="result-section">
        <div class="image-grid">
          <img
            v-for="(url, idx) in result.urls"
            :key="idx"
            :src="url"
            @click="previewImage(url)"
          />
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useSkillStore } from '@/stores/skill'
import ModelSelector from '@/components/ModelSelector.vue'

const skillStore = useSkillStore()

const modelMode = ref<'fast' | 'expert'>('fast')
const prompt = ref('')
const size = ref('1024*1024')
const n = ref(1)
const loading = ref(false)
const result = ref<any>(null)

async function generate() {
  loading.value = true
  try {
    // 直接调用专项技能API，不经过主聊天Agent
    result.value = await skillStore.directImageGenerate({
      prompt: prompt.value,
      size: size.value,
      n: n.value,
      model_mode: modelMode.value
    })
  } finally {
    loading.value = false
  }
}
</script>
```

```typescript
// frontend/src/stores/skill.ts
import { defineStore } from 'pinia'
import axios from 'axios'

export const useSkillStore = defineStore('skill', () => {
  // 直接调用专项技能API（不经过主聊天Agent）
  async function directImageGenerate(params: {
    prompt: string
    size: string
    n: number
    model_mode: 'fast' | 'expert'
  }) {
    const response = await axios.post('/api/v1/skills/direct/image/generate', params)
    return response.data.data
  }
  
  async function directImageEdit(params: {
    image_url: string
    prompt: string
    model_mode: 'fast' | 'expert'
  }) {
    const response = await axios.post('/api/v1/skills/direct/image/edit', params)
    return response.data.data
  }
  
  async function directCodeAssist(params: {
    prompt: string
    language: string
    model_mode: 'fast' | 'expert'
    stream?: boolean
  }) {
    if (params.stream) {
      // 流式处理
      const response = await fetch('/api/v1/skills/direct/code/assist', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(params)
      })
      return response.body
    } else {
      const response = await axios.post('/api/v1/skills/direct/code/assist', params)
      return response.data.data
    }
  }
  
  async function directTranslate(params: {
    text: string
    target_lang: string
    source_lang?: string
    model_mode: 'fast' | 'expert'
  }) {
    const response = await axios.post('/api/v1/skills/direct/translate', params)
    return response.data.data
  }
  
  return {
    directImageGenerate,
    directImageEdit,
    directCodeAssist,
    directTranslate
  }
})
```

### 3.4 工具统一封装方案

#### 3.4.1 简化方案 - 直接使用@tool装饰器

**RAG工具：**
```python
# app/tools/rag_tool.py
from langchain_core.tools import tool
from app.services.knowledge_service import KnowledgeService

@tool
def search_knowledge_base(query: str, k: int = 4) -> str:
    """
    从本地知识库中搜索相关文档。
    
    当用户询问项目文档、技术规范、API文档等相关问题时使用此工具。
    
    Args:
        query: 搜索查询语句
        k: 返回文档数量，默认4条
        
    Returns:
        相关文档的格式化内容
    """
    service = KnowledgeService()
    documents = service.search(query, k=k)
    
    if not documents:
        return "未找到相关文档。"
    
    formatted = []
    for i, doc in enumerate(documents, 1):
        source = doc.metadata.get("source", "未知")
        formatted.append(f"[文档 {i}] 来源: {source}\n{doc.page_content}\n")
    
    return "\n".join(formatted)
```

**搜索工具：**
```python
# app/tools/web_search_tool.py
from langchain_core.tools import tool
from langchain_community.tools.tavily_search import TavilySearchResults
from app.config import settings

@tool
def web_search(query: str) -> str:
    """
    使用联网搜索获取最新信息。
    
    当用户询问实时信息、新闻、当前事件或知识库中未包含的内容时使用此工具。
    
    Args:
        query: 搜索查询语句
        
    Returns:
        搜索结果的格式化摘要
    """
    search_tool = TavilySearchResults(
        api_key=settings.tavily_api_key,
        max_results=5,
        search_depth="advanced"
    )
    results = search_tool.invoke({"query": query})
    return str(results)
```

**图像生成工具（同时支持Agent调用和直接调用）：**
```python
# app/tools/image_tools.py
from langchain_core.tools import tool
from app.llm.model_factory import ModelFactory

@tool
def generate_image(prompt: str, size: str = "1024*1024", n: int = 1) -> str:
    """
    根据文本描述生成图像。
    
    当用户要求生成图像、绘画、设计图或任何视觉内容时使用此工具。
    
    Args:
        prompt: 图像的详细描述，越详细效果越好
        size: 图像尺寸，可选 "1024*1024", "1024*768", "768*1024"
        n: 生成图像数量，1-4之间
        
    Returns:
        生成图像的URL列表
    """
    model = ModelFactory.get_image_model(is_turbo=True)
    urls = model.generate(prompt, size=size, n=n)
    return f"图像已生成：{', '.join(urls)}"

@tool
def edit_image(image_url: str, prompt: str) -> str:
    """
    根据编辑指令修改现有图像。
    
    当用户要求修改、优化或变换已有图像时使用此工具。
    
    Args:
        image_url: 待编辑图像的URL
        prompt: 编辑指令描述
        
    Returns:
        编辑后图像的URL
    """
    model = ModelFactory.get_image_model(is_turbo=True)
    url = model.edit(image_url=image_url, prompt=prompt)
    return f"图像编辑完成：{url}"
```

**编程工具：**
```python
# app/tools/code_tools.py
from langchain_core.tools import tool
from app.llm.model_factory import ModelFactory

@tool
def code_assist(prompt: str, language: str = "python") -> str:
    """
    协助编程任务，包括代码生成、调试、解释和优化。
    
    当用户需要编写代码、解决编程问题、理解代码或优化代码时使用此工具。
    
    Args:
        prompt: 编程需求描述
        language: 编程语言，默认python
        
    Returns:
        代码及解释
    """
    model = ModelFactory.get_coder_model(is_plus=False)
    messages = [
        {"role": "system", "content": f"你是一个专业的{language}编程助手。"},
        {"role": "user", "content": prompt}
    ]
    result = model.invoke(messages)
    return result.content
```

**翻译工具：**
```python
# app/tools/translation_tools.py
from langchain_core.tools import tool
from app.llm.model_factory import ModelFactory

@tool
def translate_text(text: str, target_lang: str, source_lang: str = None) -> str:
    """
    将文本翻译成目标语言。
    
    当用户需要翻译内容时使用此工具。
    
    Args:
        text: 待翻译的文本
        target_lang: 目标语言代码 (zh, en, ja, ko, fr, de, es等)
        source_lang: 源语言代码，不传则自动检测
        
    Returns:
        翻译后的文本
    """
    model = ModelFactory.get_translation_model(is_plus=False)
    return model.translate(text, source_lang=source_lang, target_lang=target_lang)
```

#### 3.4.2 工具导出

```python
# app/tools/__init__.py
from .rag_tool import search_knowledge_base
from .web_search_tool import web_search
from .multimodal_tool import ocr_document, understand_image
from .image_tools import generate_image, edit_image
from .code_tools import code_assist
from .translation_tools import translate_text

# 所有工具列表 - 直接传递给create_agent
ALL_TOOLS = [
    search_knowledge_base,
    web_search,
    ocr_document,
    understand_image,
    generate_image,
    edit_image,
    code_assist,
    translate_text,
]

__all__ = [
    "ALL_TOOLS",
    "search_knowledge_base",
    "web_search",
    "ocr_document",
    "understand_image",
    "generate_image",
    "edit_image",
    "code_assist",
    "translate_text",
]
```

### 3.5 模型配置化方案

#### 3.5.1 配置文件扩展

```python
# app/config.py - 模型配置扩展

class ModelConfig:
    """模型配置类 - 开发者可自定义模型映射"""
    
    # 通用模型配置
    GENERAL_FAST = "qwen-flash"
    GENERAL_EXPERT = "qwen3-max"
    
    # 视觉模型配置
    VISION_OCR = "qwen-vl-ocr"
    VISION_GENERAL = "qwen3-vl-plus"
    
    # 图像生成模型配置
    IMAGE_FAST = "z-image-turbo"
    IMAGE_EXPERT = "qwen-image"
    
    # 编程模型配置
    CODER_FAST = "qwen3-coder-flash"
    CODER_EXPERT = "qwen3-coder-plus"
    
    # 翻译模型配置
    TRANSLATION_FAST = "qwen-mt-flash"
    TRANSLATION_EXPERT = "qwen-mt-plus"
    
    # 模型能力配置
    CAPABILITIES = {
        "qwen3-max": {"supports_thinking": True, "supports_streaming": True},
        "qwen-flash": {"supports_thinking": False, "supports_streaming": True},
        "qwen3-vl-plus": {"supports_thinking": False, "supports_streaming": True},
        "qwen-vl-ocr": {"supports_thinking": False, "supports_streaming": True},
    }


class Settings(BaseSettings):
    # ... 现有配置 ...
    
    # 模型配置覆盖 - 允许开发者自定义
    model_general_fast: str = "qwen-flash"
    model_general_expert: str = "qwen3-max"
    model_vision_ocr: str = "qwen-vl-ocr"
    model_vision_general: str = "qwen3-vl-plus"
    model_image_fast: str = "z-image-turbo"
    model_image_expert: str = "qwen-image"
    model_coder_fast: str = "qwen3-coder-flash"
    model_coder_expert: str = "qwen3-coder-plus"
    model_translation_fast: str = "qwen-mt-flash"
    model_translation_expert: str = "qwen-mt-plus"
```

#### 3.5.2 ModelFactory优化

```python
# app/llm/model_factory.py

class ModelFactory:
    """模型工厂 - 支持配置化模型创建"""
    
    _model_cache = {}
    
    @classmethod
    def get_general_model(cls, is_expert: bool = False, **kwargs):
        """获取通用模型"""
        model_name = (
            settings.model_general_expert if is_expert 
            else settings.model_general_fast
        )
        return cls.get_model(model_name, **kwargs)
    
    @classmethod
    def get_vision_model(cls, is_ocr: bool = False, **kwargs):
        """获取视觉模型"""
        model_name = (
            settings.model_vision_ocr if is_ocr 
            else settings.model_vision_general
        )
        return cls.get_model(model_name, **kwargs)
    
    @classmethod
    def get_image_model(cls, is_turbo: bool = True, **kwargs):
        """获取图像生成模型"""
        model_name = (
            settings.model_image_fast if is_turbo 
            else settings.model_image_expert
        )
        return cls.get_model(model_name, **kwargs)
    
    @classmethod
    def get_coder_model(cls, is_plus: bool = False, **kwargs):
        """获取编程模型"""
        model_name = (
            settings.model_coder_expert if is_plus 
            else settings.model_coder_fast
        )
        return cls.get_model(model_name, **kwargs)
    
    @classmethod
    def get_translation_model(cls, is_plus: bool = False, **kwargs):
        """获取翻译模型"""
        model_name = (
            settings.model_translation_expert if is_plus 
            else settings.model_translation_fast
        )
        return cls.get_model(model_name, **kwargs)
```

### 3.6 主聊天AgentFactory

```python
# app/agents/agent_factory.py

from typing import Optional
from langchain.agents import create_agent
from langgraph.checkpoint.postgres import PostgresSaver

from app.config import settings
from app.tools import ALL_TOOLS
from app.llm.model_factory import ModelFactory


SYSTEM_PROMPT = """你是一个强大的AI助手，能够帮助用户处理各种任务。

你可以使用以下工具来帮助用户：

1. **search_knowledge_base** - 从本地知识库搜索信息
   - 当用户询问项目文档、技术规范、内部资料时使用
   
2. **web_search** - 联网搜索最新信息
   - 当用户询问新闻、实时信息、公开资料时使用
   
3. **ocr_document** - 识别图片中的文字
   - 当用户上传包含文字的图片时使用
   
4. **understand_image** - 理解图片内容
   - 当用户上传图片并询问图片内容时使用
   
5. **generate_image** - 生成图像
   - 当用户要求生成、绘制、创建图像时使用
   
6. **edit_image** - 编辑图像
   - 当用户要求修改、编辑已有图像时使用
   
7. **code_assist** - 编程协助
   - 当用户需要写代码、调试代码、解释代码时使用
   
8. **translate_text** - 翻译文本
   - 当用户需要翻译内容时使用

请根据用户的需求，合理选择和使用这些工具。如果用户请求不明确，请主动询问以澄清需求。
"""


class AgentFactory:
    """Agent工厂类 - 使用LangChain 1.0+推荐的create_agent"""
    
    _checkpointer: Optional[PostgresSaver] = None
    
    @classmethod
    def get_checkpointer(cls) -> PostgresSaver:
        """获取PostgresSaver单例"""
        if cls._checkpointer is None:
            cls._checkpointer = PostgresSaver.from_conn_string(
                settings.database_url
            )
        return cls._checkpointer
    
    @classmethod
    def create_chat_agent(
        cls,
        is_expert: bool = False,
        enable_thinking: bool = False
    ):
        """创建聊天Agent (LangChain 1.0+ 推荐方式)
        
        使用create_agent创建ReAct模式的Agent，无需AgentExecutor。
        内部基于LangGraph构建，支持持久化、流式输出等特性。
        
        Args:
            is_expert: 是否使用专家模型
            enable_thinking: 是否启用深度思考
            
        Returns:
            Agent实例，可直接调用invoke或stream
        """
        # 1. 获取模型
        model = ModelFactory.get_general_model(
            is_expert=is_expert,
            thinking=enable_thinking
        )
        
        # 2. 获取checkpointer用于对话状态持久化
        checkpointer = cls.get_checkpointer()
        
        # 3. 创建Agent (LangChain 1.0+ 推荐方式)
        # 直接传递工具列表，无需ToolRegistry
        # 传入checkpointer实现对话状态持久化
        # 参考: https://python.langchain.com/docs/how_to/agent/
        agent = create_agent(
            model=model,
            tools=ALL_TOOLS,  # 直接传递工具列表
            system_prompt=SYSTEM_PROMPT,
            checkpointer=checkpointer,  # 传入PostgresSaver
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
```

### 3.7 主聊天服务

```python
# app/services/chat_service.py - 优化版

import json
from typing import List, Optional, AsyncGenerator, Dict, Any

from app.agents.agent_factory import AgentFactory
from app.llm.model_factory import ModelFactory


class ChatService:
    async def process_message(
        self,
        conversation_id: int,
        content: str,
        images: Optional[List[str]] = None,
        files: Optional[List[str]] = None,
        is_expert: bool = False,
        enable_thinking: bool = False
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """处理用户消息 - 支持多模态输入和Agent工具调用
        
        使用LangChain 1.0+的create_agent，通过stream_mode="values"获取流式输出。
        使用PostgresSaver实现对话状态持久化。
        """
        # 1. 处理多模态输入
        context_parts = [content]
        
        if images:
            for img in images:
                vision_model = ModelFactory.get_vision_model()
                image_understanding = await vision_model.aunderstand_image(img)
                context_parts.append(f"[图片内容: {image_understanding}]")
        
        if files:
            for file in files:
                doc_content = await self._extract_document_content(file)
                context_parts.append(f"[文档内容: {doc_content}]")
        
        full_context = "\n\n".join(context_parts)
        
        # 2. 创建Agent
        agent = AgentFactory.create_chat_agent(
            is_expert=is_expert,
            enable_thinking=enable_thinking
        )
        
        # 3. 获取Agent配置（用于对话状态持久化）
        config = AgentFactory.get_agent_config(str(conversation_id))
        
        # 4. 流式执行Agent (LangChain 1.0+ 方式)
        # 参考: https://python.langchain.com/docs/how_to/agent/
        async for event in agent.astream(
            {"messages": [{"role": "user", "content": full_context}]},
            config,  # 传入config实现对话状态持久化
            stream_mode="values"
        ):
            yield self._format_event(event, enable_thinking)
    
    def _format_event(self, event: Dict, include_thinking: bool) -> Dict[str, Any]:
        """格式化Agent事件为前端可消费的格式"""
        messages = event.get("messages", [])
        if not messages:
            return {"type": "unknown", "data": event}
        
        last_message = messages[-1]
        message_type = last_message.get("type", "")
        
        # 处理AI消息
        if message_type == "ai":
            content = last_message.get("content", "")
            
            # 检查是否有思考内容
            thinking_content = None
            if include_thinking:
                thinking_content = last_message.get("thinking_content") or \
                                   last_message.get("reasoning_content")
            
            return {
                "type": "content",
                "data": {
                    "content": content,
                    "thinking_content": thinking_content
                }
            }
        
        # 处理工具调用
        elif message_type == "tool":
            return {
                "type": "tool_call",
                "data": {
                    "name": last_message.get("name"),
                    "content": last_message.get("content")
                }
            }
        
        return {"type": "unknown", "data": event}
    
    async def _extract_document_content(self, file_path: str) -> str:
        """提取文档内容"""
        # 实现...
        return ""


chat_service = ChatService()
```

### 3.8 前端优化方案

#### 3.8.1 思考过程展示组件

```vue
<!-- frontend/src/components/ThinkingProcess.vue -->
<template>
  <div class="thinking-process" v-if="thinkingContent">
    <div class="thinking-header" @click="isExpanded = !isExpanded">
      <el-icon><Cpu /></el-icon>
      <span>思考过程</span>
      <el-icon class="expand-icon" :class="{ 'is-expanded': isExpanded }">
        <ArrowDown />
      </el-icon>
    </div>
    <div v-show="isExpanded" class="thinking-content">
      <pre>{{ thinkingContent }}</pre>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { Cpu, ArrowDown } from '@element-plus/icons-vue'

interface Props {
  thinkingContent: string
}

defineProps<Props>()

const isExpanded = ref(false)
</script>

<style scoped>
.thinking-process {
  margin: 8px 0;
  border: 1px solid #e4e7ed;
  border-radius: 8px;
  background: #f5f7fa;
}

.thinking-header {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 12px;
  cursor: pointer;
  font-size: 13px;
  color: #606266;
}

.thinking-content {
  padding: 12px;
  border-top: 1px solid #e4e7ed;
}

.thinking-content pre {
  margin: 0;
  white-space: pre-wrap;
  font-size: 13px;
  color: #606266;
  line-height: 1.6;
}

.expand-icon {
  margin-left: auto;
  transition: transform 0.3s;
}

.expand-icon.is-expanded {
  transform: rotate(180deg);
}
</style>
```

#### 3.8.2 消息气泡增强

```vue
<!-- ChatMessageBubble.vue - 增强版 -->
<template>
  <div class="message-bubble" :class="messageClass">
    <div class="message-avatar">
      <!-- ... -->
    </div>
    <div class="message-content">
      <div class="message-role">{{ roleLabel }}</div>
      
      <!-- 思考过程展示 -->
      <ThinkingProcess 
        v-if="message.thinking_content" 
        :thinking-content="message.thinking_content" 
      />
      
      <!-- 工具调用展示 -->
      <ToolCallCard
        v-for="(tool, index) in message.tool_calls"
        :key="index"
        :tool="tool"
      />
      
      <!-- 消息内容 -->
      <div class="message-text" v-html="formattedContent"></div>
      
      <!-- 生成的图像展示 -->
      <div v-if="generatedImages.length > 0" class="generated-images">
        <img 
          v-for="(img, idx) in generatedImages" 
          :key="idx"
          :src="img"
          @click="previewImage(img)"
        />
      </div>
      
      <div class="message-footer">
        <!-- ... -->
      </div>
    </div>
  </div>
</template>
```

#### 3.8.3 Chat Store增强

```typescript
// frontend/src/stores/chat.ts - 增强版

export interface ChatMessage {
  id: number
  conversation_id: number
  role: 'user' | 'assistant'
  content: string
  thinking_content?: string  // 思考过程
  tool_calls?: ToolCall[]    // 工具调用记录
  generated_images?: string[] // 生成的图像
  created_at: string
  is_streaming?: boolean
}

export interface ToolCall {
  name: string
  input: any
  output?: any
  status: 'pending' | 'success' | 'error'
}

export const useChatStore = defineStore('chat', () => {
  // ... 现有代码 ...
  
  function handleStreamEvent(event: any, messageId: number) {
    const msgIndex = messages.value.findIndex((m) => m.id === messageId)
    if (msgIndex === -1) return
    
    const msg = messages.value[msgIndex]
    
    switch (event.type) {
      case 'content':
        messages.value[msgIndex] = {
          ...msg,
          content: msg.content + event.data.content,
          thinking_content: event.data.thinking_content || msg.thinking_content
        }
        break
        
      case 'tool_call':
        const toolCalls = msg.tool_calls || []
        toolCalls.push({
          name: event.data.name,
          input: event.data.content,
          status: 'success'
        })
        messages.value[msgIndex] = { ...msg, tool_calls: toolCalls }
        break
    }
  }
  
  // ... 其他方法 ...
})
```

### 3.9 API路由配置

```python
# app/main.py - 路由配置

from fastapi import FastAPI
from app.api.v1 import chat, skills_direct

app = FastAPI()

# 主聊天API（Agent模式）
app.include_router(
    chat.router,
    prefix="/api/v1/chat",
    tags=["chat"]
)

# 专项技能直接触发API（非Agent模式）
app.include_router(
    skills_direct.router,
    prefix="/api/v1/skills/direct",
    tags=["skills-direct"]
)
```

---

## 四、实施步骤

### 阶段一：基础架构重构 (Week 1)

| 任务 | 描述 | 文件 |
|------|------|------|
| 1.1 重构现有工具 | 将rag_tool、web_search_tool等改为@tool装饰器 | `app/tools/*.py` |
| 1.2 创建技能工具 | 将skills改造为@tool装饰器函数 | `app/tools/image_tools.py`等 |
| 1.3 更新__init__ | 导出ALL_TOOLS列表 | `app/tools/__init__.py` |
| 1.4 删除中间件 | 移除SkillMiddleware和loader_tool | 删除相关文件 |

### 阶段二：Agent架构改造 (Week 1-2)

| 任务 | 描述 | 文件 |
|------|------|------|
| 2.1 重构AgentFactory | 使用create_agent，传入PostgresSaver | `app/agents/agent_factory.py` |
| 2.2 优化System Prompt | 编写包含所有工具描述的System Prompt | `app/agents/prompts.py` |
| 2.3 更新模型配置 | 添加模型配置化支持 | `app/config.py` |
| 2.4 优化ModelFactory | 支持配置化模型创建 | `app/llm/model_factory.py` |

### 阶段三：专项技能直接触发 (Week 2)

| 任务 | 描述 | 文件 |
|------|------|------|
| 3.1 创建专项技能API | 实现图像生成/编辑、编程、翻译的直接触发API | `app/api/v1/skills_direct.py` |
| 3.2 创建专项技能服务 | 封装直接调用逻辑 | `app/services/direct_skill_service.py` |
| 3.3 更新路由配置 | 添加专项技能路由 | `app/main.py` |

### 阶段四：前端优化 (Week 2-3)

| 任务 | 描述 | 文件 |
|------|------|------|
| 4.1 创建专项技能页面 | 图像生成、编程、翻译的独立页面 | `frontend/src/views/*.vue` |
| 4.2 创建Skill Store | 管理专项技能的直接调用 | `frontend/src/stores/skill.ts` |
| 4.3 创建思考过程组件 | 实现可展开的思考过程展示 | `frontend/src/components/ThinkingProcess.vue` |
| 4.4 增强消息气泡 | 集成思考过程和工具调用展示 | `frontend/src/components/ChatMessageBubble.vue` |
| 4.5 更新Chat Store | 支持新的流式事件格式 | `frontend/src/stores/chat.ts` |

### 阶段五：测试与优化 (Week 3)

| 任务 | 描述 |
|------|------|
| 5.1 单元测试 | 测试Agent创建、模型工厂、专项技能API |
| 5.2 集成测试 | 测试主聊天Agent触发和专项技能直接触发 |
| 5.3 性能测试 | 测试流式响应性能 |
| 5.4 代码审查 | 确保符合项目规则和最佳实践 |

---

## 五、预期效果

### 5.1 功能效果

| 功能 | 优化前 | 优化后 |
|------|--------|--------|
| 主聊天Agent触发 | 不支持 | Agent自动识别意图并调用工具 |
| 专项技能直接触发 | 不支持 | 支持独立页面直接调用专用模型 |
| 深度思考 | 仅后端支持 | 前后端完整支持，可展示思考过程 |
| 多模态 | 仅图片理解 | 图片+文档完整支持 |
| 模型配置 | 硬编码 | 可配置化 |
| 对话持久化 | 手动管理 | PostgresSaver自动管理 |

### 5.2 性能效果

- **响应延迟**: 流式响应首字节时间 < 500ms
- **并发能力**: 支持100+并发会话
- **内存占用**: 模型实例缓存复用，降低内存占用

### 5.3 代码质量

- **可维护性**: 单一职责原则，模块间低耦合
- **可扩展性**: 新工具添加只需定义@tool函数并加入ALL_TOOLS列表
- **可测试性**: 各模块独立，便于单元测试

---

## 六、验证方法

### 6.1 主聊天Agent触发验证

```bash
# 测试Agent工具调用
curl -X POST http://localhost:8000/api/v1/chat/send \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "conversation_id": 1,
    "content": "生成一张猫咪的图片",
    "model_mode": "fast",
    "stream": true
  }'
```

### 6.2 专项技能直接触发验证

```bash
# 测试图像生成直接触发
curl -X POST http://localhost:8000/api/v1/skills/direct/image/generate \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "prompt": "一只可爱的橘猫",
    "size": "1024*1024",
    "n": 1,
    "model_mode": "fast"
  }'

# 测试编程直接触发
curl -X POST http://localhost:8000/api/v1/skills/direct/code/assist \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "prompt": "写一个快速排序算法",
    "language": "python",
    "model_mode": "expert"
  }'

# 测试翻译直接触发
curl -X POST http://localhost:8000/api/v1/skills/direct/translate \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "text": "Hello, world!",
    "target_lang": "zh",
    "model_mode": "fast"
  }'
```

### 6.3 测试用例

| 用例ID | 场景 | 触发方式 | 预期结果 |
|--------|------|----------|----------|
| TC-001 | 用户请求生成图像 | 主聊天Agent | Agent调用generate_image工具 |
| TC-002 | 用户进入图像生成页面点击生成 | 专项技能直接 | 直接调用QwenImageModel生成图像 |
| TC-003 | 用户请求编程帮助 | 主聊天Agent | Agent调用code_assist工具 |
| TC-004 | 用户进入编程助手页面 | 专项技能直接 | 直接调用QwenCoderModel |
| TC-005 | 用户上传图片询问内容 | 主聊天Agent | Agent调用understand_image工具 |
| TC-006 | 用户询问知识库内容 | 主聊天Agent | Agent调用search_knowledge_base工具 |
| TC-007 | 用户询问实时信息 | 主聊天Agent | Agent调用web_search工具 |
| TC-008 | 专家模式+深度思考 | 主聊天Agent | 返回思考过程+最终答案 |
| TC-009 | 多轮对话上下文 | 主聊天Agent | PostgresSaver正确保存和恢复对话状态 |

---

## 七、LangChain 1.0+ 关键参考

### 7.1 官方文档

- **Agent概念**: https://python.langchain.com/docs/concepts/agents/
- **Agent教程**: https://python.langchain.com/docs/tutorials/agents/
- **How-To指南**: https://python.langchain.com/docs/how_to/agent/

### 7.2 核心API

```python
from langchain.agents import create_agent
from langchain_core.tools import tool
from langgraph.checkpoint.postgres import PostgresSaver

# 1. 定义工具 - 使用@tool装饰器
@tool
def my_tool(query: str) -> str:
    """工具描述."""
    return "result"

# 2. 创建PostgresSaver用于对话状态持久化
checkpointer = PostgresSaver.from_conn_string(
    "postgresql://user:password@localhost:5432/dbname"
)

# 3. 创建Agent (无需AgentExecutor，无需ToolRegistry)
agent = create_agent(
    model="model-name",
    tools=[my_tool],  # 直接传递工具列表
    system_prompt="系统提示词",
    checkpointer=checkpointer,  # 传入PostgresSaver实现对话状态持久化
)

# 4. 调用时传入config指定会话ID
config = {"configurable": {"thread_id": "conversation_123"}}
response = agent.invoke({"messages": [...]}, config)

# 5. 流式调用
for event in agent.stream(
    {"messages": [...]},
    config,
    stream_mode="values"
):
    print(event)
```

### 7.3 关键特性

- 基于LangGraph构建，支持持久化、流式、人机协同
- 无需显式创建AgentExecutor
- 无需复杂的ToolRegistry，工具直接以列表形式传递
- 支持`stream_mode`参数控制流式输出
- 通过`checkpointer`参数传入PostgresSaver实现对话状态持久化
- 调用时通过`config`参数指定`thread_id`区分不同对话线程

---

## 八、风险与应对

| 风险 | 影响 | 应对措施 |
|------|------|----------|
| LangChain 1.0+ API变化 | 高 | 严格遵循官方文档，使用create_agent标准API |
| 工具调用延迟 | 中 | 异步执行，流式返回中间状态 |
| 模型兼容性 | 中 | 通过配置化支持多种模型 |
| 前端兼容性 | 低 | 渐进式升级，保持向后兼容 |
| PostgresSaver配置 | 低 | 使用单例模式管理checkpointer |

---

## 九、总结

本优化方案通过以下核心改进，将DragonAI V2打造成一个真正的AI Agent智能体：

### 9.1 双模式架构

1. **主聊天Agent模式**
   - 用户通过自然语言与Agent交互
   - Agent智能识别意图并调用工具
   - 使用`create_agent` + `PostgresSaver`实现对话持久化

2. **专项技能直接触发模式**
   - 用户点击专项功能入口
   - 直接调用专用模型，不经过Agent
   - 适用于用户明确知道需要什么功能的场景

### 9.2 核心改进

1. **架构升级**: 使用LangChain 1.0+推荐的`create_agent`，无需AgentExecutor和ToolRegistry
2. **对话持久化**: 使用`PostgresSaver`作为`checkpointer`，实现对话状态自动持久化
3. **工具简化**: 所有功能使用`@tool`装饰器定义，直接以列表形式传递给create_agent
4. **双模式支持**: 主聊天Agent触发 + 专项技能直接触发
5. **体验优化**: 深度思考过程展示、工具调用状态可视化
6. **配置灵活**: 模型映射可配置，便于开发者自定义

### 9.3 方案核心要点

- **主聊天**: `create_agent(model, tools, system_prompt, checkpointer=PostgresSaver())`
- **专项技能**: 直接调用`ModelFactory.get_xxx_model()`，不经过Agent
- **对话隔离**: 调用时传入`config={"configurable": {"thread_id": "xxx"}}`
- **工具复用**: 同一套工具函数既可用于Agent调用，也可用于直接调用

优化后的系统将具备更强的智能性、可扩展性和用户体验，完全符合LangChain 1.0+的最佳实践。
