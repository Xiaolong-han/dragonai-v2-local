import { defineStore } from 'pinia'
import { ref, computed, watch, onMounted } from 'vue'

type ThemeMode = 'light' | 'dark' | 'system'

const THEME_STORAGE_KEY = 'theme-mode'

export const useThemeStore = defineStore('theme', () => {
  // 从 localStorage 读取主题设置，默认为 'system'
  const themeMode = ref<ThemeMode>((localStorage.getItem(THEME_STORAGE_KEY) as ThemeMode) || 'system')
  
  // 系统主题媒体查询
  const systemThemeMedia = window.matchMedia('(prefers-color-scheme: dark)')
  
  // 计算当前实际应用的主题（考虑 system 模式）
  const currentTheme = computed<'light' | 'dark'>(() => {
    if (themeMode.value === 'system') {
      return systemThemeMedia.matches ? 'dark' : 'light'
    }
    return themeMode.value
  })
  
  // 是否是深色模式
  const isDark = computed(() => currentTheme.value === 'dark')
  
  // 应用主题到文档
  function applyTheme() {
    const html = document.documentElement
    
    // 移除旧的主题类
    html.removeAttribute('data-theme')
    
    // 应用新主题
    if (currentTheme.value === 'dark') {
      html.setAttribute('data-theme', 'dark')
    }
    
    // 添加过渡动画类
    html.classList.add('theme-transition')
    
    // 移除过渡类（避免影响其他样式变化）
    setTimeout(() => {
      html.classList.remove('theme-transition')
    }, 300)
  }
  
  // 设置主题模式
  function setTheme(mode: ThemeMode) {
    themeMode.value = mode
    localStorage.setItem(THEME_STORAGE_KEY, mode)
    applyTheme()
  }
  
  // 监听系统主题变化
  function handleSystemThemeChange() {
    if (themeMode.value === 'system') {
      applyTheme()
    }
  }
  
  // 初始化主题
  function initTheme() {
    applyTheme()
    
    // 监听系统主题变化
    if (systemThemeMedia.addEventListener) {
      systemThemeMedia.addEventListener('change', handleSystemThemeChange)
    } else {
      // 兼容旧版浏览器
      systemThemeMedia.addListener(handleSystemThemeChange)
    }
  }
  
  // 清理监听器
  function cleanup() {
    if (systemThemeMedia.removeEventListener) {
      systemThemeMedia.removeEventListener('change', handleSystemThemeChange)
    } else {
      systemThemeMedia.removeListener(handleSystemThemeChange)
    }
  }
  
  // 监听主题模式变化
  watch(themeMode, () => {
    applyTheme()
  })
  
  return {
    themeMode,
    currentTheme,
    isDark,
    setTheme,
    initTheme,
    cleanup
  }
})
