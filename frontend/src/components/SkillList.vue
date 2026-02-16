<template>
  <div class="skill-list">
    <div class="skill-header">
      <h3>AI 技能</h3>
    </div>
    <div class="skill-grid">
      <div
        v-for="skill in skills"
        :key="skill.name"
        class="skill-card"
        @click="handleSkillClick(skill)"
      >
        <div class="skill-icon">
          <el-icon :size="32">
            <component :is="getSkillIcon(skill.name)" />
          </el-icon>
        </div>
        <div class="skill-info">
          <h4>{{ skill.name }}</h4>
          <p>{{ skill.description }}</p>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import {
  Picture,
  Edit,
  Document,
  Operation,
  Position,
  Guide,
  Connection
} from '@element-plus/icons-vue'
import request from '@/utils/request'

interface Skill {
  name: string
  description: string
}

const router = useRouter()
const skills = ref<Skill[]>([])
const loading = ref(false)

const skillRoutes: Record<string, string> = {
  '图像生成': '/image-generation',
  '图像编辑': '/image-editing',
  '编程': '/coding',
  '翻译': '/translation'
}

const skillIcons: Record<string, any> = {
  '图像生成': Picture,
  '图像编辑': Edit,
  '编程': Operation,
  '翻译': Guide
}

function getSkillIcon(name: string) {
  return skillIcons[name] || Document
}

async function fetchSkills() {
  loading.value = true
  try {
    const data = await request.get('/api/v1/skills')
    skills.value = data as Skill[]
  } catch (error) {
    console.error('Failed to fetch skills:', error)
  } finally {
    loading.value = false
  }
}

function handleSkillClick(skill: Skill) {
  const route = skillRoutes[skill.name]
  if (route) {
    router.push(route)
  }
}

onMounted(() => {
  fetchSkills()
})
</script>

<style scoped>
.skill-list {
  padding: 20px;
}

.skill-header {
  margin-bottom: 20px;
}

.skill-header h3 {
  font-size: 18px;
  font-weight: 600;
  color: #303133;
  margin: 0;
}

.skill-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 16px;
}

.skill-card {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 16px;
  background: white;
  border-radius: 12px;
  border: 1px solid #e4e7ed;
  cursor: pointer;
  transition: all 0.2s;
}

.skill-card:hover {
  border-color: #409eff;
  box-shadow: 0 4px 12px rgba(64, 158, 255, 0.15);
  transform: translateY(-2px);
}

.skill-icon {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 56px;
  height: 56px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-radius: 12px;
  color: white;
  flex-shrink: 0;
}

.skill-info {
  flex: 1;
  min-width: 0;
}

.skill-info h4 {
  font-size: 16px;
  font-weight: 600;
  color: #303133;
  margin: 0 0 4px 0;
}

.skill-info p {
  font-size: 13px;
  color: #909399;
  margin: 0;
  line-height: 1.4;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
</style>
