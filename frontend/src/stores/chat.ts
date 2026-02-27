
import { defineStore } from 'pinia'
import { ref } from 'vue'
import { ElMessage } from 'element-plus'

export interface ChatMessage {
  id: number
  conversation_id: number
  role: 'user' | 'assistant'
  content: string
  created_at: string
  is_streaming?: boolean
  thinking_content?: string
  is_thinking_expanded?: boolean
}

export interface ToolOptions {
  targetLang?: string
  sourceLang?: string
  model?: string
  size?: string
  n?: number
  language?: string
}

export interface ChatSettings {
  isExpert: boolean
  enableThinking: boolean
}

const TOOL_PREFIXES: Record<string, string> = {
  translation: '翻译',
  coding: '编程',
  image_generation: '生成图像',
  image_editing: '编辑图像'
}

export const useChatStore = defineStore('chat', () => {
  const messages = ref<ChatMessage[]>([])
  const loading = ref<boolean>(false)
  const sending = ref<boolean>(false)

  async function fetchConversationHistory(conversationId: number) {
    loading.value = true
    try {
      const response = await request.get(`/api/v1/chat/conversations/${conversationId}/history`)
      const rawMessages = (response as any).messages || []
      console.log('[HISTORY] Raw messages:', rawMessages)
      messages.value = rawMessages.map((msg: any) => {
        const metadata = msg.metadata_ || msg.metadata || {}
        console.log('[HISTORY] Message:', msg.id, 'metadata:', metadata, 'thinking_content:', metadata.thinking_content)
        return {
          ...msg,
          thinking_content: metadata.thinking_content || undefined,
          is_thinking_expanded: false
        }
      })
    } finally {
      loading.value = false
    }
  }

  function sendMessage(
    conversationId: number, 
    content: string, 
    images?: string[],
    settings?: ChatSettings
  ) {
    _sendMessageInternal(conversationId, content, images, settings)
  }

  function sendMessageWithTool(
    conversationId: number,
    content: string,
    tool: string,
    options?: ToolOptions,
    images?: string[],
    settings?: ChatSettings
  ) {
    const prefix = TOOL_PREFIXES[tool] || ''
    let prefixedContent = content
    
    if (prefix) {
      if (tool === 'translation' && options?.targetLang) {
        const langMap: Record<string, string> = {
          'zh': '中文',
          'en': '英文',
          'ja': '日文',
          'ko': '韩文',
          'fr': '法文',
          'de': '德文',
          'es': '西班牙文',
          'ru': '俄文'
        }
        const targetLangName = langMap[options.targetLang] || options.targetLang
        prefixedContent = `翻译成${targetLangName}：${content}`
      } else {
        prefixedContent = `${prefix}：${content}`
      }
    }
    
    _sendMessageInternal(conversationId, prefixedContent, images, settings)
  }

  function _sendMessageInternal(
    conversationId: number,
    content: string,
    images: string[] | undefined,
    settings?: ChatSettings
  ) {
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
      is_streaming: true,
      thinking_content: '',
      is_thinking_expanded: true
    }
    messages.value.push(assistantMessage)

    const url = '/api/v1/chat/send'
    
    const body: any = {
      conversation_id: conversationId,
      content: content,
      stream: true,
      model_type: 'general',
      is_expert: settings?.isExpert ?? false,
      enable_thinking: settings?.enableThinking ?? false,
      images: images || null
    }

    const xhr = new XMLHttpRequest()
    let receivedLength = 0
    let isThinkingPhase = false
    
    xhr.open('POST', url, true)
    xhr.setRequestHeader('Content-Type', 'application/json')
    xhr.setRequestHeader('Authorization', `Bearer ${localStorage.getItem('token')}`)
    
    xhr.onprogress = () => {
      if (xhr.status === 401) {
        console.log('[SSE] 401 detected in onprogress')
        localStorage.removeItem('token')
        sending.value = false
        window.location.href = '/login'
        return
      }
      
      const newData = xhr.responseText.substring(receivedLength)
      receivedLength = xhr.responseText.length
      
      console.log('[SSE] onprogress, newData length:', newData.length, 'total:', receivedLength)
      
      const lines = newData.split('\n')
      let newContent = ''
      let newThinkingContent = ''
      
      lines.forEach((line, index) => {
        if (index === lines.length - 1 && !newData.endsWith('\n')) {
          receivedLength -= line.length
          return
        }
        
        if (line.startsWith('data: ')) {
          const data = line.slice(6)
          if (data === '[DONE]') {
            console.log('[SSE] Received DONE signal')
            return
          }
          try {
            const decoded = JSON.parse(data)
            console.log('[SSE] Decoded:', decoded, 'type:', typeof decoded)
            
            if (typeof decoded === 'object' && decoded.type === 'thinking') {
              isThinkingPhase = true
              const thinkingContent = decoded.data?.content || decoded.content || ''
              newThinkingContent += thinkingContent
              console.log('[SSE] Thinking chunk:', thinkingContent.substring(0, 50), 'decoded.data:', decoded.data)
            } else if (typeof decoded === 'object' && decoded.type === 'thinking_end') {
              isThinkingPhase = false
              console.log('[SSE] Thinking phase ended')
            } else if (typeof decoded === 'object' && decoded.type === 'content') {
              const contentStr = decoded.data?.content || decoded.content || ''
              newContent += contentStr
              console.log('[SSE] content event:', contentStr.substring(0, 50) + (contentStr.length > 50 ? '...' : ''))
            } else if (typeof decoded === 'string') {
              newContent += decoded
              console.log('[SSE] data chunk:', decoded.substring(0, 50) + (decoded.length > 50 ? '...' : ''))
            }
          } catch (e) {
            console.error('[SSE] JSON parse error:', e, 'data:', data)
          }
        }
      })
      
      if (newThinkingContent || newContent) {
        const msgIndex = messages.value.findIndex((m) => m.id === assistantMessageId)
        if (msgIndex !== -1) {
          const currentMsg = messages.value[msgIndex]
          messages.value[msgIndex] = {
            ...currentMsg,
            content: currentMsg.content + newContent,
            thinking_content: (currentMsg.thinking_content || '') + newThinkingContent,
            is_streaming: true,
            is_thinking_expanded: isThinkingPhase ? true : false
          }
          console.log('[SSE] Message updated, content length:', messages.value[msgIndex].content.length, 
                      'thinking length:', messages.value[msgIndex].thinking_content?.length)
        } else {
          console.error('[SSE] Message not found for id:', assistantMessageId)
        }
      }
    }
    
    xhr.onload = () => {
      console.log('[SSE] Request completed, status:', xhr.status)
      
      if (xhr.status === 401) {
        localStorage.removeItem('token')
        sending.value = false
        import('element-plus').then(({ ElMessage }) => {
          ElMessage.error('登录已过期，请重新登录')
        })
        window.location.href = '/login'
        return
      }
      
      sending.value = false
      const msgIndex = messages.value.findIndex((m) => m.id === assistantMessageId)
      if (msgIndex !== -1) {
        messages.value[msgIndex] = {
          ...messages.value[msgIndex],
          is_streaming: false,
          is_thinking_expanded: false
        }
      }
    }
    
    xhr.onerror = () => {
      console.error('[SSE] Request error')
      sending.value = false
      const msgIndex = messages.value.findIndex((m) => m.id === assistantMessageId)
      if (msgIndex !== -1) {
        messages.value[msgIndex] = {
          ...messages.value[msgIndex],
          content: messages.value[msgIndex].content || '请求失败，请重试',
          is_streaming: false
        }
      }
    }
    
    xhr.ontimeout = () => {
      console.error('[SSE] Request timeout')
      sending.value = false
      const msgIndex = messages.value.findIndex((m) => m.id === assistantMessageId)
      if (msgIndex !== -1) {
        messages.value[msgIndex] = {
          ...messages.value[msgIndex],
          is_streaming: false
        }
      }
    }
    
    xhr.timeout = 120000
    xhr.send(JSON.stringify(body))
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

  function toggleThinkingExpanded(messageId: number) {
    const msgIndex = messages.value.findIndex((m) => m.id === messageId)
    if (msgIndex !== -1) {
      messages.value[msgIndex] = {
        ...messages.value[msgIndex],
        is_thinking_expanded: !messages.value[msgIndex].is_thinking_expanded
      }
    }
  }

  return {
    messages,
    loading,
    sending,
    fetchConversationHistory,
    sendMessage,
    sendMessageWithTool,
    regenerateMessage,
    clearMessages,
    toggleThinkingExpanded
  }
})

import request from '@/utils/request'
