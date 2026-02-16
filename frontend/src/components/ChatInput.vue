<template>
  <div class="chat-input-container">
    <div class="attachments-wrapper" v-if="uploadedFiles.length > 0">
      <div
        v-for="file in uploadedFiles"
        :key="file.id"
        class="attachment-item"
      >
        <div class="attachment-preview">
          <img v-if="file.type.startsWith('image/')" :src="file.preview" alt="" />
          <el-icon v-else :size="32">
            <Document />
          </el-icon>
        </div>
        <div class="attachment-info">
          <span class="attachment-name">{{ file.name }}</span>
          <span class="attachment-size">{{ formatFileSize(file.size) }}</span>
        </div>
        <el-button
          type="danger"
          :icon="Close"
          circle
          size="small"
          @click="removeFile(file.id)"
        />
      </div>
    </div>
    <div class="input-wrapper">
      <div class="upload-actions">
        <el-upload
          ref="imageUploadRef"
          class="upload-item"
          :show-file-list="false"
          :before-upload="handleBeforeUploadImage"
          :http-request="handleUploadImage"
          accept="image/*"
        >
          <el-button :icon="Picture" circle size="small" />
        </el-upload>
        <el-upload
          ref="fileUploadRef"
          class="upload-item"
          :show-file-list="false"
          :before-upload="handleBeforeUploadFile"
          :http-request="handleUploadFile"
          accept=".pdf,.doc,.docx,.txt,.md"
        >
          <el-button :icon="Folder" circle size="small" />
        </el-upload>
      </div>
      <el-input
        v-model="inputValue"
        type="textarea"
        :rows="1"
        :autosize="{ minRows: 1, maxRows: 6 }"
        placeholder="请输入消息..."
        :disabled="disabled"
        @keydown="handleKeydown"
        class="chat-input"
      />
      <el-button
        type="primary"
        :icon="Promotion"
        :loading="loading"
        :disabled="disabled || (!inputValue.trim() && uploadedFiles.length === 0)"
        @click="handleSend"
        class="send-button"
      >
        发送
      </el-button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { Promotion, Picture, Folder, Close, Document } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import request from '@/utils/request'

interface UploadedFile {
  id: string
  file: File
  name: string
  type: string
  size: number
  preview: string
  url?: string
}

interface Props {
  loading?: boolean
  disabled?: boolean
}

interface Emits {
  (e: 'send', value: string, files: UploadedFile[]): void
}

const props = withDefaults(defineProps<Props>(), {
  loading: false,
  disabled: false
})

const emit = defineEmits<Emits>()
const inputValue = ref<string>('')
const uploadedFiles = ref<UploadedFile[]>([])
const imageUploadRef = ref()
const fileUploadRef = ref()

function generateId(): string {
  return Date.now().toString(36) + Math.random().toString(36).substr(2)
}

function formatFileSize(bytes: number): string {
  if (bytes === 0) return '0 B'
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i]
}

function handleBeforeUploadImage(file: File): boolean {
  const isImage = file.type.startsWith('image/')
  if (!isImage) {
    ElMessage.error('只能上传图片文件！')
    return false
  }
  const isLt10M = file.size / 1024 / 1024 < 10
  if (!isLt10M) {
    ElMessage.error('图片大小不能超过 10MB！')
    return false
  }
  return true
}

async function handleUploadImage(options: any) {
  const file = options.file
  const uploadedFile: UploadedFile = {
    id: generateId(),
    file,
    name: file.name,
    type: file.type,
    size: file.size,
    preview: URL.createObjectURL(file)
  }
  uploadedFiles.value.push(uploadedFile)
}

function handleBeforeUploadFile(file: File): boolean {
  const allowedTypes = ['.pdf', '.doc', '.docx', '.txt', '.md']
  const fileName = file.name.toLowerCase()
  const isValid = allowedTypes.some(type => fileName.endsWith(type))
  if (!isValid) {
    ElMessage.error('只能上传 PDF、Word、TXT 或 Markdown 文件！')
    return false
  }
  const isLt50M = file.size / 1024 / 1024 < 50
  if (!isLt50M) {
    ElMessage.error('文件大小不能超过 50MB！')
    return false
  }
  return true
}

async function handleUploadFile(options: any) {
  const file = options.file
  const uploadedFile: UploadedFile = {
    id: generateId(),
    file,
    name: file.name,
    type: file.type,
    size: file.size,
    preview: ''
  }
  uploadedFiles.value.push(uploadedFile)
}

function removeFile(id: string) {
  const index = uploadedFiles.value.findIndex(f => f.id === id)
  if (index > -1) {
    const file = uploadedFiles.value[index]
    if (file.preview) {
      URL.revokeObjectURL(file.preview)
    }
    uploadedFiles.value.splice(index, 1)
  }
}

function handleSend() {
  const value = inputValue.value.trim()
  if ((value || uploadedFiles.value.length > 0) && !props.loading && !props.disabled) {
    emit('send', value, [...uploadedFiles.value])
    inputValue.value = ''
    uploadedFiles.value.forEach(file => {
      if (file.preview) {
        URL.revokeObjectURL(file.preview)
      }
    })
    uploadedFiles.value = []
  }
}

function handleKeydown(event: KeyboardEvent) {
  if (event.key === 'Enter' && !event.shiftKey) {
    event.preventDefault()
    handleSend()
  }
}
</script>

<style scoped>
.chat-input-container {
  padding: 16px 24px 24px;
  background: white;
  border-top: 1px solid #e4e7ed;
}

.attachments-wrapper {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  max-width: 1200px;
  margin: 0 auto 12px;
  padding: 0 4px;
}

.attachment-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 8px 12px;
  background: #f5f7fa;
  border-radius: 8px;
  border: 1px solid #e4e7ed;
}

.attachment-preview {
  width: 40px;
  height: 40px;
  border-radius: 6px;
  overflow: hidden;
  display: flex;
  align-items: center;
  justify-content: center;
  background: white;
  border: 1px solid #e4e7ed;
  flex-shrink: 0;
}

.attachment-preview img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.attachment-info {
  display: flex;
  flex-direction: column;
  gap: 2px;
  min-width: 0;
}

.attachment-name {
  font-size: 13px;
  color: #303133;
  font-weight: 500;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  max-width: 150px;
}

.attachment-size {
  font-size: 11px;
  color: #909399;
}

.input-wrapper {
  display: flex;
  gap: 12px;
  align-items: flex-end;
  max-width: 1200px;
  margin: 0 auto;
}

.upload-actions {
  display: flex;
  gap: 8px;
  flex-shrink: 0;
}

.upload-item {
  display: flex;
}

.chat-input {
  flex: 1;
}

.chat-input :deep(.el-textarea__inner) {
  border-radius: 8px;
  resize: none;
  font-size: 15px;
  line-height: 1.5;
}

.send-button {
  height: 40px;
  padding: 0 24px;
  font-weight: 500;
}
</style>
