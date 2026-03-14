<template>
  <div class="message-content-rendered">
    <template v-for="(part, index) in parsedContent" :key="index">
      <!-- 普通文本 -->
      <span v-if="part.type === 'text'" class="text-part" v-html="renderMarkdown(part.content || '')"></span>
      
      <!-- 工具调用卡片 -->
      <div v-else-if="part.type === 'tool'" class="tool-part">
        <div 
          v-if="part.tool"
          class="tool-call-card"
          :class="{ 'tool-pending': part.tool.status === 'pending', 'tool-success': part.tool.status === 'success' }"
        >
          <div class="tool-header" @click="toggleToolDetails(index)">
            <div class="tool-icon-wrapper">
              <el-icon v-if="part.tool.status === 'pending'" class="tool-icon spinning">
                <Loading />
              </el-icon>
              <el-icon v-else class="tool-icon success">
                <CircleCheck />
              </el-icon>
            </div>
            <div class="tool-info">
              <span class="tool-name">{{ getToolDisplayName(part.tool.name) }}</span>
              <span v-if="part.tool.summary" class="tool-summary">{{ part.tool.summary }}</span>
            </div>
            <el-icon class="toggle-icon" :class="{ expanded: expandedTools[index] }">
              <ArrowDown />
            </el-icon>
          </div>
          
          <!-- 工具详情（可折叠） -->
          <div class="tool-details" v-show="expandedTools[index]">
            <!-- 非图片工具：链接卡片 -->
            <div v-if="part.tool.links && part.tool.links.length > 0" class="tool-links">
              <template v-for="(link, linkIndex) in part.tool.links" :key="linkIndex">
                <!-- 有 URL：显示为链接 -->
                <a v-if="link.url" :href="getFullUrl(link.url)" target="_blank" class="link-card">
                  <div class="link-icon">
                    <el-icon><Link /></el-icon>
                  </div>
                  <div class="link-content">
                    <div class="link-title">{{ link.title || getDomainFromUrl(getFullUrl(link.url)) }}</div>
                    <div class="link-url">{{ getDomainFromUrl(getFullUrl(link.url)) }}</div>
                  </div>
                  <el-icon class="link-arrow"><ArrowRight /></el-icon>
                </a>
                <!-- 无 URL：显示为纯文本 -->
                <div v-else class="link-card plain">
                  <div class="link-icon">
                    <el-icon><Document /></el-icon>
                  </div>
                  <div class="link-content">
                    <div class="link-title">{{ link.title }}</div>
                  </div>
                </div>
              </template>
            </div>
            <!-- 详细内容 -->
            <div v-if="part.tool.details" class="tool-detail-content">
              <!-- 图片工具：格式化显示详情 -->
              <div v-if="isImageTool(part.tool.name)" class="image-details">
                <div v-for="(line, idx) in part.tool.details.split('\n')" :key="idx" class="detail-line">
                  <template v-if="line.startsWith('提示词:') || line.startsWith('编辑指令:')">
                    <span class="detail-label">{{ line.split(':')[0] }}:</span>
                    <span class="detail-value">{{ line.split(':').slice(1).join(':') }}</span>
                  </template>

                  <template v-else-if="line.startsWith('尺寸:')">
                    <span class="detail-label">尺寸:</span>
                    <span class="detail-value">{{ line.split(':')[1] }}</span>
                  </template>
                  <!-- 忽略原图行（不显示） -->
                  <template v-else-if="line.startsWith('原图:')">
                  </template>
                  <template v-else>
                    {{ line }}
                  </template>
                </div>
              </div>
              <!-- 其他工具：完整展示详情 -->
              <pre v-else>{{ truncateDetails(part.tool.details) }}</pre>
            </div>
          </div>
        </div>
        <!-- 找不到工具信息时显示简化占位符 -->
        <div v-else class="tool-call-card tool-unknown">
          <div class="tool-header">
            <div class="tool-icon-wrapper">
              <el-icon class="tool-icon"><CircleCheck /></el-icon>
            </div>
            <div class="tool-info">
              <span class="tool-name">工具调用</span>
              <span class="tool-summary">已执行</span>
            </div>
          </div>
        </div>
      </div>
    </template>
  </div>
</template>

<script setup lang="ts">
import { computed, reactive } from 'vue'
import { ElMessage } from 'element-plus'
import { Loading, CircleCheck, ArrowDown, Link, ArrowRight, Document } from '@element-plus/icons-vue'
import { renderMarkdown } from '@/utils/markdown'
import type { ToolCall } from '@/stores/chat'

interface ContentPart {
  type: 'text' | 'tool'
  content?: string
  tool?: ToolCall
}

interface Props {
  content: string
  toolCalls?: ToolCall[]
}

const props = defineProps<Props>()

const expandedTools = reactive<Record<number, boolean>>({})

