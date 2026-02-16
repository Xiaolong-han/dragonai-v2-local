import { createRouter, createWebHistory, RouteRecordRaw } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const routes: Array<RouteRecordRaw> = [
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
    component: () => import('../layouts/MainLayout.vue'),
    meta: { requiresAuth: true },
    children: [
      {
        path: '',
        name: 'Home',
        component: () => import('../views/Home.vue')
      },
      {
        path: 'image-generation',
        name: 'ImageGeneration',
        component: () => import('../views/ImageGeneration.vue')
      },
      {
        path: 'image-editing',
        name: 'ImageEditing',
        component: () => import('../views/ImageEditing.vue')
      },
      {
        path: 'coding',
        name: 'Coding',
        component: () => import('../views/Coding.vue')
      },
      {
        path: 'translation',
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

router.beforeEach(async (to, from, next) => {
  const authStore = useAuthStore()
  
  if (to.meta.requiresAuth && !authStore.isLoggedIn) {
    next('/login')
  } else if ((to.path === '/login' || to.path === '/register') && authStore.isLoggedIn) {
    next('/')
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
    next()
  }
})

export default router