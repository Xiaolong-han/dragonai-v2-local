<template>
  <div class="chat-input-wrapper">
    <div class="chat-input-card" :class="{ 'tool-mode': activeTool }">
      <!-- 工具模式指示器 -->
      <div v-if="activeTool" class="tool-indicator">
        <div class="tool-tag">
          <el-icon :size="16"><component :is="activeTool.icon" /></el-icon>
          <span>{{ activeTool.label }}</span>
          <el-icon class="close-icon" :size="14" @click="clearTool"><Close /></el-icon>
        </div>
        <div v-if="activeTool.name === 'translation'" class="tool-options">
          <span>翻译为</span>
          <el-select v-model="targetLang" size="small" style="width: 100px">
            <el-option label="中文" value="zh" />
            <el-option label="English" value="en" />
            <el-option label="日本語" value="ja" />
            <el-option label="한국어" value="ko" />
          </el-select>
        </div>
      </div>

      <!-- 附件预览区域 -->
      <div class="attachments-area" v-if="uploadedFiles.length > 0">
        <div
          v-for="file in uploadedFiles"
          :key="file.id"
          class="attachment-chip"
        >
          <div class="attachment-preview">
            <img v-if="file.type.startsWith('image/')" :src="file.preview" alt="" />
            <el-icon v-else :size="20"><Document /></el-icon>
          </div>
          <span class="attachment-name">{{ file.name }}</span>
          <el-button
            type="danger"
            :icon="Close"
            circle
            size="small"
            class="attachment-close"
            @click="removeFile(file.id)"
          />
        </div>
      </div>

      <!-- 输入区域 -->
      <div class="input-area">
        <el-input
          ref="inputRef"
          v-model="inputValue"
          type="textarea"
          :rows="1"
          :autosize="{ minRows: 1, maxRows: 8 }"
          :placeholder="currentPlaceholder"
          :disabled="disabled"
          @keydown="handleKeydown"
          @input="handleInput"
          class="message-textarea"
        />
        
        <!-- 工具选择下拉菜单 -->
        <div v-if="showToolMenu" class="tool-menu">
          <div class="tool-menu-header">选择工具</div>
          <div
            v-for="tool in tools"
            :key="tool.name"
            class="tool-menu-item"
            :class="{ active: activeTool?.name === tool.name }"
            @click="selectTool(tool)"
          >
            <el-icon :size="18"><component :is="tool.icon" /></el-icon>
            <span>{{ tool.label }}</span>
          </div>
        </div>
      </div>

      <!-- 底部工具栏 -->
      <div class="input-toolbar">
        <div class="toolbar-left">
          <!-- 上传按钮 -->
          <el-upload
            ref="uploadRef"
            class="upload-btn"
            :show-file-list="false"
            :before-upload="handleBeforeUpload"
            :http-request="handleUpload"
            accept="image/*,.pdf,.doc,.docx,.txt,.md"
          >
            <div class="tool-item" title="上传文件">
              <el-icon :size="18"><Paperclip /></el-icon>
            </div>
          </el-upload>

          <div class="divider"></div>

          <!-- 模型选择按钮 -->
          <el-dropdown trigger="click" @command="selectModel">
            <div class="tool-item model-select" :class="{ 'is-expert': isExpert }" title="选择模型">
              <el-icon :size="18"><Cpu /></el-icon>
              <span>{{ isExpert ? '专家模型' : '快速模型' }}</span>
            </div>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item command="fast" :class="{ 'is-active': !isExpert }">
                  <el-icon :size="16"><Promotion /></el-icon>
                  <span>快速模型</span>
                </el-dropdown-item>
                <el-dropdown-item command="expert" :class="{ 'is-active': isExpert }">
                  <el-icon :size="16"><Medal /></el-icon>
                  <span>专家模型</span>
                </el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>

          <!-- 深度思考按钮 -->
          <div 
            class="tool-item thinking-toggle" 
            :class="{ active: enableThinking }" 
            :title="enableThinking ? '关闭深度思考' : '开启深度思考'"
            @click="toggleThinking"
          >
            <el-icon :size="18"><MagicStick /></el-icon>
            <span>深度思考</span>
          </div>

          <div class="divider"></div>

          <!-- 工具按钮 -->
          <div
            v-for="tool in visibleTools"
            :key="tool.name"
            class="tool-item"
            :class="{ active: activeTool?.name === tool.name }"
            @click="selectTool(tool)"
            :title="tool.label"
          >
            <el-icon :size="18"><component :is="tool.icon" /></el-icon>
            <span>{{ tool.label }}</span>
          </div>

          <!-- 更多工具 -->
          <el-dropdown v-if="moreTools.length > 0" trigger="click" @command="selectTool">
            <div class="tool-item" title="更多工具">
              <el-icon :size="18"><More /></el-icon>
              <span>更多</span>
            </div>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item
                  v-for="tool in moreTools"
                  :key="tool.name"
                  :command="tool"
                >
                  <el-icon :size="16"><component :is="tool.icon" /></el-icon>
                  <span>{{ tool.label }}</span>
                </el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
        </div>

        <div class="toolbar-right">
          <el-button
            type="primary"
            :icon="Promotion"
            :loading="loading"
            :disabled="disabled || (!inputValue.trim() && uploadedFiles.length === 0)"
            @click="handleSend"
            class="send-btn"
            size="small"
          >
            发送
          </el-button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, nextTick } from 'vue'
