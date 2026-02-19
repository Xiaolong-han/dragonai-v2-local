import { defineStore } from 'pinia'
import request from '@/utils/request'

export interface ImageGenerateParams {
  prompt: string
  size?: string
  n?: number
  is_expert?: boolean
}

export interface ImageEditParams {
  image_path: string
  prompt: string
  size?: string
  is_expert?: boolean
}

export interface CodeAssistParams {
  prompt: string
  is_expert?: boolean
  temperature?: number
  max_tokens?: number
}

export interface TranslateParams {
  text: string
  target_lang: string
  source_lang?: string
  is_expert?: boolean
}

export interface ImageGenerateResponse {
  images: string[]
}

export interface ImageEditResponse {
  images: string[]
}

export interface CodeAssistResponse {
  content: string
  model_name: string
  thinking_content?: string
  reasoning_content?: string
}

export interface TranslateResponse {
  text: string
  source_lang?: string
  target_lang: string
  model_name: string
}

export const useSkillStore = defineStore('skill', () => {
  async function directImageGenerate(params: ImageGenerateParams): Promise<ImageGenerateResponse> {
    return await request.post('/api/v1/skills/image-generation', params)
  }

  async function directImageEdit(params: ImageEditParams): Promise<ImageEditResponse> {
    return await request.post('/api/v1/skills/image-editing', params)
  }

  async function directCodeAssist(params: CodeAssistParams): Promise<CodeAssistResponse> {
    return await request.post('/api/v1/skills/coding', params)
  }

  async function directTranslate(params: TranslateParams): Promise<TranslateResponse> {
    return await request.post('/api/v1/skills/translation', params)
  }

  return {
    directImageGenerate,
    directImageEdit,
    directCodeAssist,
    directTranslate
  }
})
