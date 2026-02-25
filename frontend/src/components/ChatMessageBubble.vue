<template>
  <div class="message-bubble" :class="{ 'user-message': message.role === 'user', 'assistant-message': message.role === 'assistant' }">
    <div class="message-avatar">
      <el-icon v-if="message.role === 'user'" size="24"><User /></el-icon>
      <el-icon v-else size="24"><ChatDotRound /></el-icon>
    </div>
    <div class="message-content">
      <div class="message-role">{{ message.role === 'user' ? '用户' : '助手' }}</div>
      
      <!-- 深度思考内容区域 -->
      <div v-if="message.thinking_content" class="thinking-section">
        <div class="thinking-header" @click="toggleThinking">
          <el-icon :size="14"><Cpu /></el-icon>
          <span>深度思考</span>
          <el-icon :size="14" class="toggle-icon" :class="{ expanded: message.is_thinking_expanded }">
            <ArrowDown />
          </el-icon>
        </div>
        <div class="thinking-content" v-show="message.is_thinking_expanded">
          <div class="thinking-text">{{ message.thinking_content }}</div>
        </div>
      </div>
      
      <div v-if="!isLoading" class="message-text" v-html="formattedContent"></div>
      
      <div v-if="isLoading" class="loading-indicator">
        <div class="loading-dots">
          <span class="dot"></span>
          <span class="dot"></span>
          <span class="dot"></span>
        </div>
        <span class="loading-text">AI 正在思考中...</span>
      </div>
      <div class="message-footer">
        <div class="message-time">{{ formatTime(message.created_at) }}</div>
        <div class="message-actions" v-if="message.role === 'assistant' && !message.is_streaming">
          <el-tooltip content="复制" placement="top">
            <el-button link type="primary" size="small" @click="handleCopy">
              <el-icon><DocumentCopy /></el-icon>
            </el-button>
          </el-tooltip>
          <el-tooltip content="重新生成" placement="top">
            <el-button link type="primary" size="small" @click="handleRegenerate">
              <el-icon><Refresh /></el-icon>
            </el-button>
          </el-tooltip>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { ElMessage } from 'element-plus'
import { User, ChatDotRound, DocumentCopy, Refresh, Cpu, ArrowDown } from '@element-plus/icons-vue'
import { renderMarkdown } from '@/utils/markdown'
import type { ChatMessage } from '@/stores/chat'

interface Props {
  message: ChatMessage
  messageIndex?: number
  conversationId?: number
}

const props = defineProps<Props>()
const emit = defineEmits<{
  copy: []
  regenerate: []
  toggleThinking: []
}>()

const formattedContent = computed(() => {
  return renderMarkdown(props.message.content)
})

const isLoading = computed(() => {
  return props.message.role === 'assistant' && 
         props.message.is_streaming && 
         !props.message.content && 
         !props.message.thinking_content
})

function formatTime(dateString: string): string {
  const date = new Date(dateString)
  return date.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' })
}

async function handleCopy() {
  try {
    await navigator.clipboard.writeText(props.message.content)
    ElMessage.success('已复制到剪贴板')
    emit('copy')
  } catch (error) {
    console.error('复制失败:', error)
    ElMessage.error('复制失败')
  }
}

function handleRegenerate() {
  emit('regenerate')
}

function toggleThinking() {
  emit('toggleThinking')
}
</script>

<style scoped>
.message-bubble {
  display: flex;
  gap: 16px;
  margin-bottom: 24px;
  max-width: 90%;
}

.user-message {
  flex-direction: row-reverse;
  margin-left: auto;
}

.assistant-message {
  margin-right: auto;
}

.message-avatar {
  width: 44px;
  height: 44px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  box-shadow: var(--shadow-sm);
}

.user-message .message-avatar {
  background: var(--primary-color);
  color: white;
}

.assistant-message .message-avatar {
  background: linear-gradient(135deg, var(--primary-color) 0%, var(--primary-dark) 100%);
  color: white;
}

