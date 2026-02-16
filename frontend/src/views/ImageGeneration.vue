<template>
  <div class="image-generation-page">
    <div class="page-header">
      <div class="header-content">
        <el-icon class="page-icon" :size="36">
          <Picture />
        </el-icon>
        <div>
          <h1>图像生成</h1>
          <p>描述你想要的图像，AI 将为你生成</p>
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
            <label>图像尺寸</label>
            <el-select v-model="size" placeholder="选择尺寸" style="width: 100%">
              <el-option label="512 × 512" value="512*512" />
              <el-option label="768 × 768" value="768*768" />
              <el-option label="1024 × 1024" value="1024*1024" />
              <el-option label="1024 × 768" value="1024*768" />
              <el-option label="768 × 1024" value="768*1024" />
            </el-select>
          </div>

          <div class="form-item">
            <label>生成数量</label>
            <el-slider
              v-model="n"
              :min="1"
              :max="4"
              :marks="{ 1: '1张', 2: '2张', 3: '3张', 4: '4张' }"
              :step="null"
            />
          </div>
        </el-card>
      </div>

      <div class="main-panel">
        <div class="prompt-section">
          <el-input
            v-model="prompt"
            type="textarea"
            :rows="4"
            placeholder="描述你想要的图像..."
            class="prompt-input"
          />
          <el-button
            type="primary"
            size="large"
            :loading="loading"
            :disabled="!prompt.trim()"
            @click="generateImage"
            class="generate-button"
          >
            <el-icon><Promotion /></el-icon>
            生成图像
          </el-button>
        </div>

        <div class="results-section" v-if="images.length > 0">
          <h3>生成结果</h3>
          <div class="image-grid">
            <div v-for="(image, index) in images" :key="index" class="image-item">
              <img :src="image" :alt="`生成的图像 ${index + 1}`" />
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
import { Picture, Promotion, Download } from '@element-plus/icons-vue'
import request from '@/utils/request'

const prompt = ref('')
const isExpert = ref(false)
const size = ref('1024*1024')
const n = ref(1)
const loading = ref(false)
const images = ref<string[]>([])

async function generateImage() {
  if (!prompt.value.trim()) {
    ElMessage.warning('请输入图像描述')
    return
  }

  loading.value = true
  try {
    const data = await request.post('/api/v1/skills/image-generation', {
      prompt: prompt.value,
      is_expert: isExpert.value,
      size: size.value,
      n: n.value
    })
    images.value = data.images
    ElMessage.success('图像生成成功！')
  } catch (error) {
    console.error('Failed to generate image:', error)
    ElMessage.error('图像生成失败，请重试')
  } finally {
    loading.value = false
  }
}

function downloadImage(imageUrl: string, index: number) {
  const link = document.createElement('a')
  link.href = imageUrl
  link.download = `generated-image-${index + 1}.png`
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
}
</script>

<style scoped>
.image-generation-page {
  min-height: 100vh;
  background: #f5f7fa;
}

.page-header {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
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
