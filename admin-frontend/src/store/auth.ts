import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

export const useAuthStore = defineStore('auth', () => {
  const token = ref(localStorage.getItem('token') || '')
  const nickname = ref(localStorage.getItem('nickname') || '')

  const isLoggedIn = computed(() => !!token.value)

  function setAuth(t: string, name: string) {
    token.value = t
    nickname.value = name
    localStorage.setItem('token', t)
    localStorage.setItem('nickname', name)
  }

  function clear() {
    token.value = ''
    nickname.value = ''
    localStorage.removeItem('token')
    localStorage.removeItem('nickname')
  }

  return { token, nickname, isLoggedIn, setAuth, clear }
})
