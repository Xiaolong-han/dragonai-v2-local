<template>
  <div class="tool-call-card">
    <div class="tool-header">
      <el-icon><Tools /></el-icon>
      <span class="tool-name">{{ tool.name }}</span>
      <el-tag :type="statusType" size="small" class="tool-status">
        {{ statusText }}
      </el-tag>
    </div>
    <div class="tool-content" v-if="tool.input || tool.output">
      <div v-if="tool.input" class="tool-section">
        <div class="section-label">输入:</div>
        <pre class="section-content">{{ formatContent(tool.input) }}</pre>
      </div>
      <div v-if="tool.output" class="tool-section">
        <div class="section-label">输出:</div>
        <pre class="section-content">{{ formatContent(tool.output) }}</pre>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { Tools } from '@element-plus/icons-vue'

interface ToolCall {
  name: string
  input?: any
  output?: any
  status: 'pending' | 'success' | 'error'
}

interface Props {
  tool: ToolCall
}

const props = defineProps<Props>()

const statusType = computed(() => {
  switch (props.tool.status) {
    case 'pending':
      return 'warning'
    case 'success':
      return 'success'
    case 'error':
      return 'danger'
    default:
      return 'info'
  }
})

const statusText = computed(() => {
  switch (props.tool.status) {
    case 'pending':
      return '执行中'
    case 'success':
      return '已完成'
    case 'error':
      return '失败'
    default:
      return '未知'
  }
})

function formatContent(content: any): string {
  if (typeof content === 'string') {
    return content
  }
  try {
    return JSON.stringify(content, null, 2)
  } catch {
    return String(content)
  }
}
</script>

<style scoped>
.tool-call-card {
  margin: 8px 0;
  border: 1px solid #e4e7ed;
  border-radius: 8px;
  background: #f0f9ff;
  overflow: hidden;
}

.tool-header {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 12px;
  background: #e6f7ff;
  font-size: 13px;
  color: #1890ff;
}

.tool-name {
  font-weight: 500;
}

.tool-status {
  margin-left: auto;
}

.tool-content {
  padding: 12px;
}

.tool-section {
  margin-bottom: 8px;
}

.tool-section:last-child {
  margin-bottom: 0;
}

.section-label {
  font-size: 12px;
  color: #909399;
  margin-bottom: 4px;
}

.section-content {
  margin: 0;
  padding: 8px;
  background: #fff;
  border-radius: 4px;
  font-size: 12px;
  color: #606266;
  white-space: pre-wrap;
  word-wrap: break-word;
  font-family: 'Courier New', monospace;
  max-height: 200px;
  overflow-y: auto;
}
</style>
