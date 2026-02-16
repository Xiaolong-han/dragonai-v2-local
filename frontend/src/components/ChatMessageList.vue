<template>
  <div class="message-list" ref="messageListRef">
    <el-empty v-if="messages.length === 0 && !loading" description="暂无消息，开始对话吧！" />
    <div v-else-if="loading" class="loading-container">
      <el-icon class="is-loading" :size="40"><Loading /></el-icon>
    </div>
    <div v-else class="messages-container">
      <ChatMessageBubble 
        v-for="(message, index) in messages" 
        :key="message.id" 
        :message="message" 
        :message-index="index" 
        :conversation-id="conversationId" 
        @regenerate="handleRegenerate(index)"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, watch, nextTick, onMounted } from 'vue'
import { Loading } from '@element-plus/icons-vue'
import ChatMessageBubble from './ChatMessageBubble.vue'
import type { ChatMessage } from '@/stores/chat'

interface Props {
  messages: ChatMessage[]
  loading: boolean
  conversationId?: number
}

const props = defineProps<Props>()
const emit = defineEmits<{
  regenerate: [index: number]
}>()
const messageListRef = ref<HTMLElement | null>(null)

function scrollToBottom() {
  nextTick(() => {
    if (messageListRef.value) {
      messageListRef.value.scrollTop = messageListRef.value.scrollHeight
    }
  })
}

function handleRegenerate(index: number) {
  emit('regenerate', index)
}

watch(
  () => props.messages,
  () => {
    scrollToBottom()
  },
  { deep: true }
)

onMounted(() => {
  scrollToBottom()
})
</script>

<style scoped>
.message-list {
  flex: 1;
  overflow-y: auto;
  padding: 20px 24px;
  display: flex;
  flex-direction: column;
}

.loading-container {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
}

.loading-container .el-icon {
  color: #409eff;
}

.messages-container {
  display: flex;
  flex-direction: column;
  gap: 8px;
}
</style>
