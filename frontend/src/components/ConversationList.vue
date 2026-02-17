<template>
  <div class="conversation-list">
    <div class="conversations">
      <div 
        v-for="conversation in sortedConversations" 
        :key="conversation.id" 
        class="conversation-item"
        @click="handleSelectConversation(conversation.id)"
      >
        <div :class="['conversation-content', { active: currentConversationId === conversation.id }]">
          <el-icon class="chat-icon"><ChatDotRound /></el-icon>
          <span v-if="conversation.is_pinned" class="pin-icon">
            <el-icon><Top /></el-icon>
          </span>
          <span class="title-text">{{ conversation.title }}</span>
        </div>
        
        <div class="conversation-actions" @click.stop>
          <el-button
            v-if="!conversation.is_pinned"
            class="action-btn"
            link
            @click="handlePinConversation(conversation.id)"
            title="置顶"
          >
            <el-icon><Top /></el-icon>
          </el-button>
          <el-button
            v-else
            class="action-btn"
            link
            @click="handleUnpinConversation(conversation.id)"
            title="取消置顶"
          >
            <el-icon><Bottom /></el-icon>
          </el-button>
          <el-button
            class="action-btn"
            link
            @click="handleEditConversation(conversation)"
            title="重命名"
          >
            <el-icon><Edit /></el-icon>
          </el-button>
          <el-button
            class="action-btn"
            link
            @click="handleDeleteConversation(conversation.id)"
            title="删除"
          >
            <el-icon><Delete /></el-icon>
          </el-button>
        </div>
      </div>
    </div>

    <el-dialog v-model="editDialogVisible" title="重命名会话" width="400px">
      <el-input
        v-model="editTitle"
        placeholder="请输入新的会话标题"
        maxlength="200"
        show-word-limit
      />
      <template #footer>
        <el-button @click="editDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleSaveEdit">保存</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="deleteDialogVisible" title="确认删除" width="400px">
      <p>确定要删除这个会话吗？此操作不可恢复。</p>
      <template #footer>
        <el-button @click="deleteDialogVisible = false">取消</el-button>
        <el-button type="danger" @click="handleConfirmDelete">删除</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { ChatDotRound, Edit, Delete, Top, Bottom } from '@element-plus/icons-vue'
import { useConversationStore } from '@/stores/conversation'

const router = useRouter()
const conversationStore = useConversationStore()

// 使用 computed 保持响应性
const sortedConversations = computed(() => conversationStore.sortedConversations)
const currentConversationId = computed(() => conversationStore.currentConversationId)
const { fetchConversations, pinConversation, unpinConversation, selectConversation, updateConversation, deleteConversation } = conversationStore

const editDialogVisible = ref(false)
const deleteDialogVisible = ref(false)
const editingId = ref<number | null>(null)
const editTitle = ref('')
const deletingId = ref<number | null>(null)

onMounted(() => {
  fetchConversations()
})

function handleSelectConversation(id: number) {
  selectConversation(id)
  // 导航到新的 URL
  router.push(`/chat/${id}`)
}

async function handlePinConversation(id: number) {
  try {
    await pinConversation(id)
    ElMessage.success('会话已置顶')
  } catch (error) {
    ElMessage.error('置顶失败')
  }
}

async function handleUnpinConversation(id: number) {
  try {
    await unpinConversation(id)
    ElMessage.success('已取消置顶')
  } catch (error) {
    ElMessage.error('取消置顶失败')
  }
}

function handleEditConversation(conversation: any) {
  editingId.value = conversation.id
  editTitle.value = conversation.title
  editDialogVisible.value = true
}

async function handleSaveEdit() {
  if (!editingId.value || !editTitle.value.trim()) return
  
  try {
    await updateConversation(editingId.value, { title: editTitle.value.trim() })
    ElMessage.success('会话重命名成功')
    editDialogVisible.value = false
  } catch (error) {
    ElMessage.error('重命名失败')
  }
}

function handleDeleteConversation(id: number) {
  deletingId.value = id
  deleteDialogVisible.value = true
}

async function handleConfirmDelete() {
  if (!deletingId.value) return
  
  try {
    await deleteConversation(deletingId.value)
    ElMessage.success('会话删除成功')
    deleteDialogVisible.value = false
  } catch (error) {
    ElMessage.error('删除失败')
  }
}
</script>

<style scoped>
.conversation-list {
  height: 100%;
  display: flex;
  flex-direction: column;
}

.conversations {
  flex: 1;
  overflow-y: auto;
  padding-right: 4px;
}

.conversations::-webkit-scrollbar {
  width: 6px;
}

.conversations::-webkit-scrollbar-track {
  background: transparent;
}

.conversations::-webkit-scrollbar-thumb {
  background: #d9d9d9;
  border-radius: 3px;
}

.conversations::-webkit-scrollbar-thumb:hover {
  background: #bfbfbf;
}

.conversation-item {
  display: flex;
  align-items: center;
  padding: 10px 12px;
  margin-bottom: 4px;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s;
  position: relative;
}

.conversation-item:hover {
  background: #f5f7fa;
}

.conversation-content {
  flex: 1;
  display: flex;
  align-items: center;
  gap: 8px;
  overflow: hidden;
  padding: 4px 0;
}

.conversation-content.active {
  background: #e6f4ff;
  border-radius: 6px;
  padding: 8px 12px;
  margin: -4px -4px;
}

.conversation-content.active .chat-icon {
  color: #1677ff;
}

.chat-icon {
  flex-shrink: 0;
  color: #8c8c8c;
  font-size: 16px;
}

.pin-icon {
  flex-shrink: 0;
  color: #faad14;
  font-size: 14px;
}

.title-text {
  flex: 1;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  font-size: 14px;
  color: #1f2329;
}

.conversation-content.active .title-text {
  color: #1677ff;
  font-weight: 500;
}

.conversation-actions {
  display: flex;
  gap: 2px;
  opacity: 0;
  transition: opacity 0.2s;
  padding-left: 4px;
}

.conversation-item:hover .conversation-actions {
  opacity: 1;
}

.action-btn {
  padding: 4px;
  color: #8c8c8c;
}

.action-btn:hover {
  color: #1677ff;
}
</style>
