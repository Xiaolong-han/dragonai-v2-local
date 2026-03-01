
import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
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
  incomplete?: boolean
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
  const messagesMap = ref<Record<number, ChatMessage[]>>({})
  const loadingMap = ref<Record<number, boolean>>({})
  const sendingMap = ref<Record<number, boolean>>({})
  const xhrMap = new Map<number, XMLHttpRequest>()
  const assistantMessageIdMap = new Map<number, number>()
  const currentConversationId = ref<number | null>(null)

  const messages = computed(() => {
    if (!currentConversationId.value) return []
    return messagesMap.value[currentConversationId.value] || []
  })

  const loading = computed(() => {
    if (!currentConversationId.value) return false
    return loadingMap.value[currentConversationId.value] || false
  })

  const sending = computed(() => {
    if (!currentConversationId.value) return false
    return sendingMap.value[currentConversationId.value] || false
  })

  function isSending(conversationId: number): boolean {
    return sendingMap.value[conversationId] || false
  }

  function setCurrentConversation(conversationId: number | null) {
    currentConversationId.value = conversationId
    // 确保新会话的 loading 状态被正确初始化
    if (conversationId && loadingMap.value[conversationId] === undefined) {
      loadingMap.value[conversationId] = false
    }
  }

  function getMessages(conversationId: number): ChatMessage[] {
    return messagesMap.value[conversationId] || []
  }

  function setMessages(conversationId: number, msgs: ChatMessage[]) {
    messagesMap.value[conversationId] = msgs
  }

  async function fetchConversationHistory(conversationId: number) {
    loadingMap.value[conversationId] = true
    try {
      const response = await request.get(`/api/v1/chat/conversations/${conversationId}/history`)
      const rawMessages = (response as any).messages || []
      console.log('[HISTORY] Raw messages for', conversationId, ':', rawMessages.length)
      
      const serverMessages = rawMessages.map((msg: any) => {
        const metadata = msg.metadata_ || msg.metadata || {}
        return {
          ...msg,
          thinking_content: metadata.thinking_content || undefined,
          is_thinking_expanded: false,
          incomplete: metadata.incomplete || false
        }
      })

      const existingMessages = messagesMap.value[conversationId] || []
      const streamingMsg = existingMessages.find(m => m.is_streaming)
      
      if (streamingMsg) {
        const serverIds = new Set(serverMessages.map((m: ChatMessage) => m.id))
        if (!serverIds.has(streamingMsg.id)) {
          messagesMap.value[conversationId] = [...serverMessages, streamingMsg]
        } else {
          messagesMap.value[conversationId] = serverMessages
        }
      } else {
        messagesMap.value[conversationId] = serverMessages
      }
    } catch (error) {
      console.error('[HISTORY] Error fetching history for', conversationId, error)
      messagesMap.value[conversationId] = []
    } finally {
      loadingMap.value[conversationId] = false
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
    sendingMap.value[conversationId] = true

    const existingMsgs = messagesMap.value[conversationId] || []

    const userMessage: ChatMessage = {
      id: Date.now(),
      conversation_id: conversationId,
      role: 'user',
      content: content,
      created_at: new Date().toISOString()
    }

    const assistantMessageId = Date.now() + 1
    assistantMessageIdMap.set(conversationId, assistantMessageId)
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

    messagesMap.value[conversationId] = [...existingMsgs, userMessage, assistantMessage]

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
    xhrMap.set(conversationId, xhr)
    let receivedLength = 0
    let isThinkingPhase = false
    
    xhr.open('POST', url, true)
    xhr.setRequestHeader('Content-Type', 'application/json')
    xhr.setRequestHeader('Authorization', `Bearer ${localStorage.getItem('token')}`)
    
    const updateMessage = (newContent: string, newThinkingContent: string) => {
      const currentMsgs = messagesMap.value[conversationId]
      if (!currentMsgs) return
      
      const msgIndex = currentMsgs.findIndex((m) => m.id === assistantMessageId)
      if (msgIndex !== -1) {
        const currentMsg = currentMsgs[msgIndex]
        const newMsgs = [...currentMsgs]
        newMsgs[msgIndex] = {
          ...currentMsg,
          content: currentMsg.content + newContent,
          thinking_content: (currentMsg.thinking_content || '') + newThinkingContent,
          is_streaming: true,
          is_thinking_expanded: isThinkingPhase ? true : false
        }
        messagesMap.value[conversationId] = newMsgs
      }
    }
    
    xhr.onprogress = () => {
      if (xhr.status === 401) {
        console.log('[SSE] 401 detected in onprogress')
        localStorage.removeItem('token')
        sendingMap.value[conversationId] = false
        window.location.href = '/login'
        return
      }
      
      const newData = xhr.responseText.substring(receivedLength)
      receivedLength = xhr.responseText.length
      
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
            return
          }
          try {
            const decoded = JSON.parse(data)
            
            if (typeof decoded === 'object' && decoded.type === 'thinking') {
              isThinkingPhase = true
              const thinkingContent = decoded.data?.content || decoded.content || ''
              newThinkingContent += thinkingContent
            } else if (typeof decoded === 'object' && decoded.type === 'thinking_end') {
              isThinkingPhase = false
            } else if (typeof decoded === 'object' && decoded.type === 'content') {
              const contentStr = decoded.data?.content || decoded.content || ''
              newContent += contentStr
            } else if (typeof decoded === 'string') {
              newContent += decoded
            }
          } catch (e) {
            console.error('[SSE] JSON parse error:', e, 'data:', data)
          }
        }
      })
      
      if (newThinkingContent || newContent) {
        updateMessage(newContent, newThinkingContent)
      }
    }
    
    xhr.onload = () => {
      console.log('[SSE] Request completed for conversation:', conversationId)
      xhrMap.delete(conversationId)
      assistantMessageIdMap.delete(conversationId)
      
      if (xhr.status === 401) {
        localStorage.removeItem('token')
        sendingMap.value[conversationId] = false
        import('element-plus').then(({ ElMessage }) => {
          ElMessage.error('登录已过期，请重新登录')
        })
        window.location.href = '/login'
        return
      }
      
      sendingMap.value[conversationId] = false
      const currentMsgs = messagesMap.value[conversationId]
      if (currentMsgs) {
        const msgIndex = currentMsgs.findIndex((m) => m.id === assistantMessageId)
        if (msgIndex !== -1) {
          const newMsgs = [...currentMsgs]
          newMsgs[msgIndex] = {
            ...newMsgs[msgIndex],
            is_streaming: false,
            is_thinking_expanded: false
          }
          messagesMap.value[conversationId] = newMsgs
        }
      }
    }
    
    xhr.onerror = () => {
      console.error('[SSE] Request error for conversation:', conversationId)
      xhrMap.delete(conversationId)
      assistantMessageIdMap.delete(conversationId)
      
      sendingMap.value[conversationId] = false
      const currentMsgs = messagesMap.value[conversationId]
      if (currentMsgs) {
        const msgIndex = currentMsgs.findIndex((m) => m.id === assistantMessageId)
        if (msgIndex !== -1) {
          const newMsgs = [...currentMsgs]
          newMsgs[msgIndex] = {
            ...newMsgs[msgIndex],
            content: newMsgs[msgIndex].content || '请求失败，请重试',
            is_streaming: false
          }
          messagesMap.value[conversationId] = newMsgs
        }
      }
    }
    
    xhr.ontimeout = () => {
      console.error('[SSE] Request timeout for conversation:', conversationId)
      xhrMap.delete(conversationId)
      assistantMessageIdMap.delete(conversationId)
      
      sendingMap.value[conversationId] = false
      const currentMsgs = messagesMap.value[conversationId]
      if (currentMsgs) {
        const msgIndex = currentMsgs.findIndex((m) => m.id === assistantMessageId)
        if (msgIndex !== -1) {
          const newMsgs = [...currentMsgs]
          newMsgs[msgIndex] = {
            ...newMsgs[msgIndex],
            is_streaming: false
          }
          messagesMap.value[conversationId] = newMsgs
        }
      }
    }
    
    xhr.onabort = () => {
      console.log('[SSE] Request aborted for conversation:', conversationId)
      xhrMap.delete(conversationId)
      assistantMessageIdMap.delete(conversationId)
      
      sendingMap.value[conversationId] = false
      const currentMsgs = messagesMap.value[conversationId]
      if (currentMsgs) {
        const msgIndex = currentMsgs.findIndex((m) => m.id === assistantMessageId)
        if (msgIndex !== -1) {
          const newMsgs = [...currentMsgs]
          newMsgs[msgIndex] = {
            ...newMsgs[msgIndex],
            is_streaming: false,
            incomplete: true
          }
          messagesMap.value[conversationId] = newMsgs
        }
      }
    }
    
    xhr.timeout = 120000
    xhr.send(JSON.stringify(body))
  }

  function regenerateMessage(conversationId: number, messageIndex: number) {
    const msgs = messagesMap.value[conversationId]
    if (!msgs) return
    
    const message = msgs[messageIndex]
    if (!message || message.role !== 'assistant') {
      return
    }

    let userMessage: ChatMessage | undefined
    for (let i = messageIndex - 1; i >= 0; i--) {
      if (msgs[i]?.role === 'user') {
        userMessage = msgs[i]
        break
      }
    }

    if (!userMessage) {
      return
    }

    messagesMap.value[conversationId] = msgs.slice(0, messageIndex)
    sendMessage(conversationId, userMessage.content)
  }

  function clearMessages() {
    if (currentConversationId.value) {
      delete messagesMap.value[currentConversationId.value]
    }
  }

  function cancelRequest(conversationId: number) {
    const xhr = xhrMap.get(conversationId)
    if (xhr) {
      xhr.abort()
      xhrMap.delete(conversationId)
    }
    sendingMap.value[conversationId] = false
  }

  function toggleThinkingExpanded(messageId: number) {
    if (!currentConversationId.value) return
    const msgs = messagesMap.value[currentConversationId.value]
    if (!msgs) return
    
    const msgIndex = msgs.findIndex((m) => m.id === messageId)
    if (msgIndex !== -1) {
      const newMsgs = [...msgs]
      newMsgs[msgIndex] = {
        ...newMsgs[msgIndex],
        is_thinking_expanded: !newMsgs[msgIndex].is_thinking_expanded
      }
      messagesMap.value[currentConversationId.value] = newMsgs
    }
  }

  return {
    messages,
    loading,
    sending,
    isSending,
    setCurrentConversation,
    getMessages,
    setMessages,
    fetchConversationHistory,
    sendMessage,
    sendMessageWithTool,
    regenerateMessage,
    clearMessages,
    cancelRequest,
    toggleThinkingExpanded
  }
})

import request from '@/utils/request'
