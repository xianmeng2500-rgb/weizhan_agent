<template>
  <div class="file-attachment-editor">
    <div class="editor-toolbar">
      <el-upload
        :action="uploadUrl"
        :headers="uploadHeaders"
        :show-file-list="false"
        :before-upload="beforeUpload"
        :on-success="onUploadSuccess"
        :on-error="onUploadError"
        :accept="acceptTypes"
        multiple
        drag
      >
        <el-icon class="upload-icon"><UploadFilled /></el-icon>
        <div class="upload-text">拖拽文件到此处，或<em>点击上传</em></div>
        <template #tip>
          <div class="upload-tip">
            支持 PDF / Word / Excel / PPT / 图片（jpg/png/gif/webp），单文件最大 50MB
          </div>
        </template>
      </el-upload>
    </div>

    <div class="editor-list" v-if="files.length">
      <div
        v-for="(file, index) in files"
        :key="file.id"
        class="file-row"
      >
        <!-- 缩略图/类型图标 -->
        <div class="file-thumb">
          <el-image
            v-if="file.category === 'image'"
            :src="file.url"
            fit="cover"
            class="thumb-img"
            :preview-src-list="[file.url]"
            :hide-on-click-modal="true"
            preview-teleported
          />
          <div v-else class="thumb-icon" :class="`ext-${file.ext}`">
            <span class="ext-label">{{ file.ext.toUpperCase() }}</span>
          </div>
        </div>

        <!-- 标题与元信息 -->
        <div class="file-info">
          <el-input
            v-model="file.title"
            placeholder="设置显示标题（可与文件名不同）"
            size="default"
            maxlength="60"
            show-word-limit
            class="title-input"
            @change="syncToParent"
          />
          <div class="file-meta">
            <span class="meta-name" :title="file.name">{{ file.name }}</span>
            <el-divider direction="vertical" />
            <span>{{ formatSize(file.size) }}</span>
            <el-divider direction="vertical" />
            <span>上传于 {{ formatTime(file.uploaded_at) }}</span>
          </div>
        </div>

        <!-- 操作 -->
        <div class="file-actions">
          <el-button-group>
            <el-button
              size="small"
              :disabled="index === 0"
              :icon="ArrowUp"
              @click="moveUp(index)"
              title="上移"
            />
            <el-button
              size="small"
              :disabled="index === files.length - 1"
              :icon="ArrowDown"
              @click="moveDown(index)"
              title="下移"
            />
          </el-button-group>
          <el-button
            size="small"
            link
            :icon="View"
            @click="previewFile(file)"
          >预览</el-button>
          <el-button
            size="small"
            link
            type="danger"
            :icon="Delete"
            @click="removeFile(index)"
          >删除</el-button>
        </div>
      </div>
    </div>

    <el-empty
      v-else
      description="还没有附件，请在上面拖入或点击上传"
      :image-size="100"
    />

    <!-- PDF 预览弹窗 -->
    <el-dialog
      v-model="previewVisible"
      :title="previewTitle"
      width="80%"
      top="5vh"
      append-to-body
      destroy-on-close
    >
      <iframe
        v-if="previewUrl"
        :src="previewUrl"
        class="preview-iframe"
      />
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  UploadFilled, ArrowUp, ArrowDown, View, Delete,
} from '@element-plus/icons-vue'
import { useAuthStore } from '@/store/auth'
import api from '@/api'

export interface AttachmentFile {
  id: string
  name: string
  title: string
  url: string
  size: number
  ext: string
  category: 'image' | 'document'
  uploaded_at: string
}

interface AttachmentConfig {
  files: AttachmentFile[]
}

const props = defineProps<{
  modelValue: AttachmentConfig | null
  siteId: number
  moduleId: number
}>()

const emit = defineEmits<{
  (e: 'update:modelValue', value: AttachmentConfig): void
}>()

const auth = useAuthStore()
const uploadHeaders = computed(() => ({ Authorization: `Bearer ${auth.token}` }))
const uploadUrl = '/api/v1/upload/file'
const acceptTypes = '.pdf,.doc,.docx,.xls,.xlsx,.ppt,.pptx,.jpg,.jpeg,.png,.gif,.webp'

const IMAGE_EXTS = new Set(['jpg', 'jpeg', 'png', 'gif', 'webp'])
const ALLOWED_EXTS = new Set(['pdf', 'doc', 'docx', 'xls', 'xlsx', 'ppt', 'pptx', 'jpg', 'jpeg', 'png', 'gif', 'webp'])

const files = ref<AttachmentFile[]>([])

// 首次从 props 初始化
watch(() => props.modelValue, (val) => {
  if (val && Array.isArray(val.files) && val.files.length > 0 && files.value.length === 0) {
    files.value = val.files.map((f: any) => ({
      id: f.id || crypto.randomUUID(),
      name: f.name || '',
      title: f.title || f.name || '',
      url: f.url || '',
      size: f.size || 0,
      ext: (f.ext || '').toLowerCase(),
      category: f.category || (IMAGE_EXTS.has((f.ext || '').toLowerCase()) ? 'image' : 'document'),
      uploaded_at: f.uploaded_at || new Date().toISOString(),
    }))
  }
}, { immediate: true })

function syncToParent() {
  emit('update:modelValue', { files: [...files.value] })
}

