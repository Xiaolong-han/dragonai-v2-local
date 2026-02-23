<template>
  <div class="tool-list">
    <div class="tool-header">
      <h3>AI 工具</h3>
    </div>
    <div class="tool-grid">
      <div
        v-for="tool in tools"
        :key="tool.name"
        class="tool-card"
        @click="handleToolClick(tool)"
      >
        <div class="tool-icon">
          <el-icon :size="32">
            <component :is="getToolIcon(tool.name)" />
          </el-icon>
        </div>
        <div class="tool-info">
          <h4>{{ tool.name }}</h4>
          <p>{{ tool.description }}</p>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import {
  Picture,
  Edit,
  Document,
  Operation,
  Position,
  Guide,
  Connection
} from '@element-plus/icons-vue'
import request from '@/utils/request'

interface Tool {
  name: string
  description: string
}

const router = useRouter()
const tools = ref<Tool[]>([])
const loading = ref(false)

const toolRoutes: Record<string, string> = {
  '图像生成': '/image-generation',
  '图像编辑': '/image-editing',
  '编程': '/coding',
  '翻译': '/translation'
}

const toolIcons: Record<string, any> = {
  '图像生成': Picture,
  '图像编辑': Edit,
  '编程': Operation,
  '翻译': Guide
}

function getToolIcon(name: string) {
  return toolIcons[name] || Document
}

async function fetchTools() {
  loading.value = true
  try {
    const data = await request.get('/api/v1/tools')
    tools.value = data as Tool[]
  } catch (error) {
    console.error('Failed to fetch tools:', error)
  } finally {
    loading.value = false
  }
}

function handleToolClick(tool: Tool) {
  const route = toolRoutes[tool.name]
  if (route) {
    router.push(route)
  }
}

onMounted(() => {
  fetchTools()
})
</script>

<style scoped>
.tool-list {
  padding: 20px;
}

.tool-header {
  margin-bottom: 20px;
}

.tool-header h3 {
  font-size: 18px;
  font-weight: 600;
  color: #303133;
  margin: 0;
}

.tool-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 16px;
}

.tool-card {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 16px;
  background: white;
  border-radius: 12px;
  border: 1px solid #e4e7ed;
  cursor: pointer;
  transition: all 0.2s;
}

.tool-card:hover {
  border-color: #409eff;
  box-shadow: 0 4px 12px rgba(64, 158, 255, 0.15);
  transform: translateY(-2px);
}

.tool-icon {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 56px;
  height: 56px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-radius: 12px;
  color: white;
  flex-shrink: 0;
}

.tool-info {
  flex: 1;
  min-width: 0;
}

.tool-info h4 {
  font-size: 16px;
  font-weight: 600;
  color: #303133;
  margin: 0 0 4px 0;
}

.tool-info p {
  font-size: 13px;
  color: #909399;
  margin: 0;
  line-height: 1.4;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
</style>
