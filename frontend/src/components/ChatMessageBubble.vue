<template>
  <div class="message-bubble" :class="{ 'user-message': message.role === 'user', 'assistant-message': message.role === 'assistant' }">
    <div class="message-avatar">
      <el-icon v-if="message.role === 'user'" size="20"><User /></el-icon>
      <el-icon v-else size="20"><ChatDotRound /></el-icon>
    </div>
    <div class="message-content">
      <div class="message-role">{{ message.role === 'user' ? '用户' : '助手' }}</div>
      <div class="message-text" v-html="formattedContent"></div>
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
import { User, ChatDotRound, DocumentCopy, Refresh } from '@element-plus/icons-vue'
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
}>()

const formattedContent = computed(() => {
  return renderMarkdown(props.message.content)
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
</script>

<style scoped>
.message-bubble {
  display: flex;
  gap: 12px;
  margin-bottom: 20px;
  max-width: 85%;
}

.user-message {
  flex-direction: row-reverse;
  margin-left: auto;
}

.assistant-message {
  margin-right: auto;
}

.message-avatar {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.user-message .message-avatar {
  background: #409eff;
  color: white;
}

.assistant-message .message-avatar {
  background: #67c23a;
  color: white;
}

.message-content {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.message-role {
  font-size: 12px;
  color: #909399;
  font-weight: 500;
}

.user-message .message-role {
  text-align: right;
}

.message-text {
  padding: 12px 16px;
  border-radius: 12px;
  line-height: 1.6;
  word-wrap: break-word;
}

.user-message .message-text {
  background: #409eff;
  color: white;
  border-top-right-radius: 4px;
}

.assistant-message .message-text {
  background: white;
  color: #303133;
  border-top-left-radius: 4px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
}

.message-text :deep(p) {
  margin: 0 0 8px 0;
}

.message-text :deep(p:last-child) {
  margin-bottom: 0;
}

.message-text :deep(pre) {
  margin: 8px 0;
  padding: 12px;
  background: #f5f7fa;
  border-radius: 6px;
  overflow-x: auto;
}

.message-text :deep(code) {
  font-family: 'Consolas', 'Monaco', monospace;
  font-size: 14px;
}

.message-text :deep(pre code) {
  background: transparent;
  padding: 0;
}

.assistant-message .message-text :deep(pre) {
  background: #f5f7fa;
}

.message-footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.message-time {
  font-size: 11px;
  color: #c0c4cc;
}

.user-message .message-time {
  text-align: right;
}

.message-actions {
  display: flex;
  gap: 4px;
}
</style>
