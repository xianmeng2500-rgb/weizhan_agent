<template>
  <div class="template-select">
    <el-card shadow="never" class="table-card">
      <template #header>
        <div class="card-header">
          <span class="card-title">
            <el-icon><Files /></el-icon>
            选择微站模板
          </span>
          <el-button :icon="ArrowLeft" @click="$router.back()">返回</el-button>
        </div>
      </template>

      <div v-loading="loading" class="template-grid">
        <!-- 空白创建 -->
        <div class="template-card blank-card" :class="{ selected: !selectedId }" @click="selectTemplate(null)">
          <div class="card-preview">
            <el-icon :size="40" class="blank-icon"><Plus /></el-icon>
          </div>
          <div class="card-info">
            <div class="info-title">空白创建</div>
            <div class="info-desc">不使用模板，从零开始自由配置微站外观与模块</div>
          </div>
        </div>

        <!-- 模板卡片 -->
        <div
          v-for="tpl in templates"
          :key="tpl.id"
          class="template-card"
          :class="{ selected: selectedId === tpl.id }"
          @click="selectTemplate(tpl.id)"
        >
          <div class="card-preview" :class="'tpl-' + tpl.template_key">
            <img v-if="tpl.preview_image" :src="tpl.preview_image" class="preview-img" />
            <div v-else class="preview-placeholder">
              <span class="style-name">{{ templateKeyMap[tpl.template_key] || tpl.template_key }}</span>
            </div>
            <div v-if="selectedId === tpl.id" class="selected-badge">
              <el-icon><Check /></el-icon>
            </div>
          </div>
          <div class="card-info">
            <div class="info-title">{{ tpl.name }}</div>
            <div class="info-desc">{{ tpl.description || '暂无描述' }}</div>
            <div class="info-tags">
              <el-tag size="small" type="info">{{ templateKeyMap[tpl.template_key] || tpl.template_key }}</el-tag>
              <el-tag size="small" type="info">{{ layoutMap[tpl.layout] || tpl.layout }}</el-tag>
              <el-tag v-if="moduleCount(tpl) > 0" size="small" type="info">预置模块 {{ moduleCount(tpl) }} 个</el-tag>
            </div>
            <div class="card-actions" @click.stop>
              <el-button size="small" :icon="ZoomIn" @click="openPreview(tpl)">预览</el-button>
              <el-button size="small" type="primary" plain @click="useTemplate(tpl)">使用该模板</el-button>
            </div>
          </div>
        </div>

        <el-empty v-if="!loading && templates.length === 0" description="暂无可用模板，可选择空白创建" class="grid-empty" />
      </div>

      <div class="footer-actions">
        <el-button type="primary" size="large" :disabled="selectedId === undefined" @click="goCreate">
          {{ selectedId === null ? '空白创建微站' : selectedId ? '使用该模板创建' : '请选择模板' }}
        </el-button>
      </div>
    </el-card>

    <!-- 模板大图预览弹窗 -->
    <el-dialog v-model="previewVisible" :title="previewTpl?.name || '模板预览'" width="390px" align-center destroy-on-close>
      <div v-if="previewTpl" class="preview-dialog-body">
        <div class="device-frame" :class="'tpl-' + previewTpl.template_key" :style="previewBgStyle">
          <div class="device-notch"></div>
          <div class="status-bar">
            <span class="status-time">9:41</span>
            <div class="status-icons">
              <span class="signal"></span>
              <span class="wifi"></span>
              <span class="battery"></span>
            </div>
          </div>
          <div v-if="previewTpl.background_image" class="bg-layer">
            <img :src="previewTpl.background_image" class="bg-image" alt="" />
          </div>
          <!-- 自由拖拽布局 -->
          <div v-if="previewTpl.layout === 'free'" class="free-layout">
            <div
              v-for="(m, i) in activeModules"
              :key="i"
              class="preview-btn free-btn icon-only"
              :class="{ 'has-height': m.height != null }"
              :style="freeBtnStyle(m)"
            >
              <div class="free-btn-inner">
                <img v-if="m.icon" :src="m.icon" class="btn-icon" />
                <div v-else class="btn-icon-placeholder">{{ (m.title || '?').charAt(0) }}</div>
              </div>
            </div>
          </div>
          <!-- 页面标题装饰 -->
          <div v-if="previewTpl.title_config?.enabled" class="site-title-deco" :style="previewTitleStyle">
            {{ previewTitleText }}
          </div>
          <div class="device-screen">
            <div class="kv-area" v-if="previewTpl.kv_image">
              <img :src="previewTpl.kv_image" class="kv-image" />
            </div>
            <!-- 九宫格布局 -->
            <div v-if="previewTpl.layout === 'grid'" class="content-area">
              <div class="grid-layout">
                <div v-for="(m, i) in activeModules" :key="i" class="preview-btn grid-item">
                  <img v-if="m.icon" :src="m.icon" class="grid-icon" />
                  <div v-else class="grid-icon-placeholder">{{ (m.title || '?').charAt(0) }}</div>
                  <div class="grid-title">{{ m.title }}</div>
                </div>
              </div>
            </div>
            <!-- 按钮列表布局 -->
            <div v-else-if="previewTpl.layout === 'button'" class="content-area">
              <div class="button-layout">
                <div v-for="(m, i) in activeModules" :key="i" class="preview-btn button-item">
                  <img v-if="m.icon" :src="m.icon" class="btn-icon" />
                  <div v-else class="btn-icon-placeholder">{{ (m.title || '?').charAt(0) }}</div>
                  <span class="btn-text">{{ m.title }}</span>
                  <span class="btn-arrow">›</span>
                </div>
              </div>
            </div>
            <!-- 空状态 -->
            <div v-if="activeModules.length === 0" class="empty-tip">
              <el-icon size="36"><Files /></el-icon>
              <div>该模板暂无预置模块</div>
            </div>
          </div>
        </div>
        <div class="preview-meta">
          <el-tag size="small" type="info">{{ templateKeyMap[previewTpl.template_key] || previewTpl.template_key }}</el-tag>
          <el-tag size="small" type="info">{{ layoutMap[previewTpl.layout] || previewTpl.layout }}</el-tag>
          <el-tag v-if="activeModules.length > 0" size="small" type="info">预置模块 {{ activeModules.length }} 个</el-tag>
          <el-tag v-if="previewTpl.title_config?.enabled" size="small" type="warning">含标题装饰</el-tag>
        </div>
      </div>
      <template #footer>
        <el-button @click="previewVisible = false">关闭</el-button>
        <el-button type="primary" @click="usePreviewTemplate">使用该模板创建</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { Files, Plus, Check, ArrowLeft, ZoomIn } from '@element-plus/icons-vue'