import { 
  Promotion, 
  Paperclip, 
  Close, 
  Document, 
  More,
  Brush,
  Edit,
  Cpu,
  Guide,
  MagicStick,
  Medal
} from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import request from '@/utils/request'

interface UploadedFile {
  id: string
  file: File
  name: string
  type: string
  size: number
  preview: string
  url?: string
}

interface Tool {
  name: string
  label: string
  icon: any
  placeholder: string
}

interface Props {
  loading?: boolean
  disabled?: boolean
}

interface Emits {
  (e: 'send', value: string, files: string[], tool?: string, options?: any, settings?: { isExpert: boolean; enableThinking: boolean }): void
}

const props = withDefaults(defineProps<Props>(), {
  loading: false,
  disabled: false
})

const emit = defineEmits<Emits>()

const isExpert = ref(false)
const enableThinking = ref(false)

// 工具列表（根据后端实际支持的功能）
const tools: Tool[] = [
  {
    name: 'image_generation',
    label: '图像生成',
    icon: Brush,
    placeholder: '描述你想要生成的图像...'
  },
  {
    name: 'image_editing',
    label: '图像编辑',
    icon: Edit,
    placeholder: '描述你想要对图像进行的编辑...'
  },
  {
    name: 'coding',
    label: '编程',
    icon: Cpu,
    placeholder: '描述你的编程需求...'
  },
  {
    name: 'translation',
    label: '翻译',
    icon: Guide,
    placeholder: '输入要翻译的文本...'
  }
]

// 可见工具（显示在工具栏）
const visibleTools = computed(() => tools.slice(0, 3))
// 更多工具（在 dropdown 中）
const moreTools = computed(() => tools.slice(3))

const inputValue = ref<string>('')
const uploadedFiles = ref<UploadedFile[]>([])
const uploadRef = ref()
const inputRef = ref()
const activeTool = ref<Tool | null>(null)
const showToolMenu = ref(false)
const targetLang = ref('zh')

// 动态占位符
const currentPlaceholder = computed(() => {
  if (activeTool.value) {
    return activeTool.value.placeholder
  }
  return '发消息或输入 "/" 选择工具'
})

function generateId(): string {
  return Date.now().toString(36) + Math.random().toString(36).substr(2)
}

function formatFileSize(bytes: number): string {
  if (bytes === 0) return '0 B'
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i]
}

// 处理输入
function handleInput(value: string) {
  // 检测是否输入了 "/"
  if (value === '/') {
    showToolMenu.value = true
  } else if (!value.startsWith('/')) {
    showToolMenu.value = false
  }
}

// 选择工具
function selectTool(tool: Tool) {
  activeTool.value = tool
  showToolMenu.value = false
  
  // 清除输入框中的 "/"
  if (inputValue.value === '/') {
    inputValue.value = ''
  }
  
  // 聚焦输入框
  nextTick(() => {
    inputRef.value?.focus()
  })
}

// 清除工具
function clearTool() {
  activeTool.value = null
  targetLang.value = 'zh'
}

// 选择模型
function selectModel(model: string) {
  isExpert.value = model === 'expert'
}

// 切换深度思考
function toggleThinking() {
  enableThinking.value = !enableThinking.value
}

