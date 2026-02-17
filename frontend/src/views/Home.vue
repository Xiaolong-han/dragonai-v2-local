<template>
  <div class="chat-page">
    <template v-if="conversationStore.currentConversationId">
      <div class="chat-container">
        <div class="chat-content">
          <ChatMessageList :messages="chatStore.messages" :loading="chatStore.loading" />
        </div>
        <div class="chat-input-wrapper">
          <ChatInput
            :loading="chatStore.sending"
            :disabled="chatStore.loading"
            @send="handleSendMessage"
          />
        </div>
      </div>
    </template>
    <WelcomeView @send-message="handleQuickMessage" />
  </div>
</template>

<script setup>
import { watch, onMounted } from 'vue'
import { useConversationStore } from '@/stores/conversation'
import { useChatStore } from '@/stores/chat'
import ChatMessageList from '@/components/ChatMessageList.vue'
import ChatInput from '@/components/ChatInput.vue'
import WelcomeView from '@/components/WelcomeView.vue'

const conversationStore = useConversationStore()
const chatStore = useChatStore()

watch(
  () => conversationStore.currentConversationId,
  async (newId) => {
    if (newId) {
      await chatStore.fetchConversationHistory(newId)
    } else {
      chatStore.clearMessages()
    }
  },
  { immediate: true }
)

async function handleSendMessage(content) {
  if (!conversationStore.currentConversationId) return
  await chatStore.sendMessage(conversationStore.currentConversationId, content)
}

async function handleQuickMessage(content) {
  const title = content.length > 20 ? content.slice(0, 20) + '...' : content
  const conversation = await conversationStore.createConversation({ title })
  if (conversation) {
    await chatStore.sendMessage(conversation.id, content)
  }
}

onMounted(() => {
  if (conversationStore.currentConversationId) {
    chatStore.fetchConversationHistory(conversationStore.currentConversationId)
  }
})
</script>

<style scoped>
.chat-page {
  display: flex;
  flex-direction: column;
  height: 100%;
  background: #f7f8fa;
}

.chat-container {
  display: flex;
  flex-direction: column;
  height: 100%;
  max-width: 900px;
  width: 100%;
  margin: 0 auto;
}

.chat-content {
  flex: 1;
  overflow: hidden;
  padding: 0 24px;
}

.chat-input-wrapper {
  padding: 16px 24px 24px;
}
</style>
