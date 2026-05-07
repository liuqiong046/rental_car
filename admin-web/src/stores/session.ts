import { defineStore } from 'pinia'

import type { AdminActor } from '../api/admin'

type SessionState = {
  token: string
  actor: AdminActor | null
}

const savedToken = localStorage.getItem('admin_token') || ''
const savedActor = localStorage.getItem('admin_actor')

export const useSessionStore = defineStore('session', {
  state: (): SessionState => ({
    token: savedToken,
    actor: savedActor ? (JSON.parse(savedActor) as AdminActor) : null
  }),
  actions: {
    setSession(token: string, actor: AdminActor) {
      this.token = token
      this.actor = actor
      localStorage.setItem('admin_token', token)
      localStorage.setItem('admin_actor', JSON.stringify(actor))
    },
    clearSession() {
      this.token = ''
      this.actor = null
      localStorage.removeItem('admin_token')
      localStorage.removeItem('admin_actor')
    }
  }
})