function beforeUpload(file: File) {
  const ext = (file.name.split('.').pop() || '').toLowerCase()
  if (!ALLOWED_EXTS.has(ext)) {
    ElMessage.error(`不支持的文件类型 .${ext}，请上传 PDF/Office/图片`)
    return false
  }
  if (file.size > 50 * 1024 * 1024) {
    ElMessage.error(`${file.name} 超过 50MB 上限`)
    return false
  }
  return true
}

async function onUploadSuccess(res: any, uploadFile: any) {
  if (!res?.url) {
    ElMessage.error('上传失败：未返回 URL')
    return
  }
  const ext = (res.original_name || uploadFile.name).split('.').pop().toLowerCase()
  files.value.push({
    id: crypto.randomUUID(),
    name: res.original_name || uploadFile.name,
    title: (res.original_name || uploadFile.name).replace(/\.[^.]+$/, ''),
    url: res.url,
    size: uploadFile.size,
    ext,
    category: IMAGE_EXTS.has(ext) ? 'image' : 'document',
    uploaded_at: new Date().toISOString(),
  })
  syncToParent()
  ElMessage.success(`${uploadFile.name} 上传成功`)
}

function onUploadError(err: any) {
  const msg = err?.message || '上传失败'
  ElMessage.error(msg)
}

function moveUp(index: number) {
  if (index === 0) return
  const [item] = files.value.splice(index, 1)
  files.value.splice(index - 1, 0, item)
  syncToParent()
}

function moveDown(index: number) {
  if (index === files.value.length - 1) return
  const [item] = files.value.splice(index, 1)
  files.value.splice(index + 1, 0, item)
  syncToParent()
}

async function removeFile(index: number) {
  const f = files.value[index]
  try {
    await ElMessageBox.confirm(
      `确认删除「${f.title || f.name}」？仅删除列表引用，OSS 上的文件保留。`,
      '删除附件',
      { type: 'warning', confirmButtonText: '删除', cancelButtonText: '取消' }
    )
  } catch {
    return
  }
  files.value.splice(index, 1)
  syncToParent()
  ElMessage.success('已删除')
}

// 预览
const previewVisible = ref(false)
const previewUrl = ref('')
const previewTitle = ref('')
function previewFile(file: AttachmentFile) {
  if (file.ext === 'pdf') {
    previewUrl.value = file.url
    previewTitle.value = file.title || file.name
    previewVisible.value = true
  } else if (file.category === 'image') {
    // 图片直接用 el-image preview，弹窗内不做事
    ElMessage.info('点击列表中的图片可放大预览')
  } else {
    // Office 及其他：直接下载预览
    window.open(file.url, '_blank')
  }
}

function formatSize(bytes: number): string {
  if (!bytes) return '-'
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
  return `${(bytes / 1024 / 1024).toFixed(2)} MB`
}

function formatTime(iso: string): string {
  if (!iso) return '-'
  const d = new Date(iso)
  const pad = (n: number) => String(n).padStart(2, '0')
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())} ${pad(d.getHours())}:${pad(d.getMinutes())}`
}

defineExpose({
  getConfig: (): AttachmentConfig => ({ files: [...files.value] }),
})
</script>

<style scoped>
.file-attachment-editor {
  display: flex;
  flex-direction: column;
  gap: 16px;
  height: 100%;
}

.editor-toolbar :deep(.el-upload) {
  width: 100%;
}
.editor-toolbar :deep(.el-upload-dragger) {
  padding: 24px;
}
.upload-icon {
  font-size: 36px;
  color: #409eff;
  margin-bottom: 8px;
}
.upload-text {
  font-size: 14px;
  color: #606266;
}
.upload-text em { color: #409eff; font-style: normal; font-weight: 600; }
.upload-tip {
  font-size: 12px;
  color: #909399;
  margin-top: 6px;
}

.editor-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
  max-height: 480px;
  overflow-y: auto;
}

.file-row {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 10px 12px;
  background: #fafbfc;
  border: 1px solid #ebeef5;
  border-radius: 6px;
  transition: background 0.15s;
}
.file-row:hover { background: #f5f7fa; }

.file-thumb {
  width: 48px;
  height: 48px;
  flex-shrink: 0;
  border-radius: 4px;
  overflow: hidden;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #fff;
  border: 1px solid #ebeef5;
}
.thumb-img { width: 100%; height: 100%; }
.thumb-icon {
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
  font-size: 11px;
  font-weight: 600;
}
.ext-label { letter-spacing: 0.5px; }
.thumb-icon.ext-pdf { background: #e74c3c; }
.thumb-icon.ext-doc, .thumb-icon.ext-docx { background: #2980b9; }
.thumb-icon.ext-xls, .thumb-icon.ext-xlsx { background: #27ae60; }
.thumb-icon.ext-ppt, .thumb-icon.ext-pptx { background: #e67e22; }

.file-info {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 4px;
}
.title-input { width: 100%; }
.file-meta {
  font-size: 12px;
  color: #909399;
  display: flex;
  align-items: center;
  gap: 4px;
  flex-wrap: wrap;
}
.meta-name {
  max-width: 220px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  color: #606266;
}

.file-actions {
  display: flex;
  align-items: center;
  gap: 4px;
  flex-shrink: 0;
}

.preview-iframe {
  width: 100%;
  height: 75vh;
  border: none;
}
</style>
