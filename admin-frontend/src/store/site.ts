import { defineStore } from 'pinia'
import { ref } from 'vue'
import api from '@/api'

export const useSiteStore = defineStore('site', () => {
  const currentSiteId = ref<number | null>(null)
  const currentSiteName = ref('')

  async function loadSite(id: number) {
    if (currentSiteId.value === id && currentSiteName.value) return
    currentSiteId.value = id
    currentSiteName.value = ''
    try {
      const res: any = await api.get(`/sites/${id}`)
      currentSiteName.value = res.name || ''
    } catch {
      // ignore
    }
  }

  function clear() {
    currentSiteId.value = null
    currentSiteName.value = ''
  }

  return { currentSiteId, currentSiteName, loadSite, clear }
})
