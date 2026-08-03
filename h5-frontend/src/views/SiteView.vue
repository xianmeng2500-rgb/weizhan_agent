<template>
  <div class="site-page" :class="'tpl-' + site.template" :style="bgStyle">
    <!-- KV 区域 -->
    <div class="kv-area" v-if="site.kv_image">
      <img :src="site.kv_image" class="kv-image" mode="widthFix" />
    </div>

    <!-- 九宫格/按钮布局 -->
    <div class="content-area">
      <!-- 九宫格 -->
      <div v-if="site.layout === 'grid'" class="grid-layout">
        <div
          v-for="m in modules"
          :key="m.id"
          class="grid-item"
          @click="handleClick(m)"
        >
          <img v-if="m.icon" :src="m.icon" class="grid-icon" />
          <div v-else class="grid-icon-placeholder">{{ m.title.charAt(0) }}</div>
          <div class="grid-title">{{ m.title }}</div>
        </div>
      </div>

      <!-- 按钮布局 -->
      <div v-else class="button-layout">
        <div
          v-for="m in modules"
          :key="m.id"
          class="button-item"
          @click="handleClick(m)"
        >
          <img v-if="m.icon" :src="m.icon" class="button-icon" />
          <span class="button-text">{{ m.title }}</span>
          <span class="arrow">›</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { showToast } from 'vant'
import api from '@/api'

const route = useRoute()
const router = useRouter()
const code = route.params.code as string

const site = ref<any>({})
const modules = ref<any[]>([])

const bgStyle = computed(() => {
  if (site.value.background_color) {
    return { background: site.value.background_color }
  }
  return {}
})

async function loadSite() {
  try {
    site.value = await api.get(`/p/sites/${code}`)
  } catch (err: any) {
    if (err.response?.status === 403) {
      showToast(err.response.data?.detail || '微站不可访问')
    } else if (err.response?.status === 404) {
      showToast('微站不存在')
    }
    return
  }
  // 上报访问
  api.post(`/p/sites/${code}/access`, {}).catch(() => {})
  // 加载模块
  await loadModules()
}

async function loadModules() {
  try {
    modules.value = await api.get(`/p/sites/${code}/modules`)
  } catch (err: any) {
    // 401 表示需要登录
    if (err.response?.status === 401 && err.response?.data?.detail === '请先登录') {
      router.push(`/s/${code}/login`)
    }
  }
}

function handleClick(m: any) {
  // 上报点击
  api.post(`/p/sites/${code}/click`, { module_id: m.id }).catch(() => {})

  if (m.content_type === 'external_link' && m.external_url) {
    window.location.href = m.external_url
  } else {
    router.push(`/s/${code}/module/${m.id}`)
  }
}

onMounted(loadSite)
</script>

<style scoped>
.site-page { min-height: 100vh; overflow-x: hidden; }

/* 模板背景 */
.tpl-classic { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); }
.tpl-dark { background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%); }
.tpl-festive { background: linear-gradient(135deg, #c0392b 0%, #e74c3c 100%); }

.kv-area { width: 100%; }
.kv-image { width: 100%; display: block; }

.content-area { padding: 16px; }

/* 九宫格 */
.grid-layout {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 12px;
}
.grid-item {
  display: flex; flex-direction: column; align-items: center; justify-content: center;
  padding: 16px 8px; border-radius: 12px; cursor: pointer;
  background: rgba(255,255,255,0.95); transition: transform 0.2s;
}
.tpl-dark .grid-item { background: rgba(255,255,255,0.1); }
.tpl-festive .grid-item { background: rgba(255,255,255,0.95); border: 2px solid #ffd700; }
.grid-item:active { transform: scale(0.96); }
.grid-icon { width: 48px; height: 48px; object-fit: cover; border-radius: 8px; }
.grid-icon-placeholder {
  width: 48px; height: 48px; border-radius: 8px;
  display: flex; align-items: center; justify-content: center;
  background: linear-gradient(135deg, #667eea, #764ba2); color: #fff;
  font-size: 20px; font-weight: bold;
}
.grid-title { margin-top: 8px; font-size: 12px; text-align: center; color: #333; }
.tpl-dark .grid-title { color: #fff; }

/* 按钮布局 */
.button-layout { display: flex; flex-direction: column; gap: 10px; }
.button-item {
  display: flex; align-items: center; padding: 14px 16px;
  background: rgba(255,255,255,0.95); border-radius: 10px; cursor: pointer;
  transition: transform 0.2s;
}
.tpl-dark .button-item { background: rgba(255,255,255,0.1); }
.tpl-festive .button-item { background: rgba(255,255,255,0.95); border: 1px solid #ffd700; }
.button-item:active { transform: scale(0.98); }
.button-icon { width: 36px; height: 36px; object-fit: cover; border-radius: 8px; }
.button-text { flex: 1; margin-left: 12px; font-size: 15px; color: #333; }
.tpl-dark .button-text { color: #fff; }
.arrow { color: #ccc; font-size: 20px; }
</style>
