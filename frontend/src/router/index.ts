import { createRouter, createWebHistory, type RouteRecordRaw } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { useConversationStore } from '@/stores/conversation'

const routes: RouteRecordRaw[] = [
  {
    path: '/login',
    name: 'Login',
    component: () => import('../views/Login.vue'),
    meta: { requiresAuth: false }
  },
  {
    path: '/register',
    name: 'Register',
    component: () => import('../views/Register.vue'),
    meta: { requiresAuth: false }
  },
  {
    path: '/',
    redirect: '/chat'
  },
  {
    path: '/chat',
    component: () => import('../layouts/MainLayout.vue'),
    meta: { requiresAuth: true },
    children: [
      {
        path: '',
        name: 'Chat',
        component: () => import('../views/Chat.vue')
      },
      {
        path: ':conversationId',
        name: 'ChatConversation',
        component: () => import('../views/Chat.vue'),
        props: true
      }
    ]
  },
  {
    path: '/image-generation',
    component: () => import('../layouts/MainLayout.vue'),
    meta: { requiresAuth: true },
    children: [
      {
        path: '',
        name: 'ImageGeneration',
        component: () => import('../views/ImageGeneration.vue')
      }
    ]
  },
  {
    path: '/image-editing',
    component: () => import('../layouts/MainLayout.vue'),
    meta: { requiresAuth: true },
    children: [
      {
        path: '',
        name: 'ImageEditing',
        component: () => import('../views/ImageEditing.vue')
      }
    ]
  },
  {
    path: '/coding',
    component: () => import('../layouts/MainLayout.vue'),
    meta: { requiresAuth: true },
    children: [
      {
        path: '',
        name: 'Coding',
        component: () => import('../views/Coding.vue')
      }
    ]
  },
  {
    path: '/translation',
    component: () => import('../layouts/MainLayout.vue'),
    meta: { requiresAuth: true },
    children: [
      {
        path: '',
        name: 'Translation',
        component: () => import('../views/Translation.vue')
      }
    ]
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

router.beforeEach(async (to, _from, next) => {
  const authStore = useAuthStore()
  const conversationStore = useConversationStore()
  
  if (to.meta.requiresAuth && !authStore.isLoggedIn) {
    next('/login')
  } else if ((to.path === '/login' || to.path === '/register') && authStore.isLoggedIn) {
    next('/chat')
  } else {
    if (authStore.isLoggedIn && !authStore.user) {
      try {
        await authStore.fetchUserInfo()
      } catch (error) {
        authStore.logout()
        next('/login')
        return
      }
    }
    
    if (authStore.isLoggedIn && conversationStore.conversations.length === 0) {
      try {
        await conversationStore.fetchConversations()
      } catch (error) {
        console.error('Failed to fetch conversations:', error)
      }
    }
    
    next()
  }
})

export default router
