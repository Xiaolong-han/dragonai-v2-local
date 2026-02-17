<template>
  <div class="main-layout">
    <aside class="sidebar">
      <div class="sidebar-top">
        <button class="new-chat-btn" @click="handleNewConversation">
          <el-icon><Plus /></el-icon>
          <span>新建对话</span>
        </button>
        <div class="conversation-list-wrapper">
          <ConversationList />
        </div>
      </div>
      
      <div class="sidebar-bottom">
        <div class="user-info-section">
          <el-dropdown>
            <div class="user-info">
              <div class="user-avatar">
                <el-icon><User /></el-icon>
              </div>
              <span class="user-name">{{ authStore.user?.username }}</span>
            </div>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item @click="handleLogout">
                  <el-icon><SwitchButton /></el-icon>
                  退出登录
                </el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
        </div>
      </div>
    </aside>
    
    <main class="main-content">
      <header class="main-header">
        <div class="header-content">
          <slot name="header-left"></slot>
        </div>
      </header>
      <div class="content-area">
        <router-view />
      </div>
    </main>
  </div>
</template>

<script setup lang="ts">
import { useAuthStore } from '@/stores/auth'
import { useRouter } from 'vue-router'
import { ElMessageBox, ElMessage } from 'element-plus'
import { Plus, User, SwitchButton } from '@element-plus/icons-vue'
import ConversationList from '@/components/ConversationList.vue'
import { useConversationStore } from '@/stores/conversation'

const authStore = useAuthStore()
const conversationStore = useConversationStore()
const router = useRouter()

const handleLogout = async () => {
  try {
    await ElMessageBox.confirm('确定要退出登录吗?', '提示', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })
    authStore.logout()
    router.push('/login')
  } catch {
  }
}

const handleNewConversation = async () => {
  try {
    await conversationStore.createConversation({ title: '新会话' })
    ElMessage.success('会话创建成功')
  } catch (error) {
    ElMessage.error('创建会话失败')
  }
}
</script>

<style scoped>
.main-layout {
  display: flex;
  height: 100vh;
  overflow: hidden;
  background: var(--bg-secondary);
}

.sidebar {
  width: 260px;
  background: var(--bg-primary);
  display: flex;
  flex-direction: column;
  flex-shrink: 0;
  overflow: hidden;
  border-right: 1px solid var(--border-color);
}

.sidebar-top {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  padding: 16px 12px;
}

.new-chat-btn {
  width: 100%;
  padding: 12px 16px;
  margin-bottom: 16px;
  background: var(--primary-color);
  color: #ffffff;
  border: none;
  border-radius: var(--radius-md);
  cursor: pointer;
  font-size: 14px;
  font-weight: 500;
  transition: all var(--transition-normal);
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
}

.new-chat-btn:hover {
  background: var(--primary-light);
  transform: translateY(-1px);
  box-shadow: var(--shadow-md);
}

.new-chat-btn:active {
  transform: translateY(0);
}

.conversation-list-wrapper {
  flex: 1;
  overflow: hidden;
}

.sidebar-bottom {
  flex-shrink: 0;
  padding: 12px;
  border-top: 1px solid var(--border-light);
}

.user-info-section {
  width: 100%;
}

.user-info {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 16px;
  border-radius: var(--radius-md);
  cursor: pointer;
  transition: background var(--transition-fast);
}

.user-info:hover {
  background: var(--bg-secondary);
}

.user-avatar {
  width: 36px;
  height: 36px;
  background: rgba(45, 125, 255, 0.1);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--primary-color);
}

.user-name {
  flex: 1;
  font-size: 14px;
  color: var(--text-primary);
  font-weight: 500;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.main-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  background: var(--bg-primary);
}

.main-header {
  height: 56px;
  background: var(--bg-primary);
  border-bottom: 1px solid var(--border-light);
  display: flex;
  align-items: center;
  padding: 0 24px;
  flex-shrink: 0;
}

.header-content {
  width: 100%;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.content-area {
  flex: 1;
  overflow: hidden;
}
</style>
