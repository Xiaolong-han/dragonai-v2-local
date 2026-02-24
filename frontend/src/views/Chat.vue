<template>
  <div class="chat-page">
    <template v-if="currentConversationId">
      <ChatMessageList 
        :messages="chatStore.messages" 
        :loading="chatStore.loading" 
        :conversation-id="currentConversationId"
        @regenerate="handleRegenerate"
      />
      <ChatInput
        :loading="chatStore.sending"
        :disabled="chatStore.loading"
        @send="handleSendMessage"
      />
    </template>
    <div v-else class="no-conversation">
      <el-empty description="请选择或创建一个对话" />
    </div>
  </div>
</template>

<script setup lang="ts">
import { watch, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { storeToRefs } from 'pinia'
import { useConversationStore } from '@/stores/conversation'
import { useChatStore } from '@/stores/chat'
import ChatMessageList from '@/components/ChatMessageList.vue'
import ChatInput from '@/components/ChatInput.vue'

interface Props {
  conversationId?: string
}

const props = defineProps<Props>()
const route = useRoute()
const router = useRouter()
const conversationStore = useConversationStore()
const chatStore = useChatStore()

const { currentConversationId } = storeToRefs(conversationStore)

// 从 URL 参数或 props 获取会话 ID
function getConversationIdFromRoute(): number | null {
  const id = props.conversationId || route.params.conversationId
  if (id) {
    const numId = parseInt(id as string, 10)
    return isNaN(numId) ? null : numId
  }
  return null
}

// 同步 URL 参数到 store
async function syncConversationFromRoute() {
  const routeId = getConversationIdFromRoute()
  if (routeId && routeId !== currentConversationId.value) {
    conversationStore.selectConversation(routeId)
  }
}

// 监听路由参数变化
watch(
  () => route.params.conversationId,
  async (newId) => {
    if (newId) {
      const numId = parseInt(newId as string, 10)
      if (!isNaN(numId) && numId !== currentConversationId.value) {
        conversationStore.selectConversation(numId)
      }
    } else {
      conversationStore.currentConversationId = null
      chatStore.clearMessages()
    }
  },
  { immediate: true }
)

// 监听当前会话 ID 变化，更新 URL
watch(
  currentConversationId,
  async (newId) => {
    if (newId) {
      // 更新 URL，但不触发导航
      const currentRouteId = route.params.conversationId
      if (currentRouteId !== String(newId)) {
        router.replace(`/chat/${newId}`)
      }
      await chatStore.fetchConversationHistory(newId)
    } else {
      chatStore.clearMessages()
      // 如果没有会话 ID，重定向到 /chat
      if (route.params.conversationId) {
        router.replace('/chat')
      }
    }
  }
)

function handleSendMessage(content: string, files: any[], tool?: string, options?: any, settings?: { isExpert: boolean; enableThinking: boolean }) {
  if (!currentConversationId.value) return
  
  const imageUrls = files.filter((url): url is string => typeof url === 'string')
  
  if (tool) {
    chatStore.sendMessageWithTool(currentConversationId.value, content, tool, options, imageUrls, settings)
  } else {
    chatStore.sendMessage(currentConversationId.value, content, imageUrls, settings)
  }
}

function handleRegenerate(messageIndex: number) {
  if (!currentConversationId.value) return
  chatStore.regenerateMessage(currentConversationId.value, messageIndex)
}

onMounted(() => {
  syncConversationFromRoute()
})
</script>

<style scoped>
.chat-page {
  display: flex;
  flex-direction: column;
  height: 100vh;
  background: var(--bg-secondary);
  overflow: hidden;
}

.chat-page > *:first-child {
  flex: 1;
  overflow-y: auto;
  min-height: 0;
}

.no-conversation {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
}
</style>