import api from '@/api'

const router = useRouter()

const templates = ref<any[]>([])
const loading = ref(false)
// undefined = 未选择; null = 空白创建; number = 模板ID
const selectedId = ref<number | null | undefined>(undefined)

const templateKeyMap: Record<string, string> = { default: '默认', classic: '经典蓝紫', dark: '暗夜科技', festive: '节日红金' }
const layoutMap: Record<string, string> = { grid: '九宫格', button: '按钮列表', free: '自由拖拽' }

const TITLE_FONT_STACKS: Record<string, string> = {
  sans: "'PingFang SC', 'Helvetica Neue', 'Microsoft YaHei', sans-serif",
  song: "'Songti SC', 'SimSun', serif",
  kai: "'Kaiti SC', 'STKaiti', 'KaiTi', serif",
  fangsong: "'Fangsong SC', 'STFangsong', 'FangSong', serif",
}

function moduleCount(tpl: any): number {
  return Array.isArray(tpl.modules_config) ? tpl.modules_config.length : 0
}

// --- 模板预览弹窗 ---
const previewVisible = ref(false)
const previewTpl = ref<any>(null)

const activeModules = computed<any[]>(() => {
  const list = previewTpl.value?.modules_config
  return Array.isArray(list) ? list.filter((m: any) => m.is_active !== false) : []
})

const previewBgStyle = computed(() => {
  if (previewTpl.value?.background_color) {
    return { background: previewTpl.value.background_color }
  }
  return {}
})

const previewTitleText = computed(() => previewTpl.value?.title_config?.text || previewTpl.value?.name || '微站标题')
const previewTitleStyle = computed(() => {
  const t = previewTpl.value?.title_config || {}
  return {
    position: 'absolute',
    left: (t.position_x ?? 5) + '%',
    top: (t.position_y ?? 5) + '%',
    maxWidth: (t.max_width ?? 80) + '%',
    fontFamily: TITLE_FONT_STACKS[t.font] || TITLE_FONT_STACKS.sans,
    color: t.color || '#333333',
    fontSize: (t.size || 20) + 'px',
    fontWeight: t.bold ? '700' : '400',
  } as Record<string, string>
})

