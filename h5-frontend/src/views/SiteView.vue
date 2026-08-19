<template>
  <div class="site-page" :class="'tpl-' + (site.template || 'default')" :style="pageStyle">
    <!-- 背景图：铺满页面作为底层装饰（与后台预览一致：absolute + object-fit cover） -->
    <div v-if="site.background_image" class="bg-layer">
      <img :src="site.background_image" class="bg-image" alt="" />
    </div>

    <!-- KV 区域 -->
    <div class="kv-area" v-if="site.kv_image">
      <img :src="site.kv_image" class="kv-image" />
    </div>

    <!-- 自由拖拽布局 -->
    <div v-if="site.layout === 'free'" class="free-layout">
      <div
        v-for="m in modules"
        :key="m.id"
        class="free-btn"
        :class="{ 'has-height': m.height != null }"
        :style="freeBtnStyle(m)"
        @click="handleClick(m)"
      >
        <div class="free-btn-inner" :class="freeBtnClass(m)">
          <img v-if="m.icon" :src="m.icon" class="btn-icon" />
          <div v-else class="btn-icon-placeholder">{{ (m.title || '?').charAt(0) }}</div>
          <span class="btn-text">{{ m.title }}</span>
          <span v-if="m.show_arrow !== false" class="btn-arrow">›</span>
        </div>
      </div>
    </div>

    <!-- 九宫格 -->
    <div v-else-if="site.layout === 'grid'" class="content-area" :style="{ paddingTop: (site.grid_offset_y || 0) + '%' }">
      <div class="grid-layout">
        <div
          v-for="m in modules"
          :key="m.id"
          class="grid-item"
          @click="handleClick(m)"
        >
          <img v-if="m.icon" :src="m.icon" class="grid-icon" />
          <div v-else class="grid-icon-placeholder">{{ (m.title || '?').charAt(0) }}</div>
          <div class="grid-title">{{ m.title }}</div>
        </div>
      </div>
    </div>

    <!-- 按钮列表布局 -->
    <div v-else class="content-area" :style="{ paddingTop: (site.grid_offset_y || 0) + '%' }">
      <div class="button-layout">
        <div
          v-for="m in modules"
          :key="m.id"
          class="button-item"
          @click="handleClick(m)"
        >
          <img v-if="m.icon" :src="m.icon" class="btn-icon" />
          <div v-else class="btn-icon-placeholder">{{ (m.title || '?').charAt(0) }}</div>
          <span class="btn-text">{{ m.title }}</span>
          <span class="btn-arrow">›</span>
        </div>
      </div>
    </div>

    <button
      v-if="serviceConfig.enabled"
      class="service-float"
      type="button"
      aria-label="联系客服"
      @click="showServicePanel = true"
    >
      <span class="service-icon" aria-hidden="true">
        <svg viewBox="0 0 24 24" focusable="false"><path d="M4 13v-1a8 8 0 0 1 16 0v1" /><path d="M5 12h2.5v6H5a1 1 0 0 1-1-1v-4a1 1 0 0 1 1-1Zm14 0h-2.5v6H19a1 1 0 0 0 1-1v-4a1 1 0 0 0-1-1Z" /><path d="M16.5 18c0 1.1-.9 2-2 2H12" /></svg>
      </span>
    </button>

    <van-action-sheet v-model:show="showServicePanel" title="活动咨询" round teleport="body">
      <div class="service-panel">
        <p v-if="serviceConfig.description" class="service-description">{{ serviceConfig.description }}</p>
        <p v-if="serviceConfig.service_hours" class="service-hours">服务时间：{{ serviceConfig.service_hours }}</p>
        <van-cell-group inset>
          <van-cell v-if="serviceConfig.phone" title="电话咨询" :label="serviceConfig.phone" is-link @click="callService" />
          <van-cell v-if="serviceConfig.wechat" title="客服微信" :label="serviceConfig.wechat" is-link @click="copyWechat" />
          <van-cell v-if="serviceConfig.link" title="在线咨询" label="打开客服链接" is-link @click="openServiceLink" />
          <van-cell v-if="serviceConfig.qrcode_url" title="客服二维码" label="查看并长按识别" is-link @click="showServiceQr = true" />
        </van-cell-group>
        <div v-if="!hasServiceChannel" class="service-empty">暂未配置客服联系方式</div>
      </div>
    </van-action-sheet>

    <van-image-preview v-model:show="showServiceQr" :images="serviceConfig.qrcode_url ? [serviceConfig.qrcode_url] : []" closeable teleport="body" />
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { showToast } from 'vant'
import api from '@/api'
import { useWeChatShare } from '@/composables/useWeChatShare'

