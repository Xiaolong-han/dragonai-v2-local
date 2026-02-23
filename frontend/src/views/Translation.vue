<template>
  <div class="translation-page">
    <div class="page-header">
      <div class="header-content">
        <el-icon class="page-icon" :size="36">
          <Guide />
        </el-icon>
        <div>
          <h1>翻译助手</h1>
          <p>输入文本，AI 将为你快速翻译</p>
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
        </el-card>
      </div>

      <div class="main-panel">
        <div class="translation-area">
          <div class="language-selector">
            <el-select v-model="sourceLang" placeholder="源语言" style="width: 45%">
              <el-option label="自动检测" :value="null" />
              <el-option label="中文 (zh)" value="zh" />
              <el-option label="英语 (en)" value="en" />
              <el-option label="日语 (ja)" value="ja" />
              <el-option label="韩语 (ko)" value="ko" />
              <el-option label="法语 (fr)" value="fr" />
              <el-option label="德语 (de)" value="de" />
              <el-option label="西班牙语 (es)" value="es" />
              <el-option label="俄语 (ru)" value="ru" />
            </el-select>
            <el-button :icon="Switch" circle @click="swapLanguages" />
            <el-select v-model="targetLang" placeholder="目标语言" style="width: 45%">
              <el-option label="中文 (zh)" value="zh" />
              <el-option label="英语 (en)" value="en" />
              <el-option label="日语 (ja)" value="ja" />
              <el-option label="韩语 (ko)" value="ko" />
              <el-option label="法语 (fr)" value="fr" />
              <el-option label="德语 (de)" value="de" />
              <el-option label="西班牙语 (es)" value="es" />
              <el-option label="俄语 (ru)" value="ru" />
            </el-select>
          </div>

          <div class="text-areas">
            <div class="text-area-wrapper">
              <div class="area-header">
                <span>原文</span>
                <el-button type="primary" link size="small" @click="clearSource" :disabled="!sourceText">
                  清空
                </el-button>
              </div>
              <el-input
                v-model="sourceText"
                type="textarea"
                :rows="8"
                placeholder="请输入要翻译的文本..."
                class="text-input"
              />
            </div>
            <div class="text-area-wrapper">
              <div class="area-header">
                <span>译文</span>
                <div class="actions">
                  <el-button type="primary" link size="small" @click="copyResult" :disabled="!result">
                    <el-icon><DocumentCopy /></el-icon>
                    复制
                  </el-button>
                </div>
              </div>
              <div class="result-area" :class="{ 'has-result': result }">
                <template v-if="loading">
                  <div class="loading-state">
                    <el-icon class="loading-icon" :size="40">
                      <Loading />
                    </el-icon>
                    <p>翻译中...</p>
                  </div>
                </template>
                <template v-else-if="result">
                  <div class="result-text">{{ result }}</div>
                </template>
                <template v-else>
                  <div class="placeholder">翻译结果将显示在这里</div>
                </template>
              </div>
            </div>
          </div>

          <div class="action-bar">
            <el-button
              type="primary"
              size="large"
              :loading="loading"
              :disabled="!sourceText.trim()"
              @click="translate"
              class="translate-button"
            >
              <el-icon><Promotion /></el-icon>
              开始翻译
            </el-button>
          </div>
        </div>

        <div class="model-info" v-if="result && modelName">
          <el-alert
            :title="`使用模型: ${modelName}`"
            type="info"
            :closable="false"
            show-icon
          />
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { ElMessage } from 'element-plus'
import { Guide, Switch, DocumentCopy, Promotion, Loading } from '@element-plus/icons-vue'
import request from '@/utils/request'

const sourceText = ref('')
const sourceLang = ref<string | null>(null)
const targetLang = ref('en')
const isExpert = ref(false)
const loading = ref(false)
const result = ref('')
const modelName = ref('')

function swapLanguages() {
  if (sourceLang.value && targetLang.value) {
    const temp = sourceLang.value
    sourceLang.value = targetLang.value
    targetLang.value = temp
  }
  if (result.value) {
    sourceText.value = result.value
    result.value = ''
    modelName.value = ''
  }
}

function clearSource() {
  sourceText.value = ''
  result.value = ''
  modelName.value = ''
}

async function translate() {
  if (!sourceText.value.trim()) {
    ElMessage.warning('请输入要翻译的文本')
    return
  }

  loading.value = true
  result.value = ''
  modelName.value = ''
  try {
    const data: any = {
      text: sourceText.value,
      target_lang: targetLang.value,
      is_expert: isExpert.value
    }
    if (sourceLang.value) {
      data.source_lang = sourceLang.value
    }
    const response = await request.post('/api/v1/tools/translation', data)
    result.value = response.text
    modelName.value = response.model_name
    ElMessage.success('翻译成功！')
  } catch (error) {
    console.error('Failed to translate:', error)
    ElMessage.error('翻译失败，请重试')
  } finally {
    loading.value = false
  }
}

function copyResult() {
  if (result.value) {
    navigator.clipboard.writeText(result.value).then(() => {
      ElMessage.success('译文已复制到剪贴板')
    }).catch(() => {
      ElMessage.error('复制失败')
    })
  }
}
</script>

<style scoped>
.translation-page {
  min-height: 100vh;
  background: #f5f7fa;
}

.page-header {
  background: linear-gradient(135deg, #fa709a 0%, #fee140 100%);
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

.translation-area {
  background: white;
  border-radius: 12px;
  padding: 24px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.04);
}

.language-selector {
  display: flex;
  align-items: center;
  gap: 16px;
  margin-bottom: 20px;
}

.text-areas {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 20px;
  margin-bottom: 20px;
}

.text-area-wrapper {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.area-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 14px;
  font-weight: 600;
  color: #303133;
}

.text-input :deep(.el-textarea__inner) {
  border-radius: 8px;
  font-size: 15px;
  line-height: 1.8;
  resize: none;
}

.result-area {
  min-height: 200px;
  border: 1px solid #e4e7ed;
  border-radius: 8px;
  padding: 12px;
  display: flex;
  align-items: flex-start;
  justify-content: flex-start;
}

.result-area.has-result {
  background: #fafafa;
}

.placeholder {
  color: #c0c4cc;
  font-size: 14px;
}

.loading-state {
  width: 100%;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 12px;
  padding: 40px 0;
  color: #909399;
}

.loading-icon {
  animation: rotate 1s linear infinite;
}

@keyframes rotate {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

.result-text {
  font-size: 15px;
  line-height: 1.8;
  color: #303133;
  white-space: pre-wrap;
  word-break: break-all;
}

.action-bar {
  display: flex;
  justify-content: center;
}

.translate-button {
  min-width: 200px;
  height: 44px;
  font-size: 15px;
  font-weight: 500;
  border-radius: 8px;
}

.model-info {
  background: white;
  border-radius: 12px;
  overflow: hidden;
}
</style>
