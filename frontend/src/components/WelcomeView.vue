<template>
  <div class="welcome-view">
    <div class="welcome-content">
      <div class="brand-section">
        <div class="brand-icon">
          <svg width="72" height="72" viewBox="0 0 72 72" fill="none" xmlns="http://www.w3.org/2000/svg">
            <circle cx="36" cy="36" r="36" fill="url(#gradient)"/>
            <path d="M36 20C27.163 20 20 27.163 20 36C20 44.837 27.163 52 36 52C44.837 52 52 44.837 52 36C52 27.163 44.837 20 36 20ZM36 48C29.373 48 24 42.627 24 36C24 29.373 29.373 24 36 24C42.627 24 48 29.373 48 36C48 42.627 42.627 48 36 48ZM40 36C40 38.209 38.209 40 36 40C33.791 40 32 38.209 32 36C32 33.791 33.791 32 36 32C38.209 32 40 33.791 40 36Z" fill="white"/>
            <defs>
              <linearGradient id="gradient" x1="0" y1="0" x2="72" y2="72" gradientUnits="userSpaceOnUse">
                <stop stop-color="#4080FF"/>
                <stop offset="1" stop-color="#20C0FF"/>
              </linearGradient>
            </defs>
          </svg>
        </div>
        <h1 class="welcome-title">你好，我是AI智能助手</h1>
        <p class="welcome-subtitle">我可以帮你解答问题、写代码、翻译、分析数据等，有什么需要帮助的吗？</p>
      </div>
      
      <div class="quick-questions">
        <div class="questions-grid">
          <div class="question-card" @click="handleQuickQuestion('你好，请介绍一下自己')">
            <div class="question-icon">👋</div>
            <span class="question-text">你好，请介绍一下自己</span>
          </div>
          <div class="question-card" @click="handleQuickQuestion('帮我写一段Python代码')">
            <div class="question-icon">💻</div>
            <span class="question-text">帮我写一段Python代码</span>
          </div>
          <div class="question-card" @click="handleQuickQuestion('帮我翻译一段文字')">
            <div class="question-icon">🌐</div>
            <span class="question-text">帮我翻译一段文字</span>
          </div>
          <div class="question-card" @click="handleQuickQuestion('帮我分析一下这个问题')">
            <div class="question-icon">💡</div>
            <span class="question-text">帮我分析一下这个问题</span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
interface Emits {
  (e: 'send-message', value: string): void
}

const emit = defineEmits<Emits>()

function handleQuickQuestion(question: string) {
  emit('send-message', question)
}
</script>

<style scoped>
.welcome-view {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 100%;
  background: #f7f8fa;
  padding: 24px;
}

.welcome-content {
  max-width: 850px;
  width: 100%;
  text-align: center;
}

.brand-section {
  margin-bottom: 56px;
}

.brand-icon {
  display: flex;
  justify-content: center;
  margin-bottom: 28px;
}

.welcome-title {
  font-size: 32px;
  font-weight: 700;
  color: #1d2129;
  margin: 0 0 16px 0;
  letter-spacing: -0.3px;
}

.welcome-subtitle {
  font-size: 16px;
  color: #4e5969;
  margin: 0;
  line-height: 1.6;
  max-width: 600px;
  margin-left: auto;
  margin-right: auto;
}

.quick-questions {
  width: 100%;
}

.questions-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
  gap: 16px;
}

.question-card {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
  padding: 28px 20px;
  background: #ffffff;
  border: 1px solid #e5e6eb;
  border-radius: 16px;
  cursor: pointer;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

.question-card:hover {
  background: #ffffff;
  border-color: #4080ff;
  transform: translateY(-4px);
  box-shadow: 0 8px 24px rgba(64, 128, 255, 0.12);
}

.question-card:active {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(64, 128, 255, 0.12);
}

.question-icon {
  font-size: 36px;
}

.question-text {
  font-size: 14px;
  color: #1d2129;
  font-weight: 500;
  text-align: center;
  line-height: 1.5;
}

@media (max-width: 600px) {
  .welcome-title {
    font-size: 26px;
  }

  .welcome-subtitle {
    font-size: 14px;
  }

  .questions-grid {
    grid-template-columns: 1fr;
  }

  .brand-section {
    margin-bottom: 40px;
  }
  
  .brand-icon svg {
    width: 60px;
    height: 60px;
  }
  
  .question-card {
    padding: 24px 16px;
  }
}
</style>
