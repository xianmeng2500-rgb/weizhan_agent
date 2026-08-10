<template>
  <div class="schedule-editor">
    <div class="schedule-toolbar">
      <div class="toolbar-left">
        <el-button type="primary" :icon="Plus" @click="addItem">添加日程</el-button>
        <el-upload
          :show-file-list="false"
          :before-upload="handleImport"
          accept=".csv"
        >
          <el-button :icon="Upload">导入 CSV</el-button>
        </el-upload>
        <el-button :icon="Download" @click="downloadTemplate">下载模板</el-button>
      </div>
      <div class="toolbar-right">
        <span class="item-count">共 {{ items.length }} 条日程</span>
      </div>
    </div>

    <div class="schedule-table-wrap">
      <el-table
        v-if="items.length"
        :data="items"
        border stripe
        style="width: 100%"
        row-key="id"
        height="100%"
      >
        <el-table-column label="日期" width="150">
          <template #default="{ row }">
            <el-date-picker
              v-model="row.date"
              type="date"
              placeholder="选择日期"
              value-format="YYYY-MM-DD"
              size="default"
              style="width: 100%"
              @change="onCellChange"
            />
          </template>
        </el-table-column>
        <el-table-column label="时间" width="180">
          <template #default="{ row }">
            <el-input v-model="row.time" placeholder="如：09:00-10:00" size="default" @change="onCellChange" />
          </template>
        </el-table-column>
        <el-table-column label="题目" min-width="200">
          <template #default="{ row }">
            <el-input v-model="row.topic" placeholder="日程题目" size="default" @change="onCellChange" />
          </template>
        </el-table-column>
        <el-table-column label="人员" min-width="200">
          <template #default="{ row }">
            <el-input v-model="row.personnel" placeholder="参与人员" size="default" @change="onCellChange" />
          </template>
        </el-table-column>
        <el-table-column label="操作" width="80" fixed="right">
          <template #default="{ $index }">
            <el-button link type="danger" :icon="Delete" @click="removeItem($index)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>

      <el-empty
        v-else
        description="暂无日程，请手动添加或导入 CSV 文件"
        :image-size="100"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue'
import { ElMessage } from 'element-plus'
import { Plus, Upload, Download, Delete } from '@element-plus/icons-vue'
import api from '@/api'

interface ScheduleItem {
  id: number
  date: string
  time: string
  topic: string
  personnel: string
}

const props = defineProps<{
  modelValue: { items?: ScheduleItem[] } | null
  siteId: number
  moduleId: number
}>()

const emit = defineEmits<{
  (e: 'update:modelValue', value: { items: ScheduleItem[] }): void
}>()

let nextId = 1
const items = ref<ScheduleItem[]>([])

// 单向：仅首次从 props 初始化
watch(() => props.modelValue, (val) => {
  if (val && Array.isArray(val.items) && val.items.length > 0 && items.value.length === 0) {
    items.value = val.items.map((item: any) => ({
      id: item.id || nextId++,
      date: item.date || '',
      time: item.time || '',
      topic: item.topic || '',
      personnel: item.personnel || '',
    }))
    nextId = Math.max(...items.value.map(i => i.id), 0) + 1
  }
}, { immediate: true })

// 手动同步到父组件（不再用 deep watch，彻底消除循环）
function syncToParent() {
  emit('update:modelValue', { items: [...items.value] })
}

function addItem() {
  items.value.push({
    id: nextId++,
    date: '',
    time: '',
    topic: '',
    personnel: '',
  })
  syncToParent()
}

function removeItem(index: number) {
  items.value.splice(index, 1)
  syncToParent()
}

function onCellChange() {
  syncToParent()
}

async function handleImport(file: File) {
  const formData = new FormData()
  formData.append('file', file)

  try {
    const res: any = await api.post(
      `/sites/${props.siteId}/modules/${props.moduleId}/schedule/import`,
      formData,
      { headers: { 'Content-Type': 'multipart/form-data' } }
    )
    if (res.items) {
      items.value = res.items.map((item: any) => ({
        id: nextId++,
        date: item.date || '',
        time: item.time || '',
        topic: item.topic || '',
        personnel: item.personnel || '',
      }))
      syncToParent()
      ElMessage.success(res.message || '导入成功')
    }
  } catch {
    // 错误已在拦截器处理
  }
  return false
}

async function downloadTemplate() {
  try {
    const res = await api.get(
      `/sites/${props.siteId}/modules/schedule-template`,
      { responseType: 'blob' }
    )
    const url = window.URL.createObjectURL(new Blob([res]))
    const link = document.createElement('a')
    link.href = url
    link.setAttribute('download', 'schedule_template.csv')
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    window.URL.revokeObjectURL(url)
    ElMessage.success('模板下载成功')
  } catch {
    // 错误已在拦截器处理
  }
}

function getConfig() {
  return { items: items.value.map(({ id, ...rest }) => rest) }
}

function validate() {
  return items.value.length > 0
}

defineExpose({ getConfig, validate })
</script>

<style scoped>
.schedule-editor {
  display: flex;
  flex-direction: column;
  height: 100%;
  min-height: 400px;
}
.schedule-toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 0 16px;
  gap: 8px;
  flex-wrap: wrap;
  flex-shrink: 0;
}
.toolbar-left {
  display: flex;
  align-items: center;
  gap: 8px;
}
.toolbar-right {
  color: #909399;
  font-size: 13px;
}
.schedule-table-wrap {
  flex: 1;
  overflow: auto;
  min-height: 0;
}
</style>
