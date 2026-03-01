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
        :loading="isCurrentSending"
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
import { watch, onMounted, computed } from 'vue'
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

const isCurrentSending = computed(() => {
  return currentConversationId.value ? chatStore.isSending(currentConversationId.value) : false
})

function getConversationIdFromRoute(): number | null {
  const id = props.conversationId || route.params.conversationId
  if (id) {
    const numId = parseInt(id as string, 10)
    return isNaN(numId) ? null : numId
  }
  return null
}

// 同步路由到状态
async function syncFromRoute() {
  const routeId = getConversationIdFromRoute()
  if (routeId) {
    if (routeId !== currentConversationId.value) {
      conversationStore.selectConversation(routeId)
    }
    if (routeId !== chatStore.currentConversationId) {
      chatStore.setCurrentConversation(routeId)
      await chatStore.fetchConversationHistory(routeId)
    }
  } else {
    conversationStore.currentConversationId = null
    chatStore.setCurrentConversation(null)
  }
}

// 监听路由变化
watch(
  () => route.params.conversationId,
  syncFromRoute,
  { immediate: true }
)

// 监听当前会话ID变化（处理新建会话的情况）
watch(
  currentConversationId,
  async (newId) => {
    if (newId) {
      // 同步URL
      const currentRouteId = route.params.conversationId
      if (currentRouteId !== String(newId)) {
        router.replace(`/chat/${newId}`)
      }
      // 确保chatStore也同步
      if (newId !== chatStore.currentConversationId) {
        chatStore.setCurrentConversation(newId)
        await chatStore.fetchConversationHistory(newId)
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
  syncFromRoute()
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
