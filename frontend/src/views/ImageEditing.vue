<template>
  <div class="image-editing-page">
    <div class="page-header">
      <div class="header-content">
        <el-icon class="page-icon" :size="36">
          <Edit />
        </el-icon>
        <div>
          <h1>图像编辑</h1>
          <p>上传图片并描述编辑需求，AI 将为你修改</p>
        </div>
      </div>
    </div>

    <div class="page-content">
      <div class="settings-panel">
        <el-card class="settings-card">
          <template #header>
            <div class="card-header">
              <span>设置</span>
            </div>
          </template>

          <div class="form-item">
            <label>模型选择</label>
            <el-radio-group v-model="isExpert" size="large">
              <el-radio-button :value="false">快速模式</el-radio-button>
              <el-radio-button :value="true">专家模式</el-radio-button>
            </el-radio-group>
          </div>

          <div class="form-item">
            <label>输出尺寸</label>
            <el-select v-model="size" placeholder="选择尺寸" style="width: 100%">
              <el-option label="512 × 512" value="512*512" />
              <el-option label="768 × 768" value="768*768" />
              <el-option label="1024 × 1024" value="1024*1024" />
            </el-select>
          </div>
        </el-card>
      </div>

      <div class="main-panel">
        <div class="upload-section">
          <div class="upload-area" @click="triggerUpload">
            <input
              ref="fileInput"
              type="file"
              accept="image/*"
              @change="handleFileSelect"
              style="display: none"
            />
            <template v-if="!selectedImage">
              <el-icon :size="48" class="upload-icon">
                <UploadFilled />
              </el-icon>
              <p class="upload-text">点击或拖拽上传图片</p>
              <p class="upload-hint">支持 JPG、PNG、WEBP 格式</p>
            </template>
            <template v-else>
              <img :src="selectedImage" alt="预览" class="preview-image" />
              <div class="upload-overlay">
                <el-icon :size="32" class="overlay-icon">
                  <Refresh />
                </el-icon>
                <p>更换图片</p>
              </div>
            </template>
          </div>
        </div>

        <div class="prompt-section">
          <el-input
            v-model="prompt"
            type="textarea"
            :rows="4"
            placeholder="描述你想要的编辑效果..."
            class="prompt-input"
          />
          <el-button
            type="primary"
            size="large"
            :loading="loading"
            :disabled="!selectedImage || !prompt.trim()"
            @click="editImage"
            class="generate-button"
          >
            <el-icon><Promotion /></el-icon>
            开始编辑
          </el-button>
        </div>

        <div class="results-section" v-if="images.length > 0">
          <h3>编辑结果</h3>
          <div class="image-grid">
            <div v-for="(image, index) in images" :key="index" class="image-item">
              <img :src="getImageUrl(image)" :alt="`编辑后的图像 ${index + 1}`" />
              <div class="image-actions">
                <el-button type="primary" size="small" @click="downloadImage(image, index)">
                  <el-icon><Download /></el-icon>
                  下载
                </el-button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { ElMessage } from 'element-plus'
import { Edit, UploadFilled, Refresh, Promotion, Download } from '@element-plus/icons-vue'
import request from '@/utils/request'

const fileInput = ref<HTMLInputElement>()
const selectedImage = ref<string>('')
const selectedFile = ref<File | null>(null)
const prompt = ref('')
const isExpert = ref(false)
const size = ref('1024*1024')
const loading = ref(false)
const images = ref<string[]>([])

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

function triggerUpload() {
  fileInput.value?.click()
}

