import { defineStore } from 'pinia'
import axios from 'axios'

export interface ImageGenerateParams {
  prompt: string
  size: string
  n: number
  model_mode: 'fast' | 'expert'
}

export interface ImageEditParams {
  image_url: string
  prompt: string
  model_mode: 'fast' | 'expert'
}

export interface CodeAssistParams {
  prompt: string
  language: string
  model_mode: 'fast' | 'expert'
  stream?: boolean
}

export interface TranslateParams {
  text: string
  target_lang: string
  source_lang?: string
  model_mode: 'fast' | 'expert'
}

export const useSkillStore = defineStore('skill', () => {
  /**
   * 直接调用图像生成API（不经过主聊天Agent）
   */
  async function directImageGenerate(params: ImageGenerateParams) {
    const response = await axios.post('/api/v1/skills/direct/image/generate', params)
    return response.data.data
  }

  /**
   * 直接调用图像编辑API（不经过主聊天Agent）
   */
  async function directImageEdit(params: ImageEditParams) {
    const response = await axios.post('/api/v1/skills/direct/image/edit', params)
    return response.data.data
  }

  /**
   * 直接调用编程协助API（不经过主聊天Agent）
   */
  async function directCodeAssist(params: CodeAssistParams) {
    if (params.stream) {
      const response = await fetch('/api/v1/skills/direct/code/assist', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(params)
      })
      return response.body
    } else {
      const response = await axios.post('/api/v1/skills/direct/code/assist', params)
      return response.data.data
    }
  }

  /**
   * 直接调用翻译API（不经过主聊天Agent）
   */
  async function directTranslate(params: TranslateParams) {
    const response = await axios.post('/api/v1/skills/direct/translate', params)
    return response.data.data
  }

  return {
    directImageGenerate,
    directImageEdit,
    directCodeAssist,
    directTranslate
  }
})
