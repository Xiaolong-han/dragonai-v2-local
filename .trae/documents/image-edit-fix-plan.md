# 图像编辑功能问题修复计划

## 一、问题分析报告

### 1.1 错误现象

用户报告了两个相关问题：

1. **Chat对话中图片上传问题**：在chat对话框点击上传图片再发送编辑指令，提示需要提供图片
2. **图像编辑技能页面问题**：在图像编辑技能的专门路径上传图片再输入编辑指令也提示没有提供图片

同时终端日志显示：
```
<400> InternalError.Algo.InvalidParameter: An assistant message with "tool_calls" must be followed by tool messages responding to each "tool_call_id". The following tool_call_ids did not have response messages: message[33].role
```

### 1.2 根本原因分析

经过代码审查，发现存在**三个层面的问题**：

---

#### 问题1：前端图片上传流程不完整

**位置**: [frontend/src/components/ChatInput.vue](file:///e:\project\dragonai-v2-local\frontend\src\components\ChatInput.vue)

**问题描述**:
- `handleUploadImage` 函数只是将文件保存到本地状态 `uploadedFiles`
- `handleSend` 函数直接将本地 File 对象传递给父组件，**没有先上传到服务器**
- 父组件 `Chat.vue` 的 `handleSendMessage` 函数接收了 `files` 参数但**完全忽略**了它

**代码路径**:
```
ChatInput.handleSend() 
  → emit('send', value, [...uploadedFiles.value], ...)
  → Chat.handleSendMessage(content, files, skill, options)
  → chatStore.sendMessage(conversationId, content)  // files 参数丢失！
  → _sendMessageInternal(..., images: undefined, ...)  // images 为 undefined
```

---

#### 问题2：图像编辑API路径格式错误

**位置**: 
- [frontend/src/views/ImageEditing.vue:166-167](file:///e:\project\dragonai-v2-local\frontend\src\views\ImageEditing.vue#L166-L167)
- [app/api/v1/skills.py:155-156](file:///e:\project\dragonai-v2-local\app\api\v1\skills.py#L155-L156)
- [app/llm/qwen_models.py:373-411](file:///e:\project\dragonai-v2-local\app\llm\qwen_models.py#L373-L411)

**问题描述**:
- 前端上传文件后获取 `relative_path`（如 `images/20260220_abc123.jpg`）
- 后端 `aedit_image` 方法直接将 `relative_path` 作为 `image_url` 发送给阿里百炼API
- 阿里百炼API需要的是**完整的HTTP URL**或**Base64编码**，而不是相对路径

**代码路径**:
```
ImageEditing.vue: uploadResponse[0].relative_path = "images/xxx.jpg"
  → POST /api/v1/skills/image-editing { image_path: "images/xxx.jpg" }
  → skills.py: image_url=request.image_path  // "images/xxx.jpg"
  → qwen_models.py: {"image": image_url}  // 发送相对路径给API
  → API返回错误：无法识别图片
```

---

#### 问题3：对话历史中存在未完成的tool_calls

**位置**: [app/agents/agent_factory.py:59-67](file:///e:\project\dragonai-v2-local\app\agents\agent_factory.py#L59-L67)

**问题描述**:
- Agent使用 `InMemorySaver` 保存对话状态
- 当工具调用失败时，assistant消息中的 `tool_calls` 没有对应的响应
- 后续请求加载历史状态时，阿里百炼API拒绝处理包含未完成tool_calls的消息

---

### 1.3 相关文件清单

| 文件 | 问题类型 | 问题描述 |
|------|----------|----------|
| `frontend/src/components/ChatInput.vue` | 前端 | 未上传文件到服务器 |
| `frontend/src/views/Chat.vue` | 前端 | 忽略files参数 |
| `frontend/src/stores/chat.ts` | 前端 | 未处理图片上传 |
| `frontend/src/views/ImageEditing.vue` | 前端 | 使用相对路径而非完整URL |
| `app/api/v1/skills.py` | 后端 | 未转换路径格式 |
| `app/llm/qwen_models.py` | 后端 | 图像编辑API调用方式 |
| `app/agents/agent_factory.py` | 后端 | 对话状态管理 |
| `app/services/chat_service.py` | 后端 | 消息处理逻辑 |

---

## 二、修复方案

### 2.1 方案概述

采用**三层修复策略**：

1. **修复前端图片上传流程**：先上传文件获取URL，再发送消息
2. **修复图像编辑API调用**：将相对路径转换为完整URL
3. **修复对话历史管理**：清理未完成的tool_calls

---

### 2.2 具体修复步骤

#### 步骤1：修复ChatInput组件 - 上传文件后再发送

修改 `frontend/src/components/ChatInput.vue`：

```typescript
async function handleSend() {
  const value = inputValue.value.trim()
  if ((value || uploadedFiles.value.length > 0) && !props.loading && !props.disabled) {
    // 先上传所有文件
    const uploadedUrls: string[] = []
    
    for (const file of uploadedFiles.value) {
      try {
        const formData = new FormData()
        formData.append('file', file.file)
        const response = await request.post('/api/v1/files/upload', formData, {
          headers: { 'Content-Type': 'multipart/form-data' }
        })
        if (response && response[0]) {
          uploadedUrls.push(response[0].relative_path)
        }
      } catch (error) {
        console.error('Failed to upload file:', error)
        ElMessage.error(`文件 ${file.name} 上传失败`)
      }
    }
    
    const options: any = {}
    if (activeSkill.value?.name === 'translation') {
      options.targetLang = targetLang.value
    }
    
    emit('send', 
      value, 
      uploadedUrls,  // 传递上传后的URL列表
      activeSkill.value?.name,
      Object.keys(options).length > 0 ? options : undefined
    )
    
    // 重置状态
    inputValue.value = ''
    uploadedFiles.value.forEach(file => {
      if (file.preview) {
        URL.revokeObjectURL(file.preview)
      }
    })
    uploadedFiles.value = []
  }
}
```

#### 步骤2：修复Chat.vue - 传递图片URL

修改 `frontend/src/views/Chat.vue`：

```typescript
function handleSendMessage(content: string, files: any[], skill?: string, options?: any) {
  if (!currentConversationId.value) return
  
  // files 现在是上传后的URL列表
  const imageUrls = files.filter(url => typeof url === 'string')
  
  if (skill) {
    chatStore.sendMessageWithSkill(currentConversationId.value, content, skill, options, imageUrls)
  } else {
    chatStore.sendMessage(currentConversationId.value, content, imageUrls)
  }
}
```

#### 步骤3：修复图像编辑技能 - 转换路径为完整URL

修改 `frontend/src/views/ImageEditing.vue`：

```typescript
async function editImage() {
  if (!selectedFile.value) {
    ElMessage.warning('请先上传图片')
    return
  }
  if (!prompt.value.trim()) {
    ElMessage.warning('请输入编辑描述')
    return
  }

  loading.value = true
  try {
    // 1. 上传文件
    const formData = new FormData()
    formData.append('file', selectedFile.value)
    const uploadResponse = await request.post('/api/v1/files/upload', formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    })

    // 2. 获取完整的图片URL
    const relativePath = (uploadResponse as any)[0].relative_path
    const baseUrl = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'
    const fullImageUrl = `${baseUrl}/api/v1/files/serve/${relativePath}`

    // 3. 调用图像编辑API
    const data = await request.post('/api/v1/skills/image-editing', {
      image_path: fullImageUrl,  // 使用完整URL
      prompt: prompt.value,
      is_expert: isExpert.value,
      size: size.value
    })
    images.value = data.images
    ElMessage.success('图像编辑成功！')
  } catch (error) {
    console.error('Failed to edit image:', error)
    ElMessage.error('图像编辑失败，请重试')
  } finally {
    loading.value = false
  }
}
```

#### 步骤4：添加文件服务端点

修改 `app/api/v1/files.py`，添加文件服务路由：

```python
from fastapi.responses import FileResponse

@router.get("/serve/{relative_path:path}")
async def serve_file(
    relative_path: str,
    current_user: User = Depends(get_current_active_user),
):
    """提供文件访问服务"""
    file_path = file_storage.get_file_path(relative_path)
    if not file_path:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File not found"
        )
    return FileResponse(
        path=file_path,
        filename=file_path.name
    )
```

#### 步骤5：修复后端图像编辑 - 支持本地路径

修改 `app/llm/qwen_models.py`：

```python
import base64
from pathlib import Path

async def aedit_image(
    self,
    image_url: str,
    prompt: str,
    size: str = "1024*1024",
    negative_prompt: str = None
) -> str:
    """编辑图像（异步）"""
    headers = {
        "Authorization": f"Bearer {self.api_key}",
        "Content-Type": "application/json"
    }
    
    # 处理图片URL：支持本地路径、相对路径和完整URL
    image_content = await self._prepare_image_content(image_url)
    
    data = {
        "model": self.model_name,
        "input": {
            "messages": [
                {
                    "role": "user",
                    "content": [
                        image_content,
                        {"text": prompt}
                    ]
                }
            ]
        },
        "parameters": {"size": size}
    }
    
    if negative_prompt:
        data["parameters"]["negative_prompt"] = negative_prompt
    
    async with httpx.AsyncClient(timeout=120.0) as client:
        response = await client.post(self.base_url, headers=headers, json=data)
        response.raise_for_status()
        result = response.json()
        
        urls = self._parse_image_urls(result)
        return urls[0] if urls else ""

async def _prepare_image_content(self, image_source: str) -> dict:
    """准备图片内容，支持多种格式"""
    # 1. 如果是完整的HTTP URL，直接使用
    if image_source.startswith(('http://', 'https://')):
        return {"image": image_source}
    
    # 2. 如果是Base64数据URI，直接使用
    if image_source.startswith('data:image'):
        return {"image": image_source}
    
    # 3. 尝试作为本地文件路径读取
    from app.storage import file_storage
    
    # 3.1 尝试作为相对路径
    file_path = file_storage.get_file_path(image_source)
    if file_path and file_path.exists():
        return await self._encode_local_file(file_path)
    
    # 3.2 尝试作为绝对路径
    abs_path = Path(image_source)
    if abs_path.exists():
        return await self._encode_local_file(abs_path)
    
    # 4. 无法识别，尝试作为URL使用
    return {"image": image_source}

async def _encode_local_file(self, file_path: Path) -> dict:
    """将本地文件编码为Base64"""
    import mimetypes
    
    mime_type, _ = mimetypes.guess_type(str(file_path))
    if not mime_type:
        mime_type = "image/jpeg"
    
    with open(file_path, "rb") as f:
        image_data = base64.b64encode(f.read()).decode("utf-8")
    
    return {"image": f"data:{mime_type};base64,{image_data}"}
```

#### 步骤6：修复对话历史清理

修改 `app/services/chat_service.py`：

```python
from langchain_core.messages import AIMessage, ToolMessage

@staticmethod
def _clean_incomplete_tool_calls(messages: list) -> list:
    """清理历史消息中未完成的tool_calls
    
    确保每个assistant的tool_calls都有对应的tool响应消息
    """
    if not messages:
        return messages
    
    cleaned = []
    pending_tool_call_ids = set()
    
    for msg in messages:
        msg_type = getattr(msg, 'type', None)
        
        # 收集assistant消息中的tool_call_ids
        if isinstance(msg, AIMessage) or msg_type == 'ai':
            tool_calls = getattr(msg, 'tool_calls', [])
            if tool_calls:
                pending_tool_call_ids = {tc.get('id') for tc in tool_calls if tc.get('id')}
        
        # 检查tool消息是否响应了pending的tool_call
        if isinstance(msg, ToolMessage) or msg_type == 'tool':
            tool_call_id = getattr(msg, 'tool_call_id', None)
            if tool_call_id in pending_tool_call_ids:
                pending_tool_call_ids.discard(tool_call_id)
        
        cleaned.append(msg)
    
    # 如果还有未响应的tool_calls，移除最后一条包含tool_calls的assistant消息
    if pending_tool_call_ids:
        for i in range(len(cleaned) - 1, -1, -1):
            msg = cleaned[i]
            if (isinstance(msg, AIMessage) or getattr(msg, 'type', None) == 'ai') and getattr(msg, 'tool_calls', None):
                logger.warning(f"[CHAT] 移除未完成的tool_call消息: {msg.tool_calls}")
                cleaned.pop(i)
                break
    
    return cleaned
```

---

## 三、验证步骤

### 3.1 功能测试

1. **Chat对话图片上传测试**
   - 在Chat页面点击上传图片
   - 发送包含图片的消息
   - 验证图片正确传递到后端

2. **图像编辑技能页面测试**
   - 在图像编辑页面上传图片
   - 输入编辑指令
   - 验证编辑成功返回结果

3. **Agent工具调用测试**
   - 在Chat中上传图片并请求编辑
   - 验证Agent正确识别意图并调用工具

### 3.2 回归测试

1. 验证其他技能（翻译、编程）正常工作
2. 验证普通对话不受影响
3. 验证文件上传功能正常

---

## 四、风险评估

| 风险 | 影响 | 缓解措施 |
|------|------|----------|
| 前端上传流程变更可能影响用户体验 | 中 | 添加上传进度提示 |
| 本地文件转Base64可能增加内存占用 | 低 | 限制文件大小，使用流式处理 |
| 清理历史可能丢失上下文 | 中 | 仅清理无效的tool_calls，保留有效消息 |

---

## 五、实施计划

### Phase 1: 修复前端图片上传流程
- 修改 `ChatInput.vue` - 添加文件上传逻辑
- 修改 `Chat.vue` - 传递图片URL
- 修改 `chat.ts` - 更新接口定义

### Phase 2: 修复图像编辑API调用
- 修改 `ImageEditing.vue` - 使用完整URL
- 修改 `files.py` - 添加文件服务端点
- 修改 `qwen_models.py` - 支持本地路径

### Phase 3: 修复对话历史管理
- 修改 `chat_service.py` - 添加历史清理逻辑
- 修改 `agent_factory.py` - 添加状态清理方法

### Phase 4: 测试验证
- 功能测试
- 回归测试
- 性能测试

---

## 六、预计修改文件

| 文件 | 修改类型 |
|------|----------|
| `frontend/src/components/ChatInput.vue` | 修改 |
| `frontend/src/views/Chat.vue` | 修改 |
| `frontend/src/stores/chat.ts` | 修改 |
| `frontend/src/views/ImageEditing.vue` | 修改 |
| `app/api/v1/files.py` | 修改 |
| `app/llm/qwen_models.py` | 修改 |
| `app/services/chat_service.py` | 修改 |
| `app/agents/agent_factory.py` | 修改 |
