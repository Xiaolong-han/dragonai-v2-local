<template>
  <el-dropdown trigger="click" @command="handleThemeChange" popper-class="theme-dropdown">
    <div 
      class="theme-switcher-btn" 
      :title="currentThemeLabel"
      role="button"
      aria-label="切换主题"
      tabindex="0"
    >
      <el-icon :size="18">
        <component :is="currentThemeIcon" />
      </el-icon>
    </div>
    <template #dropdown>
      <el-dropdown-menu>
        <el-dropdown-item 
          command="light" 
          :class="{ 'is-active': themeStore.themeMode === 'light' }"
        >
          <el-icon :size="16"><Sunny /></el-icon>
          <span>浅色模式</span>
          <el-icon v-if="themeStore.themeMode === 'light'" class="check-icon" :size="14"><Check /></el-icon>
        </el-dropdown-item>
        <el-dropdown-item 
          command="dark" 
          :class="{ 'is-active': themeStore.themeMode === 'dark' }"
        >
          <el-icon :size="16"><Moon /></el-icon>
          <span>深色模式</span>
          <el-icon v-if="themeStore.themeMode === 'dark'" class="check-icon" :size="14"><Check /></el-icon>
        </el-dropdown-item>
        <el-dropdown-item 
          command="system" 
          :class="{ 'is-active': themeStore.themeMode === 'system' }"
        >
          <el-icon :size="16"><Monitor /></el-icon>
          <span>跟随系统</span>
          <el-icon v-if="themeStore.themeMode === 'system'" class="check-icon" :size="14"><Check /></el-icon>
        </el-dropdown-item>
      </el-dropdown-menu>
    </template>
  </el-dropdown>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { Sunny, Moon, Monitor, Check } from '@element-plus/icons-vue'
import { useThemeStore } from '@/stores/theme'

type ThemeMode = 'light' | 'dark' | 'system'

const themeStore = useThemeStore()

// 当前主题图标
const currentThemeIcon = computed(() => {
  switch (themeStore.themeMode) {
    case 'light':
      return Sunny
    case 'dark':
      return Moon
    case 'system':
    default:
      return Monitor
  }
})

// 当前主题标签
const currentThemeLabel = computed(() => {
  switch (themeStore.themeMode) {
    case 'light':
      return '浅色模式'
    case 'dark':
      return '深色模式'
    case 'system':
    default:
      return '跟随系统'
  }
})

// 处理主题切换
function handleThemeChange(command: ThemeMode) {
  themeStore.setTheme(command)
}
</script>

<style scoped>
.theme-switcher-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 36px;
  height: 36px;
  border-radius: 8px;
  cursor: pointer;
  color: var(--text-secondary);
  transition: all 0.2s ease;
}

.theme-switcher-btn:hover {
  background: var(--bg-secondary);
  color: var(--primary-color);
}

.theme-switcher-btn:focus-visible {
  outline: 2px solid var(--primary-color);
  outline-offset: 2px;
}
</style>

<style>
/* 下拉菜单样式 */
.theme-dropdown .el-dropdown-menu {
  background: var(--bg-primary);
  border: 1px solid var(--border-color);
  box-shadow: var(--shadow-md);
}

.theme-dropdown .el-dropdown-menu__item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 16px;
  min-width: 140px;
  color: var(--text-primary);
}

.theme-dropdown .el-dropdown-menu__item span {
  flex: 1;
}

.theme-dropdown .el-dropdown-menu__item:hover {
  color: var(--text-primary);
  background: var(--bg-secondary);
}

.theme-dropdown .el-dropdown-menu__item.is-active {
  color: var(--primary-color);
  background: var(--bg-secondary);
}

.theme-dropdown .check-icon {
  color: var(--primary-color);
}
</style>