const route = useRoute()
const router = useRouter()
const code = route.params.code as string
const { setup: setupWeChatShare } = useWeChatShare(code)

const site = ref<any>({})
const modules = ref<any[]>([])
const showServicePanel = ref(false)
const showServiceQr = ref(false)

const serviceConfig = computed(() => ({
  enabled: false,
  description: '',
  phone: '',
  wechat: '',
  link: '',
  qrcode_url: '',
  service_hours: '',
  ...(site.value.customer_service_config || {}),
}))

const hasServiceChannel = computed(() => Boolean(
  serviceConfig.value.phone || serviceConfig.value.wechat || serviceConfig.value.link || serviceConfig.value.qrcode_url,
))

// 后台预览参考尺寸（device-screen = 300x585）
const ADMIN_W = 300
const ADMIN_H = 585

// 页面背景色（仅当显式设置了 background_color 时覆盖模板渐变，与后台 previewBgStyle 一致）
const pageStyle = computed(() => {
  if (site.value.background_color) {
    return { background: site.value.background_color }
  }
  return {}
})

// 自由布局按钮样式 —— 基于后台预览参考尺寸缩放到实际屏幕
function freeBtnStyle(m: any): Record<string, string> {
  const screenW = window.innerWidth || ADMIN_W
  const screenH = window.innerHeight || ADMIN_H
  const sx = ADMIN_W / screenW
  const sy = ADMIN_H / screenH

  const style: Record<string, string> = {
    left: ((m.position_x ?? 5) * sx).toFixed(3) + '%',
    top: ((m.position_y ?? 10) * sy).toFixed(3) + '%',
  }
  if (m.width != null) style.width = (m.width * sx).toFixed(3) + '%'
  if (m.height != null) style.height = (m.height * sy).toFixed(3) + '%'
  if (m.border_radius != null) style.borderRadius = m.border_radius + 'px'
  if (m.bg_color) style.background = m.bg_color
  if (m.font_color) style.color = m.font_color
  return style
}

function freeBtnClass(m: any): string {
  const cls: string[] = []
  cls.push('icon-' + (m.icon_position || 'left'))
  if (m.content_align) cls.push('align-' + m.content_align)
  return cls.join(' ')
}

async function loadSite() {
  try {
    site.value = await api.get(`/p/sites/${code}`)
    if (site.value.need_login) {
      try {
        await api.get(`/p/sites/${code}/session`)
      } catch (err: any) {
        if (err.response?.status === 401) {
          router.replace(`/s/${code}/login`)
          return
        }
        throw err
      }
    }
  } catch (err: any) {
    if (err.response?.status === 403) {
      showToast(err.response.data?.detail || '微站不可访问')
    } else if (err.response?.status === 404) {
      showToast('微站不存在')
    } else {
      showToast(err.response?.data?.detail || '加载失败')
    }
    return
  }
  api.post(`/p/sites/${code}/access`, {}).catch(() => {})
  await loadModules()
  setupWeChatShare(site.value)
}

async function loadModules() {
  try {
    modules.value = await api.get(`/p/sites/${code}/modules`)
  } catch (err: any) {
    if (err.response?.status === 401 && err.response?.data?.detail === '请先登录') {
      router.push(`/s/${code}/login`)
    } else {
      showToast(err.response?.data?.detail || '模块加载失败')
    }
  }
}

async function copyWechat() {
  const value = serviceConfig.value.wechat
  try {
    await navigator.clipboard.writeText(value)
    showToast('客服微信已复制')
  } catch {
    showToast(`客服微信：${value}`)
  }
}

function callService() {
  window.location.href = `tel:${serviceConfig.value.phone}`
}

function openServiceLink() {
  const url = serviceConfig.value.link
  if (!url) return
  window.location.href = url
}

