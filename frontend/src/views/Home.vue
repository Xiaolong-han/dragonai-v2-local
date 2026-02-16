<template>
  <div class="chat-page">
    <template v-if="currentConversationId">
      <ChatMessageList :messages="chatStore.messages" :loading="chatStore.loading" />
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
import { useConversationStore } from '@/stores/conversation'
import { useChatStore } from '@/stores/chat'
import ChatMessageList from '@/components/ChatMessageList.vue'
import ChatInput from '@/components/ChatInput.vue'

const conversationStore = useConversationStore()
const chatStore = useChatStore()

const currentConversationId = conversationStore.currentConversationId

watch(
  currentConversationId,
  async (newId) => {
    if (newId) {
      await chatStore.fetchConversationHistory(newId)
    } else {
      chatStore.clearMessages()
    }
  },
  { immediate: true }
)

async function handleSendMessage(content: string) {
  if (!currentConversationId.value) return
  await chatStore.sendMessage(currentConversationId.value, content)
}

onMounted(() => {
  if (currentConversationId.value) {
    chatStore.fetchConversationHistory(currentConversationId.value)
  }
})
</script>

<style scoped>
.chat-page {
  display: flex;
  flex-direction: column;
  height: 100%;
  background: #f5f7fa;
}

.no-conversation {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
}
</style>
