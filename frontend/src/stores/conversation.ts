import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import request from '@/utils/request'

export interface Conversation {
  id: number
  user_id: number
  title: string
  model_name?: string
  is_pinned: boolean
  created_at: string
  updated_at: string
}

export interface ConversationCreate {
  title: string
  model_name?: string
}

export interface ConversationUpdate {
  title?: string
  is_pinned?: boolean
  model_name?: string
}

export const useConversationStore = defineStore('conversation', () => {
  const conversations = ref<Conversation[]>([])
  const currentConversationId = ref<number | null>(null)
  const loading = ref<boolean>(false)

  const currentConversation = computed(() => 
    conversations.value.find(c => c.id === currentConversationId.value) || null
  )

  const sortedConversations = computed(() => {
    return [...conversations.value].sort((a, b) => {
      if (a.is_pinned && !b.is_pinned) return -1
      if (!a.is_pinned && b.is_pinned) return 1
      return new Date(b.updated_at).getTime() - new Date(a.updated_at).getTime()
    })
  })

  async function fetchConversations() {
    loading.value = true
    try {
      const response = await request.get('/api/v1/conversations')
      conversations.value = response
    } finally {
      loading.value = false
    }
  }

  async function createConversation(data: ConversationCreate) {
    loading.value = true
    try {
      const response = await request.post('/api/v1/conversations', data)
      conversations.value.unshift(response)
      currentConversationId.value = response.id
      return response
    } finally {
      loading.value = false
    }
  }

  async function updateConversation(conversationId: number, data: ConversationUpdate) {
    loading.value = true
    try {
      const response = await request.put(`/api/v1/conversations/${conversationId}`, data)
      const index = conversations.value.findIndex(c => c.id === conversationId)
      if (index !== -1) {
        conversations.value[index] = { ...conversations.value[index], ...response }
      }
      return response
    } finally {
      loading.value = false
    }
  }

  async function deleteConversation(conversationId: number) {
    loading.value = true
    try {
      await request.delete(`/api/v1/conversations/${conversationId}`)
      conversations.value = conversations.value.filter(c => c.id !== conversationId)
      if (currentConversationId.value === conversationId) {
        currentConversationId.value = null
      }
    } finally {
      loading.value = false
    }
  }

  async function pinConversation(conversationId: number) {
    loading.value = true
    try {
      const response = await request.post(`/api/v1/conversations/${conversationId}/pin`)
      const index = conversations.value.findIndex(c => c.id === conversationId)
      if (index !== -1) {
        conversations.value[index] = { ...conversations.value[index], ...response }
      }
      return response
    } finally {
      loading.value = false
    }
  }

  async function unpinConversation(conversationId: number) {
    loading.value = true
    try {
      const response = await request.post(`/api/v1/conversations/${conversationId}/unpin`)
      const index = conversations.value.findIndex(c => c.id === conversationId)
      if (index !== -1) {
        conversations.value[index] = { ...conversations.value[index], ...response }
      }
      return response
    } finally {
      loading.value = false
    }
  }

  function selectConversation(conversationId: number) {
    currentConversationId.value = conversationId
  }

  return {
    conversations,
    currentConversationId,
    currentConversation,
    sortedConversations,
    loading,
    fetchConversations,
    createConversation,
    updateConversation,
    deleteConversation,
    pinConversation,
    unpinConversation,
    selectConversation
  }
})