const baseUrl = import.meta.env.VITE_API_BASE_URL || ''

function getFullUrl(url: string): string {
  if (!url) return ''
  if (url.startsWith('http://') || url.startsWith('https://')) {
    return url
  }
  if (url.startsWith('/api/')) {
    return `${baseUrl}${url}`
  }
  return `${baseUrl}/api/v1/files/serve/${url}`
}

const toolNameMap: Record<string, string> = {
  'web_search': '网页搜索',
  'search_knowledge_base': '知识库检索',
  'read_file': '读取文件',
  'read_pdf': '读取PDF',
  'read_word': '读取Word',
  'write_file': '写入文件',
  'edit_file': '编辑文件',
  'ls': '列出目录',
  'glob': '文件搜索',
  'grep': '文本搜索',
  'code_assist': '代码助手',
  'generate_image': '图片生成',
  'edit_image': '图片编辑',
  'translate_text': '文本翻译'
}

const parsedContent = computed(() => {
  const parts: ContentPart[] = []
  
  const regex = /\[TOOL_CALL:([^\]]+)\]/g
  let match
  let lastIndex = 0
  
  while ((match = regex.exec(props.content)) !== null) {
    if (match.index > lastIndex) {
      parts.push({
        type: 'text',
        content: props.content.slice(lastIndex, match.index)
      })
    }
    
    const toolCallId = match[1]
    const tool = props.toolCalls?.find(t => t.id === toolCallId)
    
    if (tool) {
      parts.push({
        type: 'tool',
        tool: tool
      })
    } else {
      parts.push({
        type: 'text',
        content: match[0]
      })
    }
    
    lastIndex = match.index + match[0].length
  }
  
  if (lastIndex < props.content.length) {
    parts.push({
      type: 'text',
      content: props.content.slice(lastIndex)
    })
  }
  
  if (parts.length === 0) {
    parts.push({
      type: 'text',
      content: props.content
    })
  }
  
  return parts
})

function toggleToolDetails(index: number) {
  expandedTools[index] = !expandedTools[index]
}

function getToolDisplayName(name: string): string {
  return toolNameMap[name] || name
}

function getDomainFromUrl(url: string): string {
  try {
    const urlObj = new URL(url)
    return urlObj.hostname.replace(/^www\./, '')
  } catch {
    return url
  }
}

function truncateDetails(details: string, maxLength: number = 500): string {
  if (details.length <= maxLength) {
    return details
  }
  return details.substring(0, maxLength) + '...'
}

function extractUrl(details: string): string | null {
  // 从详情中提取 URL
  const urlMatch = details.match(/https?:\/\/[^\s]+/)
  return urlMatch ? urlMatch[0] : null
}

function isImageTool(name: string): boolean {
  return name === 'generate_image' || name === 'edit_image'
}

function previewImage(url: string) {
  window.open(url, '_blank')
}
</script>