function handleBeforeUpload(file: File): boolean {
  const isImage = file.type.startsWith('image/')
  const allowedTypes = ['.pdf', '.doc', '.docx', '.txt', '.md']
  const fileName = file.name.toLowerCase()
  const isValidDoc = allowedTypes.some(type => fileName.endsWith(type))

  if (!isImage && !isValidDoc) {
    ElMessage.error('只能上传图片、PDF、Word、TXT 或 Markdown 文件！')
    return false
  }

  const maxSize = isImage ? 10 : 50
  if (file.size / 1024 / 1024 > maxSize) {
    ElMessage.error(`${isImage ? '图片' : '文件'}大小不能超过 ${maxSize}MB！`)
    return false
  }

  return true
}

async function handleUpload(options: any) {
  const file = options.file
  const isImage = file.type.startsWith('image/')
  const uploadedFile: UploadedFile = {
    id: generateId(),
    file,
    name: file.name,
    type: file.type,
    size: file.size,
    preview: isImage ? URL.createObjectURL(file) : ''
  }
  uploadedFiles.value.push(uploadedFile)
}

function removeFile(id: string) {
  const index = uploadedFiles.value.findIndex(f => f.id === id)
  if (index > -1) {
    const file = uploadedFiles.value[index]
    if (file.preview) {
      URL.revokeObjectURL(file.preview)
    }
    uploadedFiles.value.splice(index, 1)
  }
}

async function handleSend() {
  const value = inputValue.value.trim()
  if ((value || uploadedFiles.value.length > 0) && !props.loading && !props.disabled) {
    const options: any = {}
    
    if (activeTool.value?.name === 'translation') {
      options.targetLang = targetLang.value
    }
    
    const uploadedUrls: string[] = []
    const uploadPromises: Promise<void>[] = []
    
    for (const file of uploadedFiles.value) {
      const uploadPromise = (async () => {
        try {
          const formData = new FormData()
          formData.append('files', file.file)
          const response = await request.post('/api/v1/files/upload', formData)
          if (response && (response as any)[0]) {
            uploadedUrls.push((response as any)[0].relative_path)
          }
        } catch (error) {
          console.error('Failed to upload file:', error)
          ElMessage.error(`文件 ${file.name} 上传失败`)
        }
      })()
      uploadPromises.push(uploadPromise)
    }
    
    await Promise.all(uploadPromises)
    
    emit('send', 
      value, 
      uploadedUrls, 
      activeTool.value?.name,
      Object.keys(options).length > 0 ? options : undefined,
      { isExpert: isExpert.value, enableThinking: enableThinking.value }
    )
    
    inputValue.value = ''
    uploadedFiles.value.forEach(file => {
      if (file.preview) {
        URL.revokeObjectURL(file.preview)
      }
    })
    uploadedFiles.value = []
  }
}

function handleKeydown(event: KeyboardEvent) {
  if (event.key === 'Enter' && !event.shiftKey) {
    event.preventDefault()
    handleSend()
  }
  
  // ESC 关闭工具菜单
  if (event.key === 'Escape') {
    showToolMenu.value = false
  }
}
</script>

<style scoped>
.chat-input-wrapper {
  padding: 16px 24px 24px;
  background: transparent;
  max-width: 900px;
  margin: 0 auto;
  width: 100%;
}

.chat-input-card {
  background: var(--bg-primary);
  border-radius: 16px;
  border: 1px solid var(--border-color);
  box-shadow: var(--shadow-md);
  overflow: visible;
  transition: all 0.3s ease;
  position: relative;
}

.chat-input-card:focus-within {
  border-color: var(--primary-color);
  box-shadow: 0 4px 20px rgba(45, 125, 255, 0.2);
}

.chat-input-card.tool-mode {
  border-color: var(--primary-color);
  background: var(--bg-secondary);
}

/* 工具指示器 */
.tool-indicator {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 10px 16px 0;
  flex-wrap: wrap;
}

.tool-tag {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 4px 10px;
  background: var(--primary-light-bg, rgba(45, 125, 255, 0.1));
  border: 1px solid var(--primary-light-border, rgba(45, 125, 255, 0.2));
  border-radius: 6px;
  font-size: 13px;
  color: var(--primary-color);
  font-weight: 500;
}

.tool-tag .close-icon {
  cursor: pointer;
  margin-left: 4px;
  opacity: 0.7;
  transition: opacity 0.2s;
}

.tool-tag .close-icon:hover {
  opacity: 1;
}

.tool-options {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 13px;
  color: var(--text-secondary);
}

