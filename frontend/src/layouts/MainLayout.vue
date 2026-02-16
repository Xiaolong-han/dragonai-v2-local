<template>
  <div class="main-layout">
    <aside class="sidebar">
      <div class="sidebar-header">
        <h1>AI Chat</h1>
      </div>
      <ConversationList />
    </aside>
    <main class="main-content">
      <header class="main-header">
        <div class="header-content">
          <slot name="header-left"></slot>
          <div class="user-info">
            <el-dropdown>
              <span class="user-name">
                <el-icon><User /></el-icon>
                {{ authStore.user?.username }}
              </span>
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
import { ElMessageBox } from 'element-plus'
import { User, SwitchButton } from '@element-plus/icons-vue'
import ConversationList from '@/components/ConversationList.vue'

const authStore = useAuthStore()
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
    // 用户取消
  }
}
</script>

<style scoped>
.main-layout {
  display: flex;
  height: 100vh;
  overflow: hidden;
}

.sidebar {
  width: 280px;
  background: #ffffff;
  border-right: 1px solid #e4e7ed;
  display: flex;
  flex-direction: column;
  flex-shrink: 0;
}

.sidebar-header {
  padding: 20px;
  border-bottom: 1px solid #e4e7ed;
}

.sidebar-header h1 {
  margin: 0;
  font-size: 20px;
  color: #303133;
}

.main-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  background: #f5f7fa;
}

.main-header {
  height: 60px;
  background: #ffffff;
  border-bottom: 1px solid #e4e7ed;
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

.user-info {
  display: flex;
  align-items: center;
}

.user-name {
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 8px;
  color: #606266;
}

.content-area {
  flex: 1;
  overflow: hidden;
}
</style>