<style scoped>
.message-content-rendered {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.text-part {
  display: block;
}

.tool-part {
  margin: 8px 0;
}

.tool-call-card {
  border-radius: 12px;
  overflow: hidden;
  border: 1px solid;
  background: rgba(255, 255, 255, 0.03);
  backdrop-filter: blur(10px);
  transition: all 0.3s ease;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.tool-call-card:hover {
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.15);
  transform: translateY(-1px);
}

.tool-pending {
  border-color: rgba(24, 144, 255, 0.4);
  background: linear-gradient(135deg, rgba(24, 144, 255, 0.05) 0%, rgba(24, 144, 255, 0.02) 100%);
}

.tool-success {
  border-color: rgba(82, 196, 26, 0.4);
  background: linear-gradient(135deg, rgba(82, 196, 26, 0.05) 0%, rgba(82, 196, 26, 0.02) 100%);
}

.tool-unknown {
  border-color: rgba(150, 150, 150, 0.3);
  background: linear-gradient(135deg, rgba(150, 150, 150, 0.05) 0%, rgba(150, 150, 150, 0.02) 100%);
}

.tool-unknown .tool-icon-wrapper {
  background: rgba(150, 150, 150, 0.15);
}

.tool-unknown .tool-icon {
  color: #909399;
}

.tool-header {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 10px 14px;
  cursor: pointer;
  user-select: none;
  transition: all 0.2s ease;
}

.tool-header:hover {
  background: rgba(255, 255, 255, 0.05);
}

.tool-icon-wrapper {
  width: 28px;
  height: 28px;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.tool-pending .tool-icon-wrapper {
  background: rgba(24, 144, 255, 0.15);
}

.tool-success .tool-icon-wrapper {
  background: rgba(82, 196, 26, 0.15);
}

.tool-icon {
  font-size: 16px;
}

.tool-pending .tool-icon {
  color: #1890ff;
}

.tool-success .tool-icon {
  color: #52c41a;
}

.spinning {
  animation: spin 1s linear infinite;
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

.tool-info {
  display: flex;
  flex-direction: column;
  gap: 2px;
  flex: 1;
  min-width: 0;
}

.tool-name {
  font-weight: 600;
  font-size: 13px;
  color: var(--text-primary);
}

.tool-summary {
  font-size: 12px;
  color: var(--text-secondary);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.toggle-icon {
  font-size: 14px;
  color: var(--text-tertiary);
  transition: all 0.3s ease;
  flex-shrink: 0;
}

.toggle-icon.expanded {
  transform: rotate(180deg);
}

.tool-details {
  padding: 12px 14px;
  border-top: 1px solid rgba(255, 255, 255, 0.1);
  animation: slideDown 0.3s ease;
}

@keyframes slideDown {
  from {
    opacity: 0;
    transform: translateY(-10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.tool-links {
  display: flex;
  flex-direction: column;
  gap: 8px;
  margin-bottom: 12px;
}

.link-card {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 10px 12px;
  background: rgba(255, 255, 255, 0.05);
  border-radius: 10px;
  border: 1px solid rgba(255, 255, 255, 0.1);
  text-decoration: none;
  transition: all 0.2s ease;
}

.link-card:hover {
  background: rgba(255, 255, 255, 0.1);
  border-color: rgba(24, 144, 255, 0.3);
  transform: translateX(4px);
}

.link-icon {
  width: 36px;
  height: 36px;
  border-radius: 10px;
  background: rgba(24, 144, 255, 0.15);
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.link-icon .el-icon {
  font-size: 18px;
  color: #1890ff;
}

.link-content {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.link-title {
  font-size: 13px;
  font-weight: 500;
  color: var(--text-primary);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.link-url {
  font-size: 11px;
  color: var(--text-tertiary);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.link-arrow {
  font-size: 14px;
  color: var(--text-tertiary);
  flex-shrink: 0;
}

.link-card:hover .link-arrow {
  color: #1890ff;
  transform: translateX(2px);
}

.link-card.plain {
  cursor: default;
}

.link-card.plain:hover {
  background: rgba(255, 255, 255, 0.05);
  transform: none;
}

.tool-detail-content {
  margin-top: 8px;
}

.tool-detail-content pre {
  margin: 0;
  padding: 12px;
  background: rgba(0, 0, 0, 0.2);
  border-radius: 8px;
  font-size: 12px;
  color: var(--text-secondary);
  white-space: pre-wrap;
  word-break: break-word;
  max-height: 200px;
  overflow-y: auto;
  line-height: 1.5;
}

.tool-detail-content pre::-webkit-scrollbar {
  width: 6px;
}

.tool-detail-content pre::-webkit-scrollbar-track {
  background: transparent;
}

.tool-detail-content pre::-webkit-scrollbar-thumb {
  background: rgba(255, 255, 255, 0.2);
  border-radius: 3px;
}

.tool-detail-content pre::-webkit-scrollbar-thumb:hover {
  background: rgba(255, 255, 255, 0.3);
}

.tool-image-wrapper {
  position: relative;
  display: inline-block;
  border-radius: 8px;
  overflow: hidden;
}

.tool-image {
  max-width: 100%;
  max-height: 200px;
  border-radius: 8px;
  display: block;
  object-fit: contain;
}

.tool-image-overlay {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 12px;
  opacity: 0;
  transition: opacity 0.3s ease;
}

.tool-image-wrapper:hover .tool-image-overlay {
  opacity: 1;
}

.image-action-btn {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  border: none;
  background: rgba(255, 255, 255, 0.9);
  color: #333;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s ease;
}

.image-action-btn:hover {
  background: #fff;
  transform: scale(1.1);
}

/* 原图链接样式 */
.image-source-row {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 10px 12px;
  background: rgba(255, 255, 255, 0.05);
  border-radius: 8px;
  border: 1px solid rgba(255, 255, 255, 0.1);
}

.source-label {
  font-size: 12px;
  color: var(--text-secondary);
  font-weight: 500;
}

.source-link {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 13px;
  color: #1890ff;
  text-decoration: none;
  transition: all 0.2s ease;
}

.source-link:hover {
  color: #40a9ff;
  transform: translateX(2px);
}

.source-link .el-icon {
  font-size: 12px;
}

/* 图片详情样式 */
.image-details {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.detail-line {
  display: flex;
  align-items: flex-start;
  gap: 8px;
  flex-wrap: wrap;
}

.detail-label {
  font-weight: 500;
  color: var(--text-secondary);
  flex-shrink: 0;
  font-size: 13px;
}

.detail-value {
  color: var(--text-primary);
  flex: 1;
  word-break: break-word;
  font-size: 13px;
  line-height: 1.5;
}
</style>
