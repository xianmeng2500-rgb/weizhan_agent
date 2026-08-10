<template>
  <div class="form-submissions">
    <el-card shadow="never">
      <template #header>
        <div class="card-header">
          <div class="card-title">
            <el-button link @click="goBack"><el-icon><ArrowLeft /></el-icon></el-button>
            <el-icon><Document /></el-icon>
            <span>{{ moduleTitle }} - 报名数据</span>
          </div>
          <div>
            <el-button type="primary" :icon="Download" @click="exportCSV">导出 CSV</el-button>
          </div>
        </div>
      </template>

      <!-- 查询条件 -->
      <el-form :inline="true" :model="query" class="query-form">
        <el-form-item label="姓名">
          <el-input v-model="query.submitter_name" placeholder="姓名" clearable style="width: 130px" @keyup.enter="loadData" />
        </el-form-item>
        <el-form-item label="手机号">
          <el-input v-model="query.submitter_phone" placeholder="手机号" clearable style="width: 150px" @keyup.enter="loadData" />
        </el-form-item>
        <el-form-item label="提交时间">
          <el-date-picker v-model="query.start_date" type="date" value-format="YYYY-MM-DD" placeholder="开始" style="width: 140px" />
          <span class="range-sep">至</span>
          <el-date-picker v-model="query.end_date" type="date" value-format="YYYY-MM-DD" placeholder="结束" style="width: 140px" />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" :icon="Search" @click="loadData">查询</el-button>
          <el-button :icon="Refresh" @click="resetQuery">重置</el-button>
        </el-form-item>
      </el-form>

      <el-table :data="list" v-loading="loading" stripe>
        <el-table-column type="index" label="序号" width="60" />
        <el-table-column prop="id" label="ID" width="70" />
        <el-table-column prop="submitter_name" label="姓名" width="120" />
        <el-table-column prop="submitter_phone" label="手机号" width="140" />
        <el-table-column
          v-for="field in formFields"
          :key="field.id"
          :label="field.title"
          :prop="field.id"
          min-width="140"
          show-overflow-tooltip
        >
          <template #default="{ row }">
            {{ formatValue(row.data && row.data[field.id]) }}
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="提交时间" width="170">
          <template #default="{ row }">
            {{ formatTime(row.created_at) }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="150" fixed="right">
          <template #default="{ row }">
            <el-button size="small" @click="openDetail(row)">详情</el-button>
            <el-popconfirm title="确认删除？" @confirm="deleteRow(row)">
              <template #reference><el-button size="small" type="danger">删除</el-button></template>
            </el-popconfirm>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <el-dialog v-model="detailVisible" title="报名详情" width="500px">
      <div v-if="detailRow" class="detail-content">
        <div class="detail-item">
          <span class="detail-label">提交时间</span>
          <span class="detail-value">{{ formatTime(detailRow.created_at) }}</span>
        </div>
        <div class="detail-item">
          <span class="detail-label">姓名</span>
          <span class="detail-value">{{ detailRow.submitter_name || '-' }}</span>
        </div>
        <div class="detail-item">
          <span class="detail-label">手机号</span>
          <span class="detail-value">{{ detailRow.submitter_phone || '-' }}</span>
        </div>
        <el-divider />
        <div v-for="(field, idx) in formFields" :key="idx" class="detail-item">
          <span class="detail-label">{{ field.title }}</span>
          <span class="detail-value">{{ formatValue(detailRow.data[field.id]) }}</span>
        </div>
        <el-divider />
        <el-form label-position="top">
          <el-form-item label="管理员备注">
            <el-input v-model="detailNote" type="textarea" :rows="3" />
          </el-form-item>
        </el-form>
      </div>
      <template #footer>
        <el-button @click="detailVisible = false">关闭</el-button>
        <el-button type="primary" :loading="savingNote" @click="saveNote">保存备注</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { ArrowLeft, Download, Search, Refresh, Document } from '@element-plus/icons-vue'
import api from '@/api'
import dayjs from 'dayjs'

const route = useRoute()
const router = useRouter()
const siteId = route.params.id as string
const moduleId = Number(route.params.moduleId)

const query = reactive({
  submitter_name: '',
  submitter_phone: '',
  start_date: '',
  end_date: '',
})

const list = ref<any[]>([])
const loading = ref(false)
const moduleTitle = ref('模块')
const formConfig = ref<any>(null)
const detailVisible = ref(false)
const detailRow = ref<any>(null)
const detailNote = ref('')
const savingNote = ref(false)

const formFields = computed(() => {
  return formConfig.value?.fields || []
})

function goBack() {
  router.push(`/sites/${siteId}/modules`)
}

function formatTime(t: string) {
  return t ? dayjs(t).format('YYYY-MM-DD HH:mm:ss') : ''
}

function formatValue(val: any) {
  if (val === null || val === undefined) return '-'
  if (Array.isArray(val)) return val.join(', ')
  return String(val)
}

async function loadModule() {
  try {
    const res: any = await api.get(`/sites/${siteId}/modules/${moduleId}`)
    moduleTitle.value = res.title || '模块'
    formConfig.value = res.form_config || { fields: [] }
  } catch (e) {
    console.error(e)
  }
}

async function loadData() {
  loading.value = true
  try {
    const params: Record<string, any> = {}
    if (query.submitter_name) params.submitter_name = query.submitter_name
    if (query.submitter_phone) params.submitter_phone = query.submitter_phone
    if (query.start_date) params.start_date = query.start_date
    if (query.end_date) params.end_date = query.end_date
    const res: any = await api.get(`/sites/${siteId}/modules/${moduleId}/form-submissions`, { params })
    list.value = res || []
  } finally {
    loading.value = false
  }
}

function resetQuery() {
  query.submitter_name = ''
  query.submitter_phone = ''
  query.start_date = ''
  query.end_date = ''
  loadData()
}

function openDetail(row: any) {
  detailRow.value = row
  detailNote.value = row.note || ''
  detailVisible.value = true
}

async function saveNote() {
  if (!detailRow.value) return
  savingNote.value = true
  try {
    await api.put(`/sites/${siteId}/modules/${moduleId}/form-submissions/${detailRow.value.id}`, {
      note: detailNote.value,
    })
    ElMessage.success('备注已保存')
    detailRow.value.note = detailNote.value
  } finally {
    savingNote.value = false
  }
}

async function deleteRow(row: any) {
  try {
    await api.delete(`/sites/${siteId}/modules/${moduleId}/form-submissions/${row.id}`)
    ElMessage.success('已删除')
    loadData()
  } catch (e) {
    console.error(e)
  }
}

function escapeCSV(value: any) {
  const str = value === null || value === undefined ? '' : String(value)
  if (str.includes(',') || str.includes('"') || str.includes('\n')) {
    return '"' + str.replace(/"/g, '""') + '"'
  }
  return str
}

function exportCSV() {
  const headers = ['ID', '提交时间', '姓名', '手机号']
  const fieldIds: string[] = []
  for (const field of formFields.value) {
    headers.push(field.title)
    fieldIds.push(field.id)
  }
  headers.push('管理员备注')

  const lines = [headers.join(',')]
  for (const row of list.value) {
    const cells = [
      row.id,
      formatTime(row.created_at),
      row.submitter_name || '',
      row.submitter_phone || '',
    ]
    for (const fid of fieldIds) {
      cells.push(escapeCSV(formatValue(row.data?.[fid])))
    }
    cells.push(escapeCSV(row.note || ''))
    lines.push(cells.join(','))
  }

  const blob = new Blob(['\uFEFF' + lines.join('\n')], { type: 'text/csv;charset=utf-8' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `${moduleTitle.value}_报名数据_${dayjs().format('YYYYMMDD_HHmmss')}.csv`
  a.click()
  URL.revokeObjectURL(url)
}

onMounted(() => {
  if (!moduleId) {
    ElMessage.warning('缺少模块ID')
    goBack()
    return
  }
  loadModule()
  loadData()
})
</script>

<style scoped>
.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
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

.query-form {
  margin-bottom: 16px;
  padding: 14px 16px 0;
  background: #fafafa;
  border-radius: 4px;
}

.range-sep {
  margin: 0 8px;
  color: #909399;
}

.detail-content {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.detail-item {
  display: flex;
  gap: 12px;
}

.detail-label {
  width: 90px;
  color: #909399;
  flex-shrink: 0;
}

.detail-value {
  flex: 1;
  color: #303133;
  word-break: break-all;
}
</style>
