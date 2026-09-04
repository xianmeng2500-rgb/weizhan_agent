<template>
  <div class="file-attachment-page" :class="'tpl-' + siteTheme">
    <van-nav-bar
      :title="moduleTitle || '资料附件'"
      left-arrow
      @click-left="goBack"
      :style="navBarStyle"
    />

    <van-loading v-if="loading" class="page-loading" />

    <template v-else>
      <van-empty v-if="!files.length" description="暂无资料" />

      <div v-else class="groups">
        <!-- 图片分组 -->
        <div v-if="imageFiles.length" class="group">
          <div class="group-header">
            <span class="group-title">图片</span>
            <span class="group-count">{{ imageFiles.length }} 张</span>
          </div>
          <div class="image-grid">
            <div
              v-for="f in imageFiles"
              :key="f.id"
              class="image-item"
              @click="previewImage(f)"
            >
              <van-image
                :src="f.url"
                fit="cover"
                class="image-thumb"
                :show-loading="true"
              />
              <div class="image-title">{{ f.title || f.name }}</div>
            </div>
          </div>
        </div>

        <!-- 文档分组 -->
        <div v-if="docFiles.length" class="group">
          <div class="group-header">
            <span class="group-title">文档</span>
            <span class="group-count">{{ docFiles.length }} 份</span>
          </div>
          <van-cell-group inset class="doc-list">
            <van-cell
              v-for="f in docFiles"
              :key="f.id"
              center
              clickable
              :title="f.title || f.name"
              :label="`${f.ext.toUpperCase()} · ${formatSize(f.size)}`"
              @click="onDocClick(f)"
            >
              <template #icon>
                <div class="doc-icon" :class="`ext-${f.ext}`">{{ f.ext.toUpperCase() }}</div>
              </template>
              <template #right-icon>
                <van-icon name="arrow" />
              </template>
            </van-cell>
          </van-cell-group>
        </div>
      </div>
    </template>

    <!-- PDF 预览弹层（独立全屏） -->
    <van-popup
      v-model:show="pdfPreviewVisible"
      position="top"
      :style="{ height: '100vh' }"
      closeable
      close-icon-position="top-right"
      @click-close-icon="pdfPreviewVisible = false"
    >
      <div class="pdf-preview-wrap">
        <div class="pdf-preview-title">{{ pdfPreviewTitle }}</div>
        <iframe v-if="pdfPreviewUrl" :src="pdfPreviewUrl" class="pdf-iframe" />
      </div>
    </van-popup>

    <!-- 图片大图预览 -->
    <van-image-preview
      v-model:show="imagePreviewVisible"
      :images="imagePreviewList"
      :closeable="true"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { showToast } from 'vant'
import api from '@/api'

const route = useRoute()
const router = useRouter()
const moduleId = route.params.moduleId as string
const code = route.params.code as string

interface AttachmentFile {
  id: string
  name: string
  title: string
  url: string
  size: number
  ext: string
  category: 'image' | 'document'
  uploaded_at: string
}

const loading = ref(true)
const files = ref<AttachmentFile[]>([])
const moduleTitle = ref('')
const siteTheme = ref('classic')  // classic / dark / festive，匹配微站主题

// 预览状态
const pdfPreviewVisible = ref(false)
const pdfPreviewUrl = ref('')
const pdfPreviewTitle = ref('')

const imagePreviewVisible = ref(false)
const imagePreviewStartIndex = ref(0)
const imagePreviewList = computed(() => imageFiles.value.map(f => f.url))

const IMAGE_EXTS = new Set(['jpg', 'jpeg', 'png', 'gif', 'webp'])

const imageFiles = computed(() => files.value.filter(f => f.category === 'image'))
const docFiles = computed(() => files.value.filter(f => f.category === 'document'))

const navBarStyle = computed(() => {
  if (siteTheme.value === 'dark') {
    return { '--van-nav-bar-background': '#1a1a2e', '--van-nav-bar-text-color': '#e0e0e0', '--van-nav-bar-icon-color': '#e0e0e0' }
  }
  return {}
})