function freeBtnStyle(m: any) {
  const style: Record<string, string> = {
    left: (m.position_x ?? 5) + '%',
    top: (m.position_y ?? 10) + '%',
  }
  if (m.width != null) style.width = m.width + '%'
  if (m.height != null) style.height = m.height + '%'
  if (m.border_radius != null) style.borderRadius = m.border_radius + 'px'
  if (m.bg_color) style.background = m.bg_color
  if (m.font_color) style.color = m.font_color
  return style
}

function openPreview(tpl: any) {
  previewTpl.value = tpl
  previewVisible.value = true
}

function usePreviewTemplate() {
  if (previewTpl.value) {
    router.push({ path: '/sites/create', query: { template_id: String(previewTpl.value.id) } })
  }
}

function useTemplate(tpl: any) {
  router.push({ path: '/sites/create', query: { template_id: String(tpl.id) } })
}

function selectTemplate(id: number | null) {
  selectedId.value = id
}

function goCreate() {
  if (selectedId.value === undefined) return
  if (selectedId.value === null) {
    router.push('/sites/create')
  } else {
    router.push({ path: '/sites/create', query: { template_id: String(selectedId.value) } })
  }
}

onMounted(async () => {
  loading.value = true
  try {
    const res: any = await api.get('/templates/all')
    templates.value = res || []
  } finally {
    loading.value = false
  }
})
</script>

<style scoped>
.table-card :deep(.el-card__body) {
  padding: 16px;
}
.card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
}
.card-title {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 15px;
  font-weight: 600;
  color: #303133;
}
.card-title .el-icon {
  color: var(--el-color-primary);
}

