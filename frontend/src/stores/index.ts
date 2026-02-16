import { defineStore } from 'pinia'
import { ref } from 'vue'

export const useAppStore = defineStore('app', () => {
  const token = ref<string | null>(localStorage.getItem('token'))

  const setToken = (newToken: string) => {
    token.value = newToken
    localStorage.setItem('token', newToken)
  }

  const clearToken = () => {
    token.value = null
    localStorage.removeItem('token')
  }

  return {
    token,
    setToken,
    clearToken
  }
})