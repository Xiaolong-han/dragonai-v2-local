
import { defineStore } from 'pinia'
import { ref } from 'vue'
import request from '@/utils/request'
import { ElMessage } from 'element-plus'

export interface ChatMessage {
  id: number
  conversation_id: number
  role: 'user' | 'assistant'
  content: string
  created_at: string
  is_streaming?: boolean
}

export interface SkillOptions {
  targetLang?: string
  sourceLang?: string
  model?: string
  size?: string
  n?: number
  language?: string
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

  function sendMessage(
    conversationId: number, 
    content: string, 
    images?: string[]
  ) {
    _sendMessageInternal(conversationId, content, images, null, null)
  }

  function sendMessageWithSkill(
    conversationId: number,
    content: string,
    skill: string,
    options?: SkillOptions,
    images?: string[]
  ) {
    // 根据技能类型选择直接调用专项API还是通过chat接口
    if (skill === 'translation') {
      _sendTranslationSkill(conversationId, content, options)
    } else if (skill === 'coding') {
      _sendCodingSkill(conversationId, content, options)
    } else if (skill === 'image_generation') {
      _sendImageGenerationSkill(conversationId, content, options)
    } else {
      // 其他技能通过chat接口
      _sendMessageInternal(conversationId, content, images, skill, options)
    }
  }

  // 直接调用翻译专项API
  async function _sendTranslationSkill(
    conversationId: number,
    content: string,
    options?: SkillOptions
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
      is_streaming: true
    }
    messages.value.push(assistantMessage)