function handleClick(m: any) {
  api.post(`/p/sites/${code}/click`, { module_id: m.id }).catch(() => {})

  if (m.content_type === 'external_link' && m.external_url) {
    window.location.href = m.external_url
  } else if (m.content_type === 'registration_form') {
    router.push(`/s/${code}/form/${m.id}`)
  } else if (m.content_type === 'schedule') {
    router.push(`/s/${code}/schedule/${m.id}`)
  } else if (m.content_type === 'qrcode') {
    router.push(`/s/${code}/qrcode/${m.id}`)
  } else {
    router.push(`/s/${code}/module/${m.id}`)
  }
}

onMounted(loadSite)
</script>

<style scoped>
/* ====== 页面容器 ====== */
.site-page {
  min-height: 100vh;
  overflow-x: hidden;
  position: relative;
  box-sizing: border-box;
  /* 顶部安全区：内容从刘海/状态栏下方开始，与后台预览保持一致 */
  padding-top: env(safe-area-inset-top);
}

/* ====== 模板渐变 ====== */
.tpl-default { background: #ffffff; }
.tpl-classic { background: linear-gradient(135deg, #c5cef5 0%, #c8bde0 100%); }
.tpl-dark    { background: linear-gradient(135deg, #4a4a68 0%, #3e3e5a 100%); }
.tpl-festive { background: linear-gradient(135deg, #e8c5c5 0%, #e0b8b8 100%); }

/* ====== 背景图：铺满屏幕内容区域，不包含刘海/状态栏顶部安全区 ====== */
.bg-layer {
  position: fixed;
  top: env(safe-area-inset-top); left: 0;
  width: 100vw;
  height: calc(100vh - env(safe-area-inset-top));
  z-index: 0;
  overflow: hidden;
  line-height: 0;
}
.bg-image {
  width: 100%;
  height: 100%;
  object-fit: cover;
  display: block;
}

/* ====== KV 区域 ====== */
.kv-area {
  width: 100%;
  position: relative;
  z-index: 1;
}
.kv-image {
  width: 100%;
  display: block;
}

/* ====== 内容区域（九宫格 / 按钮列表） ====== */
.content-area {
  padding: 16px;
  position: relative;
  z-index: 1;
}

/* ====== 自由布局 ====== */
.free-layout {
  position: fixed;
  top: 0; left: 0;
  width: 100vw;
  height: 100vh;
  z-index: 2;
  pointer-events: none;
}
.free-btn {
  position: absolute;
  display: flex;
  align-items: center;
  padding: 8px 14px;
  gap: 6px;
  white-space: nowrap;
  background: rgba(255, 255, 255, 0.95);
  border-radius: 10px;
  cursor: pointer;
  box-sizing: border-box;
  pointer-events: auto;
}
.free-btn:active { transform: scale(0.96); }

/* 内部内容容器 */
.free-btn-inner {
  display: flex;
  align-items: center;
  gap: 6px;
  width: 100%;
  min-width: 0;
}
.free-btn-inner .btn-icon,
.free-btn-inner .btn-icon-placeholder { order: 0; flex-shrink: 0; }
.free-btn-inner .btn-text { order: 1; flex: 1; min-width: 0; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.free-btn-inner .btn-arrow { order: 2; flex-shrink: 0; }

/* 图标位置: 水平 */
.free-btn-inner.icon-left { flex-direction: row; justify-content: flex-start; }
.free-btn-inner.icon-right { flex-direction: row; }
.free-btn-inner.icon-right .btn-icon,
.free-btn-inner.icon-right .btn-icon-placeholder { order: 2; }
.free-btn-inner.icon-right .btn-text { order: 0; }
.free-btn-inner.icon-right .btn-arrow { order: 1; }

/* 图标位置: 垂直 */
.free-btn-inner.icon-top,
.free-btn-inner.icon-bottom {
  flex-direction: column;
  justify-content: center;
}
.free-btn-inner.icon-top .btn-icon,
.free-btn-inner.icon-top .btn-icon-placeholder { order: 0; }
.free-btn-inner.icon-top .btn-text { order: 1; flex: 0 0 auto; }
.free-btn-inner.icon-bottom .btn-icon,
.free-btn-inner.icon-bottom .btn-icon-placeholder { order: 1; }
.free-btn-inner.icon-bottom .btn-text { order: 0; flex: 0 0 auto; }
.free-btn-inner.icon-top .btn-arrow,
.free-btn-inner.icon-bottom .btn-arrow {
  position: absolute;
  right: 10px;
  top: 50%;
  transform: translateY(-50%);
}

/* 内容水平对齐 */
.free-btn-inner.align-left { justify-content: flex-start; }
.free-btn-inner.align-center { justify-content: center; }
.free-btn-inner.align-right { justify-content: flex-end; }
.free-btn-inner.icon-top.align-left,
.free-btn-inner.icon-bottom.align-left { align-items: flex-start; }
.free-btn-inner.icon-top.align-center,
.free-btn-inner.icon-bottom.align-center { align-items: center; }
.free-btn-inner.icon-top.align-right,
.free-btn-inner.icon-bottom.align-right { align-items: flex-end; }

/* 固定高度时内容垂直居中 */
.free-btn.has-height .free-btn-inner { height: 100%; }

/* ====== 按钮图标（自由布局用） ====== */
.btn-icon {
  width: 36px; height: 36px;
  object-fit: cover;
  border-radius: 8px;
  flex-shrink: 0;
}
.btn-icon-placeholder {
  width: 36px; height: 36px;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #667eea, #764ba2);
  color: #fff;
  font-size: 16px;
  font-weight: bold;
  flex-shrink: 0;
}
.btn-text {
  font-size: 14px;
  color: #333;
  flex: 1;
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.btn-arrow {
  color: #ccc;
  font-size: 18px;
  flex-shrink: 0;
}

/* ====== 按钮列表 ====== */
.button-layout {
  display: flex;
  flex-direction: column;
  gap: 10px;
}
.button-item {
  display: flex;
  align-items: center;
  padding: 14px 16px;
  gap: 10px;
  background: rgba(255, 255, 255, 0.95);
  border-radius: 10px;
  cursor: pointer;
  transition: transform 0.2s;
}
.button-item:active { transform: scale(0.98); }

/* ====== 九宫格 ====== */
.grid-layout {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 12px;
}
.grid-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 16px 8px;
  background: rgba(255, 255, 255, 0.95);
  border-radius: 10px;
  cursor: pointer;
  transition: transform 0.2s;
}
.grid-item:active { transform: scale(0.96); }
.grid-icon {
  width: 48px;
  height: 48px;
  object-fit: cover;
  border-radius: 8px;
}
.grid-icon-placeholder {
  width: 48px;
  height: 48px;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #667eea, #764ba2);
  color: #fff;
  font-size: 20px;
  font-weight: bold;
}
.grid-title {
  margin-top: 8px;
  font-size: 12px;
  text-align: center;
  color: #333;
}

/* ====== 暗色模板 ====== */
.tpl-dark .btn-text { color: #fff; }
.tpl-dark .grid-title { color: #fff; }
.tpl-dark .free-btn { background: rgba(255, 255, 255, 0.1); }
.tpl-dark .grid-item { background: rgba(255, 255, 255, 0.1); }
.tpl-dark .button-item { background: rgba(255, 255, 255, 0.1); }

/* ====== 节日模板 ====== */
.tpl-festive .free-btn { border: 1px solid #ffd700; }
.tpl-festive .grid-item { border: 1px solid #ffd700; }
.tpl-festive .button-item { border: 1px solid #ffd700; }

/* ====== 客服悬浮按钮 ====== */
.service-float {
  position: fixed;
  right: 18px;
  bottom: calc(22px + env(safe-area-inset-bottom));
  z-index: 20;
  display: flex;
  width: 44px;
  height: 44px;
  align-items: center;
  justify-content: center;
  padding: 0;
  border: 0;
  background: transparent;
  color: #5b5bd6;
}
.service-float:active { transform: scale(0.9); }
.service-icon { display: flex; width: 30px; height: 30px; }
.service-icon svg { width: 100%; height: 100%; fill: none; stroke: currentColor; stroke-width: 1.8; stroke-linecap: round; stroke-linejoin: round; }
.tpl-dark .service-float { color: #5dCAA5; }
.tpl-festive .service-float { color: #c0392b; }
.service-panel { padding: 8px 0 24px; }
.service-description { margin: 8px 24px; color: #323233; font-size: 14px; line-height: 1.6; }
.service-hours { margin: 8px 24px 14px; color: #969799; font-size: 12px; }
.service-empty { padding: 28px 0; color: #969799; text-align: center; font-size: 13px; }
</style>