function handleFileSelect(event: Event) {
  const target = event.target as HTMLInputElement
  const file = target.files?.[0]
  if (file) {
    if (!file.type.startsWith('image/')) {
      ElMessage.error('只能上传图片文件')
      return
    }
    if (file.size > 10 * 1024 * 1024) {
      ElMessage.error('图片大小不能超过 10MB')
      return
    }
    selectedFile.value = file
    selectedImage.value = URL.createObjectURL(file)
  }
}

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
    const formData = new FormData()
    formData.append('files', selectedFile.value)
    const uploadResponse = await request.post('/api/v1/files/upload', formData)

    const relativePath = (uploadResponse as any)[0].relative_path

    const data = await request.post('/api/v1/skills/image-editing', {
      image_path: relativePath,
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

async function downloadImage(imageUrl: string, index: number) {
  try {
    const fullUrl = getImageUrl(imageUrl)
    const response = await fetch(fullUrl)
    const blob = await response.blob()
    const downloadUrl = URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = downloadUrl
    link.download = `edited-image-${index + 1}.png`
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    URL.revokeObjectURL(downloadUrl)
    ElMessage.success('图片下载成功')
  } catch (error) {
    console.error('Download failed:', error)
    ElMessage.error('图片下载失败')
  }
}
</script>

<style scoped>
.image-editing-page {
  min-height: 100vh;
  background: #f5f7fa;
}

.page-header {
  background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
  padding: 40px 32px;
  color: white;
}

.header-content {
  display: flex;
  align-items: center;
  gap: 20px;
  max-width: 1200px;
  margin: 0 auto;
}

.page-icon {
  background: rgba(255, 255, 255, 0.2);
  border-radius: 12px;
  padding: 12px;
}

.page-header h1 {
  margin: 0 0 4px 0;
  font-size: 28px;
  font-weight: 600;
}

.page-header p {
  margin: 0;
  opacity: 0.9;
  font-size: 14px;
}

.page-content {
  display: grid;
  grid-template-columns: 280px 1fr;
  gap: 24px;
  max-width: 1200px;
  margin: 24px auto;
  padding: 0 32px;
}

.settings-panel {
  position: sticky;
  top: 24px;
  height: fit-content;
}

.settings-card {
  border: none;
  border-radius: 12px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.04);
}

.card-header {
  font-weight: 600;
  font-size: 15px;
}

.form-item {
  margin-bottom: 24px;
}

.form-item:last-child {
  margin-bottom: 0;
}

.form-item label {
  display: block;
  font-size: 14px;
  color: #606266;
  margin-bottom: 10px;
  font-weight: 500;
}

.main-panel {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.upload-section {
  background: white;
  border-radius: 12px;
  padding: 24px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.04);
}

.upload-area {
  position: relative;
  width: 100%;
  min-height: 300px;
  border: 2px dashed #dcdfe6;
  border-radius: 12px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.2s;
  overflow: hidden;
}

.upload-area:hover {
  border-color: #409eff;
  background: #f0f9ff;
}

.upload-icon {
  color: #c0c4cc;
  margin-bottom: 12px;
}

.upload-text {
  margin: 0 0 4px 0;
  font-size: 16px;
  color: #606266;
  font-weight: 500;
}

.upload-hint {
  margin: 0;
  font-size: 13px;
  color: #909399;
}

.preview-image {
  width: 100%;
  height: 100%;
  object-fit: contain;
  max-height: 400px;
}

.upload-overlay {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  color: white;
  opacity: 0;
  transition: opacity 0.2s;
}

.upload-area:hover .upload-overlay {
  opacity: 1;
}

.overlay-icon {
  margin-bottom: 8px;
}

.upload-overlay p {
  margin: 0;
  font-size: 14px;
}

.prompt-section {
  background: white;
  border-radius: 12px;
  padding: 24px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.04);
}

.prompt-input :deep(.el-textarea__inner) {
  border-radius: 8px;
  font-size: 15px;
  line-height: 1.6;
  resize: none;
}

.generate-button {
  width: 100%;
  margin-top: 16px;
  height: 44px;
  font-size: 15px;
  font-weight: 500;
  border-radius: 8px;
}

.results-section {
  background: white;
  border-radius: 12px;
  padding: 24px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.04);
}

.results-section h3 {
  margin: 0 0 20px 0;
  font-size: 18px;
  font-weight: 600;
  color: #303133;
}

.image-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(240px, 1fr));
  gap: 16px;
}

.image-item {
  position: relative;
  border-radius: 12px;
  overflow: hidden;
  background: #f5f7fa;
  aspect-ratio: 1;
}

.image-item img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.image-actions {
  position: absolute;
  bottom: 0;
  left: 0;
  right: 0;
  padding: 12px;
  background: linear-gradient(transparent, rgba(0, 0, 0, 0.6));
  opacity: 0;
  transition: opacity 0.2s;
}

.image-item:hover .image-actions {
  opacity: 1;
}

.image-actions .el-button {
  width: 100%;
}
</style>