    try {
      const response = await request.post('/api/v1/skills/direct/translate', {
        text: content,
        target_lang: options?.targetLang || 'zh',
        source_lang: options?.sourceLang,
        model_mode: 'fast'
      }) as any

      if (response.success && response.data) {
        const msgIndex = messages.value.findIndex((m) => m.id === assistantMessageId)
        if (msgIndex !== -1) {
          messages.value[msgIndex] = {
            ...messages.value[msgIndex],
            content: response.data.translated,
            is_streaming: false
          }
        }
        ElMessage.success('翻译完成')
      } else {
        throw new Error('翻译失败')
      }
    } catch (error) {
      console.error('Translation error:', error)
      const msgIndex = messages.value.findIndex((m) => m.id === assistantMessageId)
      if (msgIndex !== -1) {
        messages.value[msgIndex] = {
          ...messages.value[msgIndex],
          content: '翻译失败，请重试',
          is_streaming: false
        }
      }
      ElMessage.error('翻译失败')
    } finally {
      sending.value = false
    }
  }

  // 直接调用编程专项API
  async function _sendCodingSkill(
    conversationId: number,
    content: string,
    options?: SkillOptions
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
      is_streaming: true
    }
    messages.value.push(assistantMessage)

    try {
      const response = await request.post('/api/v1/skills/direct/code/assist', {
        prompt: content,
        language: options?.language || 'python',
        model_mode: 'fast',
        stream: false
      }) as any

      if (response.success && response.data) {
        const msgIndex = messages.value.findIndex((m) => m.id === assistantMessageId)
        if (msgIndex !== -1) {
          messages.value[msgIndex] = {
            ...messages.value[msgIndex],
            content: response.data.content,
            is_streaming: false
          }
        }
        ElMessage.success('代码生成完成')
      } else {
        throw new Error('代码生成失败')
      }
    } catch (error) {
      console.error('Coding error:', error)
      const msgIndex = messages.value.findIndex((m) => m.id === assistantMessageId)
      if (msgIndex !== -1) {
        messages.value[msgIndex] = {
          ...messages.value[msgIndex],
          content: '代码生成失败，请重试',
          is_streaming: false
        }
      }
      ElMessage.error('代码生成失败')
    } finally {
      sending.value = false
    }
  }

  // 直接调用图像生成专项API
  async function _sendImageGenerationSkill(
    conversationId: number,
    content: string,
    options?: SkillOptions
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
      is_streaming: true
    }
    messages.value.push(assistantMessage)

    try {
      const response = await request.post('/api/v1/skills/direct/image/generate', {
        prompt: content,
        size: options?.size || '1024*1024',
        n: options?.n || 1,
        model_mode: 'fast'
      }) as any

      if (response.success && response.data) {
        const urls = response.data.urls || []
        const resultText = `已生成 ${urls.length} 张图片：\n\n` + 
          urls.map((url: string) => `![生成的图片](${url})`).join('\n\n')
        
        const msgIndex = messages.value.findIndex((m) => m.id === assistantMessageId)
        if (msgIndex !== -1) {
          messages.value[msgIndex] = {
            ...messages.value[msgIndex],
            content: resultText,
            is_streaming: false
          }
        }
        ElMessage.success(`成功生成 ${urls.length} 张图片`)
      } else {
        throw new Error('图像生成失败')
      }
    } catch (error) {
      console.error('Image generation error:', error)
      const msgIndex = messages.value.findIndex((m) => m.id === assistantMessageId)
      if (msgIndex !== -1) {
        messages.value[msgIndex] = {
          ...messages.value[msgIndex],
          content: '图像生成失败，请重试',
          is_streaming: false
        }
      }
      ElMessage.error('图像生成失败')
    } finally {
      sending.value = false
    }
  }

  function _sendMessageInternal(
    conversationId: number,
    content: string,
    images: string[] | undefined,
    skill: string | null,
    skillOptions: SkillOptions | null
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
      is_streaming: true
    }
    messages.value.push(assistantMessage)

    const url = 'http://localhost:8000/api/v1/chat/send'
    
    const body: any = {
      conversation_id: conversationId,
      content: content,
      stream: true,
      model_type: 'general',
      is_expert: false,
      images: images || null
    }

    if (skill) {
      body.skill = skill
      body.skill_options = skillOptions || {}
    }

    const xhr = new XMLHttpRequest()
    let receivedLength = 0
    
    xhr.open('POST', url, true)
    xhr.setRequestHeader('Content-Type', 'application/json')
    xhr.setRequestHeader('Authorization', `Bearer ${localStorage.getItem('token')}`)
    
    xhr.onprogress = () => {
      // 检查 401 状态
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
      
      // 处理可能不完整的行（以\n结尾的才是完整行）
      const lines = newData.split('\n')
      let newContent = ''
      
      lines.forEach((line, index) => {
        // 最后一行可能不完整，除非它以\n结尾
        if (index === lines.length - 1 && !newData.endsWith('\n')) {
          // 将不完整行加回到 receivedLength，下次处理
          receivedLength -= line.length
          return
        }
        
        if (line.startsWith('data: ')) {
          const data = line.slice(6)
          if (data === '[DONE]') {
            console.log('[SSE] Received DONE signal')
            return
          }
          // 解码 JSON 数据
          try {
            const decoded = JSON.parse(data)
            newContent += decoded
            console.log('[SSE] data chunk:', decoded.substring(0, 50) + (decoded.length > 50 ? '...' : ''))
          } catch (e) {
            console.error('[SSE] JSON parse error:', e, 'data:', data)
          }
        }
      })
      
      if (newContent) {
        console.log('[SSE] Adding content:', newContent.substring(0, 50) + (newContent.length > 50 ? '...' : ''))
        const msgIndex = messages.value.findIndex((m) => m.id === assistantMessageId)
        if (msgIndex !== -1) {
          const currentContent = messages.value[msgIndex].content
          messages.value[msgIndex] = {
            ...messages.value[msgIndex],
            content: currentContent + newContent,
            is_streaming: true
          }
          console.log('[SSE] Message updated, new length:', messages.value[msgIndex].content.length)
        } else {
          console.error('[SSE] Message not found for id:', assistantMessageId)
        }
      }
    }
    
    xhr.onload = () => {
      console.log('[SSE] Request completed, status:', xhr.status)
      
      // 处理 401 未授权
      if (xhr.status === 401) {
        localStorage.removeItem('token')
        sending.value = false
        // 跳转到登录页
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
          is_streaming: false
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
    
    xhr.timeout = 120000 // 2分钟超时
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

  return {
    messages,
    loading,
    sending,
    fetchConversationHistory,
    sendMessage,
    sendMessageWithSkill,
    regenerateMessage,
    clearMessages
  }
})
