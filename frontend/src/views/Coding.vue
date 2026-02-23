<template>
  <div class="coding-page">
    <div class="page-header">
      <div class="header-content">
        <el-icon class="page-icon" :size="36">
          <Operation />
        </el-icon>
        <div>
          <h1>编程助手</h1>
          <p>描述你的编程需求，AI 将为你编写代码</p>
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
            <label>温度 (Temperature)</label>
            <el-slider
              v-model="temperature"
              :min="0"
              :max="1"
              :step="0.1"
              :marks="{ 0: '精确', 0.5: '平衡', 1: '创意' }"
              show-input
            />
          </div>

          <div class="form-item">
            <label>最大 Token 数</label>
            <el-input-number
              v-model="maxTokens"
              :min="100"
              :max="32000"
              :step="100"
              placeholder="留空使用默认"
              style="width: 100%"
              controls-position="right"
            />
          </div>
        </el-card>
      </div>

      <div class="main-panel">
        <div class="prompt-section">
          <el-input
            v-model="prompt"
            type="textarea"
            :rows="6"
            placeholder="描述你的编程需求，例如：帮我写一个 Python 函数，实现快速排序算法..."
            class="prompt-input"
          />
          <el-button
            type="primary"
            size="large"
            :loading="loading"
            :disabled="!prompt.trim()"
            @click="generateCode"
            class="generate-button"
          >
            <el-icon><Promotion /></el-icon>
            生成代码
          </el-button>
        </div>

        <div class="result-section" v-if="result">
          <el-card class="result-card">
            <template #header>
              <div class="result-header">
                <span>生成结果</span>
                <el-tag size="small">{{ result.model_name }}</el-tag>
              </div>
            </template>

            <div class="result-content">
              <div class="thinking-section" v-if="result.thinking_content || result.reasoning_content">
                <div class="section-title">
                  <el-icon><ChatDotRound /></el-icon>
                  <span>思考过程</span>
                </div>
                <div class="thinking-content">
                  {{ result.thinking_content || result.reasoning_content }}
                </div>
              </div>

              <div class="code-section">
                <div class="section-title">
                  <el-icon><Document /></el-icon>
                  <span>代码</span>
                  <el-button type="primary" link size="small" @click="copyCode">
                    <el-icon><DocumentCopy /></el-icon>
                    复制
                  </el-button>
                </div>
                <div class="code-wrapper">
                  <pre><code>{{ result.content }}</code></pre>
                </div>
              </div>
            </div>
          </el-card>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { Operation, Promotion, Document, DocumentCopy, ChatDotRound } from '@element-plus/icons-vue'
import { useConversationStore } from '@/stores/conversation'
import { useChatStore } from '@/stores/chat'

const conversationStore = useConversationStore()
const chatStore = useChatStore()

const prompt = ref('')
const isExpert = ref(false)
const temperature = ref(0.7)
const maxTokens = ref<number | null>(null)
const loading = ref(false)
const result = ref<any>(null)

async function generateCode() {
  if (!prompt.value.trim()) {
    ElMessage.warning('请输入编程需求')
    return
  }

  loading.value = true
  result.value = null
  
  try {
    let conversationId = conversationStore.currentConversationId
    if (!conversationId) {
      const conv = await conversationStore.createConversation({
        title: `编程: ${prompt.value.substring(0, 20)}...`
      })
      conversationId = conv.id
    }

    const prefixedContent = `编程：${prompt.value}`

    await new Promise<void>((resolve, reject) => {
      const unsubscribe = chatStore.$onAction(({ name, after }) => {
        if (name === 'sendMessage' || name === 'sendMessageWithTool') {
          after(() => {
            const lastMessage = chatStore.messages[chatStore.messages.length - 1]
            if (lastMessage && lastMessage.role === 'assistant' && !lastMessage.is_streaming) {
              result.value = {
                content: lastMessage.content,
                model_name: isExpert.value ? 'expert' : 'fast'
              }
              loading.value = false
              ElMessage.success('代码生成成功！')
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
          reject(new Error('代码生成超时'))
        }
      }, 120000)
    })
  } catch (error) {
    console.error('Failed to generate code:', error)
    ElMessage.error('代码生成失败，请重试')
    loading.value = false
  }
}

function copyCode() {
  if (result.value?.content) {
    navigator.clipboard.writeText(result.value.content).then(() => {
      ElMessage.success('代码已复制到剪贴板')
    }).catch(() => {
      ElMessage.error('复制失败')
    })
  }
}

onMounted(async () => {
  await conversationStore.fetchConversations()
})
</script>

<style scoped>
.coding-page {
  min-height: 100vh;
  background: #f5f7fa;
}

.page-header {
  background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
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

.result-section {
  background: white;
  border-radius: 12px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.04);
}

.result-card {
  border: none;
}

.result-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.result-content {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.section-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 14px;
  font-weight: 600;
  color: #303133;
  margin-bottom: 12px;
}

.section-title .el-button {
  margin-left: auto;
}

.thinking-section {
  padding: 16px;
  background: #f5f7fa;
  border-radius: 8px;
}

.thinking-content {
  font-size: 14px;
  color: #606266;
  line-height: 1.8;
  white-space: pre-wrap;
}

.code-section {
  border: 1px solid #e4e7ed;
  border-radius: 8px;
  overflow: hidden;
}

.code-section .section-title {
  padding: 12px 16px;
  margin-bottom: 0;
  border-bottom: 1px solid #e4e7ed;
  background: #fafafa;
}

.code-wrapper {
  padding: 16px;
  background: #1e1e1e;
  overflow-x: auto;
}

.code-wrapper pre {
  margin: 0;
}

.code-wrapper code {
  font-family: 'Fira Code', 'Consolas', 'Monaco', monospace;
  font-size: 14px;
  line-height: 1.6;
  color: #d4d4d4;
  white-space: pre-wrap;
  word-break: break-all;
}
</style>
