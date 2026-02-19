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
  transition: background-color 0.2s;
}

.thinking-header:hover {
  background-color: #ebeef5;
}

.thinking-content {
  padding: 12px;
  border-top: 1px solid #e4e7ed;
}

.thinking-content pre {
  margin: 0;
  white-space: pre-wrap;
  word-wrap: break-word;
  font-size: 13px;
  color: #606266;
  line-height: 1.6;
  font-family: 'Courier New', monospace;
}

.expand-icon {
  margin-left: auto;
  transition: transform 0.3s;
}

.expand-icon.is-expanded {
  transform: rotate(180deg);
}
</style>
