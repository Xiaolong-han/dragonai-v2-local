
import { defineStore } from 'pinia'
import { ref } from 'vue'
import request from '@/utils/request'

export interface ChatMessage {
  id: number
  conversation_id: number
  role: 'user' | 'assistant'
  content: string
  created_at: string
  is_streaming?: boolean
}

export const useChatStore = defineStore('chat', () => {
  const messages = ref<ChatMessage[]>([])
  const loading = ref<boolean>(false)
  const sending = ref<boolean>(false)

  async function fetchConversationHistory(conversationId: number) {
    loading.value = true
    try {
      const response = await request.get(`/api/v1/chat/conversations/${conversationId}/history`)
      messages.value = (response as any).messages || []
    } finally {
      loading.value = false
    }
  }

  function sendMessage(conversationId: number, content: string) {
    sending.value = true

    const userMessage: ChatMessage = {
      id: Date.now(),
      conversation_id: conversationId,
      role: 'user',
      content: content,
      created_at: new Date().toISOString()
    }
    messages.value.push(userMessage)

    const assistantMessageId = Date.now() + 1
    const assistantMessage: ChatMessage = {
      id: assistantMessageId,
      conversation_id: conversationId,
      role: 'assistant',
      content: '',
      created_at: new Date().toISOString(),
      is_streaming: true
    }
    messages.value.push(assistantMessage)

    const url = 'http://localhost:8000/api/v1/chat/send'
    const body = JSON.stringify({
      conversation_id: conversationId,
      content: content,
      stream: true,
      model_type: 'general',
      is_expert: false,
      images: null
    })

    fetch(url, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${localStorage.getItem('token')}`
      },
      body: body
    })
      .then((response) => {
        if (!response.ok) {
          throw new Error('Network response was not ok')
        }
        const reader = response.body?.getReader()
        const decoder = new TextDecoder()

        function updateMessageContent(newContent: string, isStreaming: boolean = true) {
          const msgIndex = messages.value.findIndex((m) => m.id === assistantMessageId)
          if (msgIndex !== -1) {
            const msg = messages.value[msgIndex]
            messages.value[msgIndex] = {
              ...msg,
              content: newContent,
              is_streaming: isStreaming
            }
          }
        }

        function readStream() {
          reader?.read().then((result) => {
            if (result.done) {
              sending.value = false
              const msgIndex = messages.value.findIndex((m) => m.id === assistantMessageId)
              if (msgIndex !== -1) {
                const msg = messages.value[msgIndex]
                messages.value[msgIndex] = {
                  ...msg,
                  is_streaming: false
                }
              }
              return
            }

            const chunk = decoder.decode(result.value)
            const lines = chunk.split('\n')
            let newContent = ''

            lines.forEach((line) => {
              if (line.startsWith('data: ')) {
                const data = line.slice(6)
                if (data === '[DONE]') {
                  return
                }
                newContent += data
              }
            })

            if (newContent) {
              const msgIndex = messages.value.findIndex((m) => m.id === assistantMessageId)
              if (msgIndex !== -1) {
                const currentContent = messages.value[msgIndex].content
                updateMessageContent(currentContent + newContent, true)
              }
            }

            readStream()
          })
        }

        readStream()
      })
      .catch((error) => {
        console.error('Error sending message:', error)
        sending.value = false
        const msgIndex = messages.value.findIndex((m) => m.id === assistantMessageId)
        if (msgIndex !== -1) {
          const msg = messages.value[msgIndex]
          messages.value[msgIndex] = {
            ...msg,
            content: `错误: ${error.message}`,
            is_streaming: false
          }
        }
      })
  }

  function regenerateMessage(conversationId: number, messageIndex: number) {
    const message = messages.value[messageIndex]
    if (!message || message.role !== 'assistant') {
      return
    }

    let userMessage: ChatMessage | undefined
    for (let i = messageIndex - 1; i >= 0; i--) {
      if (messages.value[i]?.role === 'user') {
        userMessage = messages.value[i]
        break
      }
    }

    if (!userMessage) {
      return
    }

    messages.value = messages.value.slice(0, messageIndex)
    sendMessage(conversationId, userMessage.content)
  }

  function clearMessages() {
    messages.value = []
  }

  return {
    messages,
    loading,
    sending,
    fetchConversationHistory,
    sendMessage,
    regenerateMessage,
    clearMessages
  }
})