.message-content {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.message-role {
  font-size: 12px;
  color: var(--text-tertiary);
  font-weight: 500;
  padding: 0 4px;
}

.user-message .message-role {
  text-align: right;
}

.message-text {
  padding: 14px 18px;
  border-radius: var(--radius-lg);
  line-height: 1.7;
  word-wrap: break-word;
  font-size: 15px;
}

.user-message .message-text {
  background: var(--bg-tertiary);
  color: var(--text-primary);
  border-bottom-right-radius: var(--radius-sm);
  box-shadow: var(--shadow-sm);
  border: 1px solid var(--border-color);
}

.assistant-message .message-text {
  background: var(--bg-primary);
  color: var(--text-primary);
  border-bottom-left-radius: var(--radius-sm);
  box-shadow: var(--shadow-sm);
  border: 1px solid var(--border-color);
}

.message-text :deep(p) {
  margin: 0 0 12px 0;
}

.message-text :deep(p:last-child) {
  margin-bottom: 0;
}

.message-text :deep(pre) {
  margin: 12px 0;
  padding: 16px;
  background: var(--bg-tertiary);
  border-radius: var(--radius-md);
  overflow-x: auto;
  box-shadow: var(--shadow-sm);
  border: 1px solid var(--border-color);
}

.message-text :deep(code) {
  font-family: 'JetBrains Mono', 'Fira Code', 'Consolas', monospace;
  font-size: 14px;
}

.message-text :deep(pre code) {
  background: transparent;
  padding: 0;
  color: var(--text-primary);
  line-height: 1.6;
}

.assistant-message .message-text :deep(pre) {
  background: var(--bg-tertiary);
}

.user-message .message-text :deep(pre) {
  background: rgba(0, 0, 0, 0.2);
}

.user-message .message-text :deep(pre code) {
  color: #f0f0f0;
}

.message-text :deep(strong) {
  font-weight: 600;
}

.message-text :deep(a) {
  color: var(--primary-color);
  text-decoration: none;
  border-bottom: 1px solid transparent;
  transition: border-color var(--transition-fast);
}

.message-text :deep(a:hover) {
  border-bottom-color: var(--primary-color);
}

.message-text :deep(ul),
.message-text :deep(ol) {
  margin: 8px 0;
  padding-left: 24px;
}

.message-text :deep(li) {
  margin: 4px 0;
}

.message-text :deep(blockquote) {
  margin: 12px 0;
  padding: 10px 16px;
  border-left: 4px solid var(--primary-color);
  background: rgba(45, 125, 255, 0.05);
  border-radius: 0 var(--radius-md) var(--radius-md) 0;
  color: var(--text-secondary);
}

.user-message .message-text :deep(blockquote) {
  border-left-color: rgba(255, 255, 255, 0.4);
  background: rgba(255, 255, 255, 0.1);
  color: rgba(255, 255, 255, 0.9);
}

.message-text :deep(h1),
.message-text :deep(h2),
.message-text :deep(h3),
.message-text :deep(h4) {
  margin: 16px 0 8px 0;
  font-weight: 600;
}

.message-text :deep(h1) {
  font-size: 24px;
}

.message-text :deep(h2) {
  font-size: 20px;
}

.message-text :deep(h3) {
  font-size: 18px;
}

.message-text :deep(h4) {
  font-size: 16px;
}

.message-text :deep(table) {
  width: 100%;
  border-collapse: collapse;
  margin: 12px 0;
  font-size: 14px;
}

.message-text :deep(th),
.message-text :deep(td) {
  padding: 10px 12px;
  border: 1px solid var(--border-color);
  text-align: left;
}

.message-text :deep(th) {
  background: var(--bg-secondary);
  font-weight: 600;
}

.user-message .message-text :deep(th) {
  background: rgba(255, 255, 255, 0.15);
}

.user-message .message-text :deep(th),
.user-message .message-text :deep(td) {
  border-color: rgba(255, 255, 255, 0.2);
}

.message-footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 4px;
}

.message-time {
  font-size: 12px;
  color: var(--text-secondary);
  opacity: 0.8;
}

