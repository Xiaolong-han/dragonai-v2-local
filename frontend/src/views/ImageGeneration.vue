<template>
  <div class="skill-page">
    <div class="skill-header">
      <h2>图像生成</h2>
      <p class="skill-desc">使用AI生成高质量图像，支持多种风格和尺寸</p>
    </div>

    <div class="skill-content">
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
            v-for="(url, idx) in result.urls"
            :key="idx"
            class="image-item"
            @click="previewImage(url)"
          >
            <img :src="url" :alt="`生成的图像 ${idx + 1}`" />
            <div class="image-overlay">
              <el-icon><ZoomIn /></el-icon>
            </div>
          </div>
        </div>
        <div class="prompt-display">
          <strong>提示词:</strong> {{ result.prompt }}
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { ElMessage } from 'element-plus'
import { Picture, Lightning, Star, ZoomIn } from '@element-plus/icons-vue'
import { useSkillStore } from '@/stores/skill'

const skillStore = useSkillStore()

const modelMode = ref<'fast' | 'expert'>('fast')
const prompt = ref('')
const size = ref('1024*1024')
const n = ref(1)
const loading = ref(false)
const result = ref<any>(null)

async function generate() {
  if (!prompt.value.trim()) {
    ElMessage.warning('请输入图像描述')
    return
  }

  loading.value = true
  try {
    result.value = await skillStore.directImageGenerate({
      prompt: prompt.value,
      size: size.value,
      n: n.value,
      model_mode: modelMode.value
    })
    ElMessage.success('图像生成成功')
  } catch (error: any) {
    ElMessage.error(error.response?.data?.detail || '图像生成失败')
  } finally {
    loading.value = false
  }
}

function previewImage(url: string) {
  // 实现图片预览
  window.open(url, '_blank')
}
</script>

<style scoped>
.skill-page {
  max-width: 900px;
  margin: 0 auto;
  padding: 24px;
}

.skill-header {
  text-align: center;
  margin-bottom: 32px;
}

.skill-header h2 {
  font-size: 28px;
  font-weight: 600;
  color: #303133;
  margin-bottom: 8px;
}

.skill-desc {
  color: #909399;
  font-size: 14px;
}

.skill-content {
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