.template-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(240px, 1fr));
  gap: 16px;
  min-height: 200px;
}
.grid-empty {
  grid-column: 1 / -1;
}
.template-card {
  border: 2px solid #ebeef5;
  border-radius: 8px;
  overflow: hidden;
  transition: all 0.2s;
  background: #fff;
  cursor: pointer;
}
.template-card:hover {
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
}
.template-card.selected {
  border-color: var(--el-color-primary);
  box-shadow: 0 0 0 3px rgba(64, 158, 255, 0.15);
}
.card-preview {
  position: relative;
  height: 150px;
  overflow: hidden;
}
.preview-img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  display: block;
}
.preview-placeholder {
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
}
.tpl-default .preview-placeholder {
  background: #ffffff;
}
.tpl-classic .preview-placeholder {
  background: linear-gradient(135deg, #c5cef5 0%, #c8bde0 100%);
}
.tpl-dark .preview-placeholder {
  background: linear-gradient(135deg, #4a4a68 0%, #3e3e5a 100%);
}
.tpl-festive .preview-placeholder {
  background: linear-gradient(135deg, #e8c5c5 0%, #e0b8b8 100%);
}
.style-name {
  font-size: 15px;
  font-weight: 600;
  color: rgba(0, 0, 0, 0.45);
}
.tpl-dark .style-name {
  color: rgba(255, 255, 255, 0.75);
}
.selected-badge {
  position: absolute;
  top: 8px;
  right: 8px;
  width: 24px;
  height: 24px;
  border-radius: 50%;
  background: var(--el-color-primary);
  color: #fff;
  display: flex;
  align-items: center;
  justify-content: center;
}
.card-info {
  padding: 12px;
}
.info-title {
  font-size: 15px;
  font-weight: 600;
  color: #303133;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.info-desc {
  font-size: 12px;
  color: #909399;
  margin-top: 4px;
  height: 32px;
  line-height: 16px;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}
.info-tags {
  margin-top: 8px;
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
}
.card-actions {
  margin-top: 10px;
  display: flex;
  gap: 8px;
}
.card-actions .el-button + .el-button {
  margin-left: 0;
}
.card-actions .el-button {
  flex: 1;
}
.blank-card .card-preview {
  display: flex;
  align-items: center;
  justify-content: center;
  background: #fafafa;
  border-bottom: 1px dashed #dcdfe6;
}
.blank-icon {
  color: #c0c4cc;
}
.footer-actions {
  margin-top: 20px;
  display: flex;
  justify-content: center;
}
.footer-actions .el-button {
  min-width: 220px;
}

/* ===== 预览弹窗内手机样式（与模板编辑器预览一致） ===== */
.preview-dialog-body {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 14px;
}
.device-frame {
  width: 300px;
  height: 585px;
  border: 9px solid #1a1a1a;
  border-radius: 34px;
  overflow: hidden;
  position: relative;
  --status-area: 22px;
  background:
    linear-gradient(to bottom, #1a1a1a 0, #1a1a1a var(--status-area), transparent var(--status-area)),
    linear-gradient(135deg, #c5cef5 0%, #c8bde0 100%);
  box-shadow:
    0 0 0 2px #2a2a2a,
    0 16px 40px rgba(0, 0, 0, 0.25);
}
.device-frame.tpl-default {
  background:
    linear-gradient(to bottom, #1a1a1a 0, #1a1a1a var(--status-area), transparent var(--status-area)),
    #ffffff;
}
.device-frame.tpl-classic {
  background:
    linear-gradient(to bottom, #1a1a1a 0, #1a1a1a var(--status-area), transparent var(--status-area)),
    linear-gradient(135deg, #c5cef5 0%, #c8bde0 100%);
}
.device-frame.tpl-dark {
  background:
    linear-gradient(to bottom, #1a1a1a 0, #1a1a1a var(--status-area), transparent var(--status-area)),
    linear-gradient(135deg, #4a4a68 0%, #3e3e5a 100%);
}
.device-frame.tpl-festive {
  background:
    linear-gradient(to bottom, #1a1a1a 0, #1a1a1a var(--status-area), transparent var(--status-area)),
    linear-gradient(135deg, #e8c5c5 0%, #e0b8b8 100%);
}
.device-notch {
  position: absolute;
  top: 0;
  left: 50%;
  transform: translateX(-50%);
  width: 92px;
  height: 22px;
  background: #1a1a1a;
  border-bottom-left-radius: 11px;
  border-bottom-right-radius: 11px;
  z-index: 20;
}
.device-screen {
  width: 100%;
  height: 100%;
  overflow-y: auto;
  overflow-x: hidden;
  position: relative;
  z-index: 1;
  box-sizing: border-box;
  padding-top: var(--status-area);
}
.bg-layer {
  position: absolute;
  top: var(--status-area);
  left: 0;
  right: 0;
  bottom: 0;
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
.status-bar {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 22px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 16px;
  color: rgba(255, 255, 255, 0.95);
  font-size: 12px;
  font-weight: 600;
  z-index: 20;
  text-shadow: 0 1px 2px rgba(0, 0, 0, 0.5);
  pointer-events: none;
}
.status-icons {
  display: flex;
  align-items: center;
  gap: 5px;
}
.signal {
  width: 14px;
  height: 10px;
  background-image:
    linear-gradient(to top, rgba(255, 255, 255, 0.9) 3px, transparent 3px),
    linear-gradient(to top, rgba(255, 255, 255, 0.9) 6px, transparent 6px),
    linear-gradient(to top, rgba(255, 255, 255, 0.9) 9px, transparent 9px);
  background-size: 3.5px 100%;
  background-position: 0 100%, 5px 100%, 10px 100%;
  background-repeat: no-repeat;
}
.wifi {
  width: 12px;
  height: 10px;
  border: 2px solid rgba(255, 255, 255, 0.9);
  border-radius: 50% 50% 0 0;
  border-bottom: none;
}
.battery {
  width: 18px;
  height: 8px;
  border: 1px solid rgba(255, 255, 255, 0.9);
  border-radius: 2px;
  position: relative;
  background: rgba(255, 255, 255, 0.8);
}
.battery::after {
  content: '';
  position: absolute;
  right: -3px;
  top: 2px;
  width: 2px;
  height: 4px;
  background: rgba(255, 255, 255, 0.9);
  border-radius: 0 1px 1px 0;
}
.kv-area {
  width: 100%;
  position: relative;
  z-index: 1;
}
.kv-image {
  width: 100%;
  display: block;
}
.site-title-deco {
  line-height: 1.4;
  word-break: break-all;
  z-index: 999;
  pointer-events: none;
}
.content-area {
  padding: 16px;
  position: relative;
  z-index: 1;
}
.free-layout {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  z-index: 2;
  pointer-events: none;
}
.preview-btn {
  background: rgba(255, 255, 255, 0.95);
  border-radius: 10px;
}
.free-btn {
  position: absolute;
  display: flex;
  align-items: center;
  padding: 8px 14px;
  gap: 6px;
  white-space: nowrap;
  box-sizing: border-box;
}
/* 自由布局纯图标模式 */
.free-btn.icon-only {
  padding: 0;
  width: 44px;
  height: 44px;
  background: transparent;
  justify-content: center;
  align-items: center;
}
.free-btn.icon-only .free-btn-inner {
  display: block;
  width: 100%;
  height: 100%;
}
.free-btn.icon-only .btn-icon,
.free-btn.icon-only .btn-icon-placeholder {
  width: 100%;
  height: 100%;
  object-fit: contain;
  border-radius: inherit;
  font-size: 20px;
}
.free-btn-inner {
  display: flex;
  align-items: center;
  gap: 6px;
  width: 100%;
  min-width: 0;
}
.free-btn-inner .btn-icon,
.free-btn-inner .btn-icon-placeholder {
  order: 0;
  flex-shrink: 0;
}
.free-btn-inner .btn-text {
  order: 1;
  flex: 1;
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
}
.free-btn-inner .btn-arrow {
  order: 2;
  flex-shrink: 0;
}
.free-btn-inner.icon-left {
  flex-direction: row;
  justify-content: flex-start;
}
.free-btn-inner.icon-right {
  flex-direction: row;
}
.free-btn-inner.icon-right .btn-icon,
.free-btn-inner.icon-right .btn-icon-placeholder {
  order: 2;
}
.free-btn-inner.icon-right .btn-text {
  order: 0;
}
.free-btn-inner.icon-right .btn-arrow {
  order: 1;
}
.free-btn-inner.icon-top,
.free-btn-inner.icon-bottom {
  flex-direction: column;
  justify-content: center;
}
.free-btn-inner.icon-top .btn-icon,
.free-btn-inner.icon-top .btn-icon-placeholder {
  order: 0;
}
.free-btn-inner.icon-top .btn-text {
  order: 1;
  flex: 0 0 auto;
}
.free-btn-inner.icon-bottom .btn-icon,
.free-btn-inner.icon-bottom .btn-icon-placeholder {
  order: 1;
}
.free-btn-inner.icon-bottom .btn-text {
  order: 0;
  flex: 0 0 auto;
}
.free-btn-inner.icon-top .btn-arrow,
.free-btn-inner.icon-bottom .btn-arrow {
  position: absolute;
  right: 10px;
  top: 50%;
  transform: translateY(-50%);
}
.free-btn-inner.align-left {
  justify-content: flex-start;
}
.free-btn-inner.align-center {
  justify-content: center;
}
.free-btn-inner.align-right {
  justify-content: flex-end;
}
.free-btn-inner.icon-top.align-left,
.free-btn-inner.icon-bottom.align-left {
  align-items: flex-start;
}
.free-btn-inner.icon-top.align-center,
.free-btn-inner.icon-bottom.align-center {
  align-items: center;
}
.free-btn-inner.icon-top.align-right,
.free-btn-inner.icon-bottom.align-right {
  align-items: flex-end;
}
.free-btn.has-height .free-btn-inner {
  height: 100%;
}
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
}
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
}
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
.tpl-dark .grid-title {
  color: #fff;
}
.btn-icon {
  width: 36px;
  height: 36px;
  object-fit: cover;
  border-radius: 8px;
  flex-shrink: 0;
}
.btn-icon-placeholder {
  width: 36px;
  height: 36px;
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
.tpl-dark .btn-text {
  color: #fff;
}
.tpl-dark .preview-btn {
  background: rgba(255, 255, 255, 0.1);
}
.tpl-festive .preview-btn {
  border: 1px solid #ffd700;
}
.btn-arrow {
  color: #ccc;
  font-size: 18px;
  flex-shrink: 0;
}
.empty-tip {
  position: absolute;
  top: 55%;
  left: 50%;
  transform: translate(-50%, -50%);
  color: rgba(255, 255, 255, 0.75);
  font-size: 13px;
  text-align: center;
  z-index: 3;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
}
.tpl-default .empty-tip,
.tpl-classic .empty-tip {
  color: rgba(0, 0, 0, 0.35);
}
.preview-meta {
  display: flex;
  flex-wrap: wrap;
  justify-content: center;
  gap: 6px;
}
</style>
