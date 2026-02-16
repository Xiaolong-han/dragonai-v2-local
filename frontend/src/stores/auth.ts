import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import request from '@/utils/request'

interface User {
  id: number
  username: string
  email: string
  created_at?: string
}

interface LoginRequest {
  username: string
  password: string
}

interface RegisterRequest {
  username: string
  email: string
  password: string
}

export const useAuthStore = defineStore('auth', () => {
  const token = ref<string>(localStorage.getItem('token') || '')
  const user = ref<User | null>(null)
  const loading = ref<boolean>(false)

  const isLoggedIn = computed(() => !!token.value)

  async function login(data: LoginRequest) {
    loading.value = true
    try {
      const response = await request.post('/api/v1/auth/login', data)
      token.value = response.access_token
      localStorage.setItem('token', response.access_token)
      await fetchUserInfo()
      return response
    } finally {
      loading.value = false
    }
  }

  async function register(data: RegisterRequest) {
    loading.value = true
    try {
      const response = await request.post('/api/v1/auth/register', data)
      return response
    } finally {
      loading.value = false
    }
  }

  async function fetchUserInfo() {
    try {
      const response = await request.get('/api/v1/auth/me')
      user.value = response
      return response
    } catch (error) {
      console.error('Failed to fetch user info:', error)
      throw error
    }
  }

  function logout() {
    token.value = ''
    user.value = null
    localStorage.removeItem('token')
  }

  return {
    token,
    user,
    loading,
    isLoggedIn,
    login,
    register,
    fetchUserInfo,
    logout
  }
})
