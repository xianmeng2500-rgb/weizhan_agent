<template>
  <div class="icon-picker">
    <div class="icon-target" @click="openDialog">
      <img v-if="modelValue" :src="modelValue" />
      <div v-else class="icon-placeholder"><el-icon><Plus /></el-icon></div>
    </div>
    <div class="icon-actions">
      <el-button text size="small" @click="openDialog">选择图标</el-button>
      <el-button v-if="modelValue" text size="small" type="danger" @click="clearIcon">移除</el-button>
    </div>

    <el-dialog v-model="visible" title="选择图标" width="560px" append-to-body destroy-on-close>
      <el-tabs v-model="activeTab">
        <el-tab-pane label="图标库" name="library">
          <div v-if="iconLibrary.length" class="icon-grid">
            <div
              v-for="(icon, index) in iconLibrary"
              :key="index"
              class="icon-grid-item"
              :class="{ active: modelValue === icon.url }"
              @click="selectIcon(icon.url)"
            >
              <el-image :src="icon.url" fit="contain" class="icon-grid-img">
                <template #error><el-icon class="icon-grid-fallback"><Picture /></el-icon></template>
              </el-image>
              <span class="icon-grid-name" :title="icon.name">{{ icon.name || '未命名' }}</span>
            </div>
          </div>
          <el-empty v-else description="图标库为空，请联系管理员在系统配置中添加" :image-size="72" />
        </el-tab-pane>

        <el-tab-pane label="上传" name="upload">
          <el-upload
            action="/api/v1/upload/image"
            :headers="uploadHeaders"
            :show-file-list="false"
            :on-success="onUploadSuccess"
            :on-error="onUploadError"
            accept="image/*"
            drag
          >
            <el-icon class="upload-icon"><UploadFilled /></el-icon>
            <div class="upload-text">拖拽图片到此处，或<em>点击上传</em></div>
            <template #tip>
              <div class="upload-tip">建议 128×128 正方形图标，支持 PNG / JPG / SVG</div>
            </template>
          </el-upload>
          <div v-if="modelValue" class="upload-preview">
            <span class="upload-preview-label">当前图标：</span>
            <img :src="modelValue" class="upload-preview-img" />
          </div>
        </el-tab-pane>
      </el-tabs>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { Plus, Picture, UploadFilled } from '@element-plus/icons-vue'
import { useAuthStore } from '@/store/auth'
import api from '@/api'

interface IconItem {
  name: string
  url: string
}

const props = defineProps<{
  modelValue: string
}>()

const emit = defineEmits<{
  'update:modelValue': [value: string]
}>()

const auth = useAuthStore()
const uploadHeaders = computed(() => ({ Authorization: `Bearer ${auth.token}` }))

const visible = ref(false)
const activeTab = ref('library')
const iconLibrary = ref<IconItem[]>([])

async function loadIconLibrary() {
  try {
    const res: any = await api.get('/system-config/runtime')
    iconLibrary.value = res.local_icon_library || []
  } catch {
    iconLibrary.value = []
  }
}

function openDialog() {
  visible.value = true
  if (!iconLibrary.value.length) {
    loadIconLibrary()
  }
}

function selectIcon(url: string) {
  emit('update:modelValue', url)
  visible.value = false
}

function onUploadSuccess(res: any) {
  if (res.url) {
    emit('update:modelValue', res.url)
    ElMessage.success('上传成功')
  } else {
    ElMessage.error('上传失败')
  }
}

function onUploadError() {
  ElMessage.error('上传失败，请重试')
}

function clearIcon() {
  emit('update:modelValue', '')
}

onMounted(() => {
  loadIconLibrary()
})
</script>

<style scoped>
.icon-picker {
  display: flex;
  align-items: center;
  gap: 8px;
}

.icon-target {
  width: 48px;
  height: 48px;
  border: 1px dashed var(--el-border-color);
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  overflow: hidden;
  transition: border-color 0.2s;
}

.icon-target:hover {
  border-color: var(--el-color-primary);
}

.icon-target img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.icon-placeholder {
  color: var(--el-text-color-placeholder);
  font-size: 18px;
}

.icon-actions {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

/* dialog content */
.icon-grid {
  display: grid;
  grid-template-columns: repeat(5, 1fr);
  gap: 12px;
  max-height: 360px;
  overflow-y: auto;
}

.icon-grid-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
  padding: 8px 4px;
  border: 2px solid transparent;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s;
}

.icon-grid-item:hover {
  background: var(--el-fill-color-light);
}

.icon-grid-item.active {
  border-color: var(--el-color-primary);
  background: var(--el-color-primary-light-9);
}

.icon-grid-img {
  width: 40px;
  height: 40px;
}

.icon-grid-fallback {
  width: 40px;
  height: 40px;
  color: var(--el-text-color-placeholder);
}

.icon-grid-name {
  font-size: 12px;
  color: var(--el-text-color-secondary);
  max-width: 100%;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.upload-icon {
  font-size: 32px;
  color: var(--el-text-color-placeholder);
}

.upload-text {
  color: var(--el-text-color-regular);
  font-size: 14px;
}

.upload-text em {
  color: var(--el-color-primary);
  font-style: normal;
}

.upload-tip {
  font-size: 12px;
  color: var(--el-text-color-placeholder);
  margin-top: 4px;
}

.upload-preview {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-top: 16px;
}

.upload-preview-label {
  font-size: 13px;
  color: var(--el-text-color-secondary);
}

.upload-preview-img {
  width: 48px;
  height: 48px;
  object-fit: cover;
  border-radius: 8px;
  border: 1px solid var(--el-border-color);
}
</style>
