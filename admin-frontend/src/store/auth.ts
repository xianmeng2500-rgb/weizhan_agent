import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import api from '@/api'

export const useAuthStore = defineStore('auth', () => {
  const token = ref(localStorage.getItem('token') || '')
  const nickname = ref(localStorage.getItem('nickname') || '')
  const role = ref(localStorage.getItem('role') || '')

  const isLoggedIn = computed(() => !!token.value)
  // 可管理后台账号的角色（超级管理员 / 管理员）
  const canManageAccounts = computed(() => role.value === 'super_admin' || role.value === 'admin')
  const isSuperAdmin = computed(() => role.value === 'super_admin')

  function setAuth(t: string, name: string, r?: string) {
    token.value = t
    nickname.value = name
    if (r !== undefined) role.value = r
    localStorage.setItem('token', t)
    localStorage.setItem('nickname', name)
    if (r !== undefined) localStorage.setItem('role', r)
  }

  function clear() {
    token.value = ''
    nickname.value = ''
    role.value = ''
    localStorage.removeItem('token')
    localStorage.removeItem('nickname')
    localStorage.removeItem('role')
  }

  // 拉取当前用户信息（含角色），用于刷新后恢复角色
  async function fetchMe() {
    try {
      const res: any = await api.get('/auth/me')
      nickname.value = res.nickname || nickname.value
      role.value = res.role || role.value
      localStorage.setItem('nickname', nickname.value)
      if (role.value) localStorage.setItem('role', role.value)
    } catch {
      // 忽略
    }
  }

  return { token, nickname, role, isLoggedIn, canManageAccounts, isSuperAdmin, setAuth, clear, fetchMe }
})