/* 附件区域 */
.attachments-area {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  padding: 10px 16px 0;
}

.attachment-chip {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 6px 10px;
  background: var(--bg-secondary);
  border-radius: 8px;
  border: 1px solid var(--border-color);
  font-size: 13px;
}

.attachment-preview {
  width: 24px;
  height: 24px;
  border-radius: 4px;
  overflow: hidden;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--bg-primary);
  flex-shrink: 0;
}

.attachment-preview img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.attachment-name {
  color: #606266;
  max-width: 120px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.attachment-close {
  margin-left: 4px;
}

/* 输入区域 */
.input-area {
  padding: 12px 16px;
  position: relative;
}

.message-textarea :deep(.el-textarea__inner) {
  border: none;
  resize: none;
  font-size: 15px;
  line-height: 1.6;
  padding: 0;
  min-height: 24px !important;
  background: transparent;
  box-shadow: none;
}

.message-textarea :deep(.el-textarea__inner:focus) {
  box-shadow: none;
}

.message-textarea :deep(.el-textarea__inner::placeholder) {
  color: var(--text-tertiary);
}

/* 工具选择菜单 */
.tool-menu {
  position: absolute;
  bottom: 100%;
  left: 16px;
  margin-bottom: 8px;
  background: var(--bg-primary);
  border-radius: 12px;
  border: 1px solid var(--border-color);
  box-shadow: var(--shadow-md);
  min-width: 180px;
  max-height: 280px;
  overflow-y: auto;
  z-index: 1000;
}

.tool-menu-header {
  padding: 12px 16px;
  font-size: 13px;
  color: var(--text-tertiary);
  border-bottom: 1px solid var(--border-light);
  font-weight: 500;
}

.tool-menu-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 16px;
  cursor: pointer;
  font-size: 14px;
  color: var(--text-primary);
  transition: all 0.2s;
}

.tool-menu-item:hover {
  background: var(--bg-secondary);
}

.tool-menu-item.active {
  background: var(--primary-light-bg, rgba(45, 125, 255, 0.1));
  color: var(--primary-color);
}

/* 底部工具栏 */
.input-toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 8px 12px 12px;
  border-top: 1px solid var(--border-light);
}

.toolbar-left {
  display: flex;
  align-items: center;
  gap: 2px;
}

.toolbar-right {
  display: flex;
  align-items: center;
}

.tool-item {
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 6px 10px;
  border-radius: 8px;
  cursor: pointer;
  font-size: 13px;
  color: var(--text-secondary);
  transition: all 0.2s ease;
}

.tool-item:hover {
  background: var(--bg-secondary);
  color: var(--primary-color);
}

.tool-item.active {
  background: var(--primary-light-bg, rgba(45, 125, 255, 0.1));
  color: var(--primary-color);
}

.tool-item.model-select.is-expert {
  background: var(--danger-light-bg, rgba(245, 108, 108, 0.1));
  color: var(--danger-color, #f56c6c);
  border: 1px solid var(--danger-light-border, rgba(245, 108, 108, 0.2));
}

.tool-item.thinking-toggle.active {
  background: var(--success-light-bg, rgba(103, 194, 58, 0.1));
  color: var(--success-color, #67c23a);
  border: 1px solid var(--success-light-border, rgba(103, 194, 58, 0.2));
}

.tool-item.model-select:hover,
.tool-item.thinking-toggle:hover {
  background: var(--bg-secondary);
}

.tool-item.model-select.is-expert:hover {
  background: var(--danger-light-bg, rgba(245, 108, 108, 0.1));
}

.tool-item.thinking-toggle.active:hover {
  background: var(--success-light-bg, rgba(103, 194, 58, 0.1));
}

.upload-btn {
  display: inline-flex;
}

.upload-btn :deep(.el-upload) {
  display: inline-flex;
}

.divider {
  width: 1px;
  height: 16px;
  background: var(--border-color);
  margin: 0 4px;
}

.send-btn {
  border-radius: 8px;
  padding: 0 16px;
  height: 32px;
  font-weight: 500;
}

/* 滚动条样式 */
.tool-menu::-webkit-scrollbar {
  width: 6px;
}

.tool-menu::-webkit-scrollbar-track {
  background: transparent;
}

.tool-menu::-webkit-scrollbar-thumb {
  background: #c0c4cc;
  border-radius: 3px;
}
</style>
