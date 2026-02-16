<template>
  <div class="model-selector">
    <el-dropdown trigger="click" @command="handleSelectModel">
      <el-button class="model-button">
        <el-icon><Setting /></el-icon>
        <span>{{ currentModel?.name || '选择模型' }}</span>
        <el-icon><ArrowDown /></el-icon>
      </el-button>
      <template #dropdown>
        <el-dropdown-menu>
          <div class="model-group">
            <div class="group-title">快速模型</div>
            <el-dropdown-item
              v-for="model in fastModels"
              :key="model.name"
              :command="model"
              :class="{ 'is-selected': currentModel?.name === model.name }"
            >
              {{ model.name }}
            </el-dropdown-item>
          </div>
          <div class="model-group">
            <div class="group-title">专家模型</div>
            <el-dropdown-item
              v-for="model in expertModels"
              :key="model.name"
              :command="model"
              :class="{ 'is-selected': currentModel?.name === model.name }"
            >
              {{ model.name }}
            </el-dropdown-item>
          </div>
        </el-dropdown-menu>
      </template>
    </el-dropdown>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { Setting, ArrowDown } from '@element-plus/icons-vue'
import request from '@/utils/request'

interface ChatModel {
  name: string
  is_expert: boolean
}

interface Props {
  modelValue?: ChatModel | null
}

interface Emits {
  (e: 'update:modelValue', value: ChatModel | null): void
  (e: 'change', value: ChatModel | null): void
}

const props = withDefaults(defineProps<Props>(), {
  modelValue: null
})

const emit = defineEmits<Emits>()

const models = ref<ChatModel[]>([])
const loading = ref(false)

const currentModel = computed(() => props.modelValue || (fastModels.value[0] || null))

const fastModels = computed(() => models.value.filter(m => !m.is_expert))
const expertModels = computed(() => models.value.filter(m => m.is_expert))

async function fetchModels() {
  loading.value = true
  try {
    const data = await request.get('/api/v1/models/chat')
    models.value = data as ChatModel[]
    if (!props.modelValue && models.value.length > 0) {
      const defaultModel = fastModels.value[0] || models.value[0]
      emit('update:modelValue', defaultModel)
      emit('change', defaultModel)
    }
  } catch (error) {
    console.error('Failed to fetch models:', error)
  } finally {
    loading.value = false
  }
}

function handleSelectModel(model: ChatModel) {
  emit('update:modelValue', model)
  emit('change', model)
}

onMounted(() => {
  fetchModels()
})
</script>

<style scoped>
.model-selector {
  display: inline-flex;
}

.model-button {
  display: flex;
  align-items: center;
  gap: 6px;
  height: 36px;
  padding: 0 12px;
  border-radius: 8px;
  background: #f5f7fa;
  border: 1px solid #e4e7ed;
  color: #606266;
  font-size: 14px;
  transition: all 0.2s;
}

.model-button:hover {
  background: #ecf5ff;
  border-color: #c6e2ff;
  color: #409eff;
}

.model-group {
  padding: 4px 0;
}

.group-title {
  padding: 8px 12px;
  font-size: 12px;
  color: #909399;
  font-weight: 500;
}

.el-dropdown-menu {
  padding: 4px;
}

.is-selected {
  color: #409eff;
  font-weight: 500;
}
</style>
