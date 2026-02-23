<template>
  <div class="tool-page">
    <div class="tool-header">
      <h2>图像生成</h2>
      <p class="tool-desc">使用AI生成高质量图像，支持多种风格和尺寸</p>
    </div>

    <div class="tool-content">
      <!-- 模型选择 -->
      <div class="model-selector-wrapper">
        <span class="label">模型选择:</span>
        <el-radio-group v-model="modelMode">
          <el-radio-button label="fast">
            <el-icon><Lightning /></el-icon>
            快速模型
          </el-radio-button>
          <el-radio-button label="expert">
            <el-icon><Star /></el-icon>
            专家模型
          </el-radio-button>
        </el-radio-group>
      </div>

      <!-- 输入区域 -->
      <div class="input-section">
        <el-input
          v-model="prompt"
          type="textarea"
          :rows="4"
          placeholder="描述你想要生成的图像，例如：一只可爱的橘猫在阳光下打盹，写实风格，温暖的色调..."
          maxlength="1000"
          show-word-limit
        />

        <div class="options-row">
          <div class="option-item">
            <span class="label">图像尺寸:</span>
            <el-select v-model="size" style="width: 140px">
              <el-option label="1024×1024 (正方形)" value="1024*1024" />
              <el-option label="1024×768 (横屏)" value="1024*768" />
              <el-option label="768×1024 (竖屏)" value="768*1024" />
            </el-select>
          </div>

          <div class="option-item">
            <span class="label">生成数量:</span>
            <el-input-number v-model="n" :min="1" :max="4" />
          </div>
        </div>

        <el-button
          type="primary"
          size="large"
          :loading="loading"
          :disabled="!prompt.trim()"
          @click="generate"
        >
          <el-icon><Picture /></el-icon>
          生成图像
        </el-button>
      </div>

      <!-- 结果展示 -->
      <div v-if="result" class="result-section">
        <h3>生成结果</h3>
        <div class="image-grid">
          <div
            v-for="(url, idx) in result.images"
            :key="idx"
            class="image-item"
          >
            <img :src="getImageUrl(url)" :alt="`生成的图像 ${(idx as number) + 1}`" @click="previewImage(url)" />
            <div class="image-overlay">
              <el-icon @click="previewImage(url)"><ZoomIn /></el-icon>
              <el-icon @click="downloadImage(url, idx as number)"><Download /></el-icon>
            </div>
          </div>
        </div>
        <div class="prompt-display">
          <strong>提示词:</strong> {{ prompt }}
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { Picture, Lightning, Star, ZoomIn, Download } from '@element-plus/icons-vue'
import { useConversationStore } from '@/stores/conversation'
import { useChatStore } from '@/stores/chat'

const conversationStore = useConversationStore()
const chatStore = useChatStore()

const modelMode = ref<'fast' | 'expert'>('fast')
const prompt = ref('')
const size = ref('1024*1024')
const n = ref(1)
const loading = ref(false)
const result = ref<any>(null)

const baseUrl = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'

function getImageUrl(path: string): string {
  if (!path) return ''
  if (path.startsWith('http://') || path.startsWith('https://')) {
    return path
  }
  if (path.startsWith('/api/')) {
    return `${baseUrl}${path}`
  }
  return `${baseUrl}/api/v1/files/serve/${path}`
}

async function generate() {
  if (!prompt.value.trim()) {
    ElMessage.warning('请输入图像描述')
    return
  }

  loading.value = true
  result.value = null
  
  try {
    let conversationId = conversationStore.currentConversationId
    if (!conversationId) {
      const conv = await conversationStore.createConversation({
        title: `图像生成: ${prompt.value.substring(0, 20)}...`
      })
      conversationId = conv.id
    }

    const prefixedContent = `生成图像：${prompt.value}`

    await new Promise<void>((resolve, reject) => {
      const unsubscribe = chatStore.$onAction(({ name, after }) => {
        if (name === 'sendMessage' || name === 'sendMessageWithTool') {
          after(() => {
            const lastMessage = chatStore.messages[chatStore.messages.length - 1]
            if (lastMessage && lastMessage.role === 'assistant' && !lastMessage.is_streaming) {
              const content = lastMessage.content
              const imageUrls: string[] = []
              const regex = /!\[.*?\]\((.*?)\)/g
              let match
              while ((match = regex.exec(content)) !== null) {
                imageUrls.push(match[1])
              }
              
              if (imageUrls.length > 0) {
                result.value = { images: imageUrls }
                ElMessage.success('图像生成成功')
              } else {
                result.value = { images: [], rawContent: content }
              }
              loading.value = false
              unsubscribe()
              resolve()
            }
          })
        }
      })

      chatStore.sendMessage(conversationId!, prefixedContent)

      setTimeout(() => {
        unsubscribe()
        if (loading.value) {
          loading.value = false
          reject(new Error('图像生成超时'))
        }
      }, 120000)
    })
  } catch (error: any) {
    ElMessage.error(error.message || '图像生成失败')
    loading.value = false
  }
}

function previewImage(url: string) {
  window.open(getImageUrl(url), '_blank')
}

async function downloadImage(url: string, index: number) {
  try {
    const imageUrl = getImageUrl(url)
    const response = await fetch(imageUrl)
    const blob = await response.blob()
    const downloadUrl = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = downloadUrl
    a.download = `generated_image_${(index as number) + 1}.png`
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    URL.revokeObjectURL(downloadUrl)
    ElMessage.success('图片下载成功')
  } catch (error) {
    console.error('Download failed:', error)
    ElMessage.error('图片下载失败')
  }
}

onMounted(async () => {
  await conversationStore.fetchConversations()
})
</script>

<style scoped>
.tool-page {
  max-width: 900px;
  margin: 0 auto;
  padding: 24px;
}

.tool-header {
  text-align: center;
  margin-bottom: 32px;
}

.tool-header h2 {
  font-size: 28px;
  font-weight: 600;
  color: #303133;
  margin-bottom: 8px;
}

.tool-desc {
  color: #909399;
  font-size: 14px;
}

.tool-content {
  background: #fff;
  border-radius: 12px;
  padding: 24px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.05);
}

.model-selector-wrapper {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 20px;
}

.label {
  font-size: 14px;
  color: #606266;
  font-weight: 500;
}

.input-section {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.options-row {
  display: flex;
  gap: 24px;
  flex-wrap: wrap;
}

.option-item {
  display: flex;
  align-items: center;
  gap: 8px;
}

.result-section {
  margin-top: 32px;
  padding-top: 24px;
  border-top: 1px solid #e4e7ed;
}

.result-section h3 {
  font-size: 18px;
  font-weight: 600;
  color: #303133;
  margin-bottom: 16px;
}

.image-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
  gap: 16px;
  margin-bottom: 16px;
}

.image-item {
  position: relative;
  aspect-ratio: 1;
  border-radius: 8px;
  overflow: hidden;
  cursor: pointer;
  background: #f5f7fa;
}

.image-item img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  transition: transform 0.3s;
}

.image-item:hover img {
  transform: scale(1.05);
}

.image-overlay {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.3);
  display: flex;
  align-items: center;
  justify-content: center;
  opacity: 0;
  transition: opacity 0.3s;
}

.image-item:hover .image-overlay {
  opacity: 1;
}

.image-overlay .el-icon {
  font-size: 32px;
  color: #fff;
}

.prompt-display {
  padding: 12px;
  background: #f5f7fa;
  border-radius: 8px;
  font-size: 14px;
  color: #606266;
}
</style>
