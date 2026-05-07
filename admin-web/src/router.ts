import { createRouter, createWebHistory } from 'vue-router'

import { useSessionStore } from './stores/session'
import AdminShell from './views/AdminShell.vue'
import LoginView from './views/LoginView.vue'

export const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/login', name: 'login', component: LoginView },
    { path: '/', name: 'admin', component: AdminShell, meta: { requiresAuth: true } }
  ]
})

router.beforeEach((to) => {
  const session = useSessionStore()
  if (to.meta.requiresAuth && !session.token) {
    return { name: 'login' }
  }
  if (to.name === 'login' && session.token) {
    return { name: 'admin' }
  }
  return true
})

