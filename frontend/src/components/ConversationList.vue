<template>
  <div class="conversation-list">
    <button class="new-chat-btn" @click="handleNewConversation">
      <span>+ 新建会话</span>
    </button>

    <div class="conversations">
      <div v-for="conversation in sortedConversations" :key="conversation.id" class="conversation-item">
        <div
          :class="['conversation-title', { active: currentConversationId === conversation.id }]"
          @click="handleSelectConversation(conversation.id)"
        >
          <span v-if="conversation.is_pinned" class="pin-icon">📌</span>
          <span class="title-text">{{ conversation.title }}</span>
        </div>

        <div class="conversation-actions">
          <button
            v-if="!conversation.is_pinned"
            class="action-btn"
            @click.stop="handlePinConversation(conversation.id)"
            title="置顶"
          >
            📌
          </button>
          <button
            v-else
            class="action-btn"
            @click.stop="handleUnpinConversation(conversation.id)"
            title="取消置顶"
          >
            📌
          </button>
          <button
            class="action-btn"
            @click.stop="handleEditConversation(conversation)"
            title="重命名"
          >
            ✏️
          </button>
          <button
            class="action-btn"
            @click.stop="handleDeleteConversation(conversation.id)"
            title="删除"
          >
            🗑️
          </button>
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
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { useConversationStore } from '@/stores/conversation'

const conversationStore = useConversationStore()
const {
  sortedConversations,
  currentConversationId,
  loading,
  fetchConversations,
  createConversation,
  updateConversation,
  deleteConversation,
  pinConversation,
  unpinConversation,
  selectConversation
} = conversationStore

const editDialogVisible = ref(false)
const deleteDialogVisible = ref(false)
const editingId = ref<number | null>(null)
const editTitle = ref('')
const deletingId = ref<number | null>(null)

onMounted(() => {
  fetchConversations()
})

async function handleNewConversation() {
  try {
    await createConversation({ title: '新会话' })
    ElMessage.success('会话创建成功')
  } catch (error) {
    ElMessage.error('创建会话失败')
  }
}

function handleSelectConversation(id: number) {
  selectConversation(id)
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
  padding: 16px;
}

.new-chat-btn {
  width: 100%;
  padding: 12px;
  margin-bottom: 16px;
  background: #409eff;
  color: white;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  font-size: 14px;
  transition: background 0.2s;
}

.new-chat-btn:hover {
  background: #66b1ff;
}

.conversations {
  flex: 1;
  overflow-y: auto;
}

.conversation-item {
  display: flex;
  align-items: center;
  padding: 8px 12px;
  margin-bottom: 4px;
  border-radius: 6px;
  cursor: pointer;
  transition: background 0.2s;
}

.conversation-item:hover {
  background: #f5f7fa;
}

.conversation-title {
  flex: 1;
  display: flex;
  align-items: center;
  gap: 8px;
  overflow: hidden;
}

.conversation-title.active {
  background: #ecf5ff;
  border-radius: 4px;
  padding: 4px 8px;
  margin: -4px -8px;
}

.pin-icon {
  flex-shrink: 0;
}

.title-text {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  font-size: 14px;
}

.conversation-actions {
  display: flex;
  gap: 4px;
  opacity: 0;
  transition: opacity 0.2s;
}

.conversation-item:hover .conversation-actions {
  opacity: 1;
}

.action-btn {
  padding: 4px 8px;
  background: none;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 14px;
  transition: background 0.2s;
}

.action-btn:hover {
  background: #e4e7ed;
}
</style>