.user-message .message-time {
  text-align: right;
}

.message-actions {
  display: flex;
  gap: 8px;
}

.message-actions :deep(.el-button) {
  padding: 4px 8px;
  border-radius: var(--radius-sm);
  transition: all var(--transition-normal);
}

.message-actions :deep(.el-button:hover) {
  background: rgba(45, 125, 255, 0.1);
}

.message-text :deep(.image-container) {
  position: relative;
  display: inline-block;
  max-width: 100%;
  margin: 8px 0;
  border-radius: 8px;
  overflow: hidden;
}

.message-text :deep(.image-container img) {
  max-width: 100%;
  max-height: 400px;
  width: auto;
  height: auto;
  border-radius: 8px;
  display: block;
  object-fit: contain;
}

.message-text :deep(.image-overlay) {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.4);
  display: flex;
  align-items: center;
  justify-content: center;
  opacity: 0;
  transition: opacity 0.2s ease;
}

.message-text :deep(.image-container:hover .image-overlay) {
  opacity: 1;
}

.message-text :deep(.download-btn) {
  background: rgba(255, 255, 255, 0.9);
  border: none;
  border-radius: 50%;
  width: 40px;
  height: 40px;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  color: #333;
  transition: all 0.2s ease;
}

.message-text :deep(.download-btn:hover) {
  background: #fff;
  transform: scale(1.1);
}

.thinking-section {
  margin-bottom: 12px;
  border: 1px solid var(--warning-color, #e6a23c);
  border-radius: 8px;
  overflow: hidden;
  background: var(--warning-bg, linear-gradient(135deg, #fdf6ec 0%, #fff7e6 100%));
}

.thinking-header {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 12px;
  background: var(--warning-bg-light, #fdf6ec);
  cursor: pointer;
  font-size: 13px;
  color: var(--warning-color, #e6a23c);
  font-weight: 500;
  user-select: none;
  transition: background 0.2s;
}

.thinking-header:hover {
  background: var(--warning-bg-hover, #faecd8);
}

.thinking-header .toggle-icon {
  margin-left: auto;
  transition: transform 0.3s ease;
}

.thinking-header .toggle-icon.expanded {
  transform: rotate(180deg);
}

.thinking-content {
  padding: 12px;
  background: var(--bg-primary);
  border-top: 1px solid var(--warning-border, #f5dab1);
  max-height: 300px;
  overflow-y: auto;
}

.thinking-text {
  font-size: 13px;
  line-height: 1.7;
  color: var(--text-secondary);
  white-space: pre-wrap;
  word-break: break-word;
}

.thinking-content::-webkit-scrollbar {
  width: 4px;
}

.thinking-content::-webkit-scrollbar-track {
  background: transparent;
}

.thinking-content::-webkit-scrollbar-thumb {
  background: #e6a23c;
  border-radius: 2px;
}

.thinking-content::-webkit-scrollbar-thumb:hover {
  background: #cf9236;
}

.loading-indicator {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 14px 18px;
  background: var(--bg-primary);
  border-radius: var(--radius-lg);
  border: 1px solid var(--border-color);
  box-shadow: var(--shadow-sm);
}

.loading-dots {
  display: flex;
  gap: 4px;
}

.loading-dots .dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: var(--primary-color);
  animation: bounce 1.4s ease-in-out infinite both;
}

.loading-dots .dot:nth-child(1) {
  animation-delay: -0.32s;
}

.loading-dots .dot:nth-child(2) {
  animation-delay: -0.16s;
}

.loading-dots .dot:nth-child(3) {
  animation-delay: 0s;
}

@keyframes bounce {
  0%, 80%, 100% {
    transform: scale(0);
  }
  40% {
    transform: scale(1);
  }
}

.loading-text {
  font-size: 14px;
  color: var(--text-secondary);
  animation: pulse 2s ease-in-out infinite;
}

@keyframes pulse {
  0%, 100% {
    opacity: 0.6;
  }
  50% {
    opacity: 1;
  }
}
</style>