async function loadData() {
  loading.value = true
  try {
    const data: any = await api.get(`/p/modules/${moduleId}`)
    moduleTitle.value = data.title || ''
    const rawFiles = data.form_config?.files || []
    files.value = rawFiles.map((f: any) => {
      const ext = (f.ext || '').toLowerCase()
      return {
        id: f.id,
        name: f.name || '',
        title: f.title || f.name || '',
        url: f.url || '',
        size: f.size || 0,
        ext,
        category: f.category || (IMAGE_EXTS.has(ext) ? 'image' : 'document'),
        uploaded_at: f.uploaded_at || '',
      }
    })
  } catch (err: any) {
    showToast(err.response?.data?.detail || '资料加载失败')
  } finally {
    loading.value = false
  }
}

function onDocClick(f: AttachmentFile) {
  if (f.ext === 'pdf') {
    pdfPreviewUrl.value = f.url
    pdfPreviewTitle.value = f.title || f.name
    pdfPreviewVisible.value = true
  } else {
    // Office 等其他类型：直接下载
    showToast('正在下载…')
    const a = document.createElement('a')
    a.href = f.url
    a.download = f.name
    a.target = '_blank'
    a.rel = 'noopener'
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
  }
}

function previewImage(f: AttachmentFile) {
  const idx = imageFiles.value.findIndex(x => x.id === f.id)
  imagePreviewStartIndex.value = idx >= 0 ? idx : 0
  imagePreviewVisible.value = true
}

function formatSize(bytes: number): string {
  if (!bytes) return ''
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
  return `${(bytes / 1024 / 1024).toFixed(2)} MB`
}

function goBack() {
  router.push(`/s/${code}`)
}

onMounted(loadData)
</script>

<style scoped>
.file-attachment-page {
  min-height: 100vh;
  background: var(--page-bg, #f7f8fa);
  padding-bottom: 24px;
}

.tpl-dark { --page-bg: #0f0f1e; color: #e0e0e0; }
.tpl-festive { --page-bg: #fff5f5; }

.page-loading {
  display: block;
  margin: 80px auto;
}

.groups {
  padding: 12px 0;
}

.group {
  margin-bottom: 20px;
}

.group-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 8px 16px;
  font-size: 13px;
  color: #999;
  font-weight: 500;
}
.group-title { color: #333; font-size: 15px; font-weight: 600; }
.tpl-dark .group-title { color: #e0e0e0; }
.group-count { font-size: 12px; color: #999; }

/* 图片网格 */
.image-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 8px;
  padding: 0 12px;
}
.image-item {
  background: #fff;
  border-radius: 8px;
  overflow: hidden;
  cursor: pointer;
}
.tpl-dark .image-item { background: #1a1a2e; }
.image-thumb {
  width: 100%;
  aspect-ratio: 1;
  display: block;
}
.image-title {
  padding: 6px 8px;
  font-size: 12px;
  line-height: 1.4;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  color: #333;
}
.tpl-dark .image-title { color: #e0e0e0; }

/* 文档列表 */
.doc-list { background: transparent; }
.doc-list :deep(.van-cell) { padding: 12px 16px; }
.tpl-dark .doc-list :deep(.van-cell),
.tpl-dark .doc-list :deep(.van-cell__title) { color: #e0e0e0; background: #1a1a2e; }

.doc-icon {
  width: 36px;
  height: 36px;
  margin-right: 12px;
  border-radius: 6px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
  font-size: 10px;
  font-weight: 700;
  letter-spacing: 0.5px;
  flex-shrink: 0;
}
.ext-pdf { background: #e74c3c; }
.ext-doc, .ext-docx { background: #2980b9; }
.ext-xls, .ext-xlsx { background: #27ae60; }
.ext-ppt, .ext-pptx { background: #e67e22; }

/* PDF 预览 */
.pdf-preview-wrap {
  width: 100%;
  height: 100%;
  display: flex;
  flex-direction: column;
  background: #1a1a1a;
}
.pdf-preview-title {
  padding: 16px;
  color: #fff;
  font-size: 15px;
  text-align: center;
  flex-shrink: 0;
}
.pdf-iframe {
  flex: 1;
  width: 100%;
  border: none;
  background: #fff;
}
</style>
