<template>
  <div class="account-manage">
    <el-card shadow="never">
      <template #header>
        <div class="card-header">
          <span class="card-title">
            <el-icon><UserFilled /></el-icon>
            账号管理
          </span>
          <div>
            <el-button type="primary" :icon="Plus" @click="openCreate">新增账号</el-button>
            <el-button type="primary" plain :icon="Upload" @click="importVisible = true">批量导入</el-button>
            <el-button :icon="Download" @click="exportTemplate">下载导入模板</el-button>
          </div>
        </div>
      </template>

      <!-- 搜索区 -->
      <el-form :inline="true" class="search-form">
        <el-form-item>
          <el-input v-model="keyword" :placeholder="searchPlaceholder" clearable style="width: 250px" @keyup.enter="loadData" />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" :icon="Search" @click="loadData">搜索</el-button>
        </el-form-item>
      </el-form>

      <el-table :data="list" v-loading="loading" stripe style="margin-top: 16px">
        <el-table-column prop="id" label="ID" width="60" />
        <!-- 动态登录字段列 -->
        <el-table-column
          v-for="field in loginFields"
          :key="field.key"
          :label="field.display_name"
          :width="field.key === 'username' ? 120 : 150"
        >
          <template #default="{ row }">
            {{ getFieldValue(row, field) }}
          </template>
        </el-table-column>
        <el-table-column prop="nickname" label="昵称" width="120" />
        <el-table-column label="权限模块" min-width="200">
          <template #default="{ row }">
            <template v-if="row.permitted_module_ids && row.permitted_module_ids.length">
              <el-tag v-for="mid in row.permitted_module_ids" :key="mid" size="small" style="margin: 2px">
                {{ moduleName(mid) }}
              </el-tag>
            </template>
            <el-tag v-else type="info" size="small">全部可见</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="状态" width="80">
          <template #default="{ row }">
            <el-tag :type="row.is_active ? 'success' : 'danger'" size="small">{{ row.is_active ? '启用' : '禁用' }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="250" fixed="right">
          <template #default="{ row }">
            <el-button size="small" @click="openEdit(row)">编辑</el-button>
            <el-button size="small" type="warning" @click="openPermission(row)">权限</el-button>
            <el-popconfirm title="确认删除？" @confirm="deleteAccount(row)">
              <template #reference><el-button size="small" type="danger">删除</el-button></template>
            </el-popconfirm>
          </template>
        </el-table-column>
      </el-table>

      <el-pagination v-model:current-page="page" v-model:page-size="pageSize" :total="total" layout="total, prev, pager, next" style="margin-top: 16px; justify-content: flex-end" @current-change="loadData" />
    </el-card>

    <!-- 导入弹窗 -->
    <el-dialog v-model="importVisible" title="批量导入账号" width="600px">
      <el-alert type="info" :closable="false" style="margin-bottom: 16px">
        <div v-html="importGuide"></div>
      </el-alert>
      <el-input v-model="importText" type="textarea" :rows="10" placeholder="请按格式粘贴账号数据" />
      <template #footer>
        <el-button @click="importVisible = false">取消</el-button>
        <el-button type="primary" :loading="importing" @click="doImport">导入</el-button>
      </template>
    </el-dialog>

    <!-- 新增/编辑弹窗 -->
    <el-dialog v-model="formVisible" :title="formMode === 'create' ? '新增账号' : '编辑账号'" width="520px">
      <el-form :model="formData" label-width="100px">
        <!-- 动态登录字段 -->
        <el-form-item
          v-for="field in loginFields"
          :key="field.key"
          :label="field.display_name"
          :required="field.key === 'username'"
        >
          <el-input
            v-model="formData[field.key]"
            :placeholder="formMode === 'create' ? `请输入${field.display_name}` : '留空则不修改'"
            :disabled="formMode === 'edit' && field.key === 'username'"
          />
        </el-form-item>
        <el-form-item v-if="requirePassword" :label="formMode === 'create' ? '密码' : '新密码'" :required="formMode === 'create'">
          <el-input v-model="formData.password" :placeholder="formMode === 'create' ? '请输入密码' : '留空则不修改'" />
        </el-form-item>
        <el-form-item label="昵称"><el-input v-model="formData.nickname" /></el-form-item>
        <el-form-item label="状态"><el-switch v-model="formData.is_active" /></el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="formVisible = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="saveForm">保存</el-button>
      </template>
    </el-dialog>

    <!-- 权限设置弹窗 -->
    <el-dialog v-model="permVisible" title="设置模块权限" width="500px">
      <el-alert type="info" :closable="false" style="margin-bottom: 16px">不选任何模块则表示该账号可见全部模块</el-alert>
      <el-checkbox-group v-model="permForm.module_ids">
        <div v-for="m in modules" :key="m.id" style="margin: 8px 0">
          <el-checkbox :value="m.id">{{ m.title }}</el-checkbox>
        </div>
      </el-checkbox-group>
      <template #footer>
        <el-button @click="permVisible = false">取消</el-button>
        <el-button type="primary" @click="savePermission">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import { UserFilled, Plus, Upload, Download, Search } from '@element-plus/icons-vue'
import api from '@/api'

const route = useRoute()
const siteId = route.params.id as string

const list = ref<any[]>([])
const loading = ref(false)
const page = ref(1)
const pageSize = ref(20)
const total = ref(0)
const keyword = ref('')

const modules = ref<any[]>([])
const loginFields = ref<any[]>([])
const requirePassword = ref(true)

const importVisible = ref(false)
const importText = ref('')
const importing = ref(false)

const formVisible = ref(false)
const formMode = ref<'create' | 'edit'>('create')
const formData = reactive<Record<string, any>>({
  id: 0,
  username: '',
  phone: '',
  password: '',
  nickname: '',
  is_active: true,
})
const saving = ref(false)

const permVisible = ref(false)
const permForm = reactive({ account_id: 0, module_ids: [] as number[] })

// --- 计算属性 ---
const searchPlaceholder = computed(() => {
  const names = loginFields.value.map((f) => f.display_name)
  return names.length ? `搜索${names.join('/')}` : '搜索账号'
})

const importGuide = computed(() => {
  const headers: string[] = loginFields.value.map((f) => f.display_name)
  const headerParts = [...headers]
  if (requirePassword.value) headerParts.push('密码')
  headerParts.push('昵称')
  const sampleValues: string[] = loginFields.value.map((f) => {
    if (f.key === 'username') return 'user001'
    if (f.key === 'phone') return '13800138000'
    return 'value001'
  })
  const sampleParts = [...sampleValues]
  if (requirePassword.value) sampleParts.push('pass123')
  sampleParts.push('张三')
  const sample2Values: string[] = loginFields.value.map((f) => f.key === 'username' ? 'user002' : f.key === 'phone' ? '13900139000' : 'value002')
  const sample2Parts = [...sample2Values]
  if (requirePassword.value) sample2Parts.push('pass456')
  sample2Parts.push('李四')
  return `格式：每行一个账号，用逗号分隔：${headerParts.join(',')}<br>示例：<br>${sampleParts.join(',')}<br>${sample2Parts.join(',')}`
})

// --- 方法 ---
function getFieldValue(row: any, field: any): string {
  if (field.key === 'username') return row.username || '-'
  if (field.key === 'phone') return row.phone || '-'
  // 自定义字段
  if (row.custom_fields && row.custom_fields[field.custom_key || field.key]) {
    return row.custom_fields[field.custom_key || field.key]
  }
  return '-'
}

function moduleName(mid: number) {
  const m = modules.value.find((x) => x.id === mid)
  return m ? m.title : `#${mid}`
}

async function loadData() {
  loading.value = true
  try {
    const res: any = await api.get(`/sites/${siteId}/accounts`, {
      params: { page: page.value, page_size: pageSize.value, keyword: keyword.value || undefined },
    })
    list.value = res.items
    total.value = res.total
  } finally {
    loading.value = false
  }
}

async function loadModules() {
  const res: any = await api.get(`/sites/${siteId}/modules`)
  modules.value = res
}

async function loadSiteConfig() {
  const res: any = await api.get(`/sites/${siteId}`)
  requirePassword.value = res.login_require_password !== false
  loginFields.value = (res.login_fields_config && res.login_fields_config.length)
    ? res.login_fields_config
    : [{ key: 'username', display_name: '账号', type: 'text' }]
}

function exportTemplate() {
  const headers: string[] = loginFields.value.map((f) => f.display_name)
  const sampleValues: string[] = loginFields.value.map((f) => {
    if (f.key === 'username') return 'user001'
    if (f.key === 'phone') return '13800138000'
    return 'value001'
  })
  const headerParts = [...headers]
  if (requirePassword.value) headerParts.push('密码')
  headerParts.push('昵称')
  const sampleParts = [...sampleValues]
  if (requirePassword.value) sampleParts.push('pass123')
  sampleParts.push('张三')
  const content = headerParts.join(',') + '\n' + sampleParts.join(',')
  const blob = new Blob(['\ufeff' + content], { type: 'text/csv;charset=utf-8' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = '账号导入模板.csv'
  a.click()
  URL.revokeObjectURL(url)
}

async function doImport() {
  if (!importText.value.trim()) { ElMessage.warning('请输入账号数据'); return }
  importing.value = true
  try {
    const lines = importText.value.trim().split('\n').filter((l) => l.trim() && !l.includes(loginFields.value[0]?.display_name || '账号'))
    const accounts = lines.map((line) => {
      const parts = line.split(',').map((s) => s.trim())
      const item: any = { username: parts[0] || '' }
      // 密码列位置: 登录字段数之后（如果启用密码）
      const passwordIdx = loginFields.value.length
      if (requirePassword.value) {
        item.password = parts[passwordIdx] || ''
      }
      // 昵称在最后
      const nicknameIdx = requirePassword.value ? loginFields.value.length + 1 : loginFields.value.length
      if (parts.length > nicknameIdx) {
        item.nickname = parts[nicknameIdx] || null
      }
      // 处理各登录字段
      loginFields.value.forEach((field, idx) => {
        if (idx === 0) return // username 已处理
        const val = parts[idx]
        if (field.key === 'phone') {
          item.phone = val || null
        } else if (field.key === 'custom' && val) {
          if (!item.custom_fields) item.custom_fields = {}
          item.custom_fields[field.custom_key || field.key] = val
        }
      })
      return item
    }).filter((a) => a.username && (requirePassword.value ? a.password : true))
    if (!accounts.length) { ElMessage.warning('未解析到有效账号数据'); return }
    await api.post(`/sites/${siteId}/accounts/import`, { accounts })
    ElMessage.success('导入成功')
    importVisible.value = false
    importText.value = ''
    loadData()
  } catch {
    // 错误已在拦截器处理
  } finally {
    importing.value = false
  }
}

function resetForm() {
  formData.id = 0
  formData.password = ''
  formData.nickname = ''
  formData.is_active = true
  loginFields.value.forEach((field) => {
    formData[field.key] = ''
  })
}

function openCreate() {
  formMode.value = 'create'
  resetForm()
  formVisible.value = true
}

function openEdit(row: any) {
  formMode.value = 'edit'
  resetForm()
  formData.id = row.id
  formData.nickname = row.nickname || ''
  formData.is_active = row.is_active
  loginFields.value.forEach((field) => {
    if (field.key === 'username') {
      formData[field.key] = row.username || ''
    } else if (field.key === 'phone') {
      formData[field.key] = row.phone || ''
    } else {
      const ck = field.custom_key || field.key
      formData[field.key] = (row.custom_fields && row.custom_fields[ck]) || ''
    }
  })
  formVisible.value = true
}

async function saveForm() {
  saving.value = true
  try {
    if (formMode.value === 'create') {
      // 新增
      const data: any = { username: formData.username }
      // 需要密码时才传密码
      if (requirePassword.value) data.password = formData.password
      if (formData.nickname) data.nickname = formData.nickname
      data.is_active = formData.is_active
      // 处理各登录字段
      const customFields: Record<string, string> = {}
      loginFields.value.forEach((field) => {
        if (field.key === 'phone' && formData.phone) {
          data.phone = formData.phone
        } else if (field.key === 'custom' && formData[field.key]) {
          customFields[field.custom_key || field.key] = formData[field.key]
        }
      })
      if (Object.keys(customFields).length) data.custom_fields = customFields
      await api.post(`/sites/${siteId}/accounts`, data)
      ElMessage.success('新增成功')
    } else {
      // 编辑
      const data: any = {}
      // username 可修改（如果不是固定不可改）
      if (formData.username) data.username = formData.username
      if (requirePassword.value && formData.password) data.password = formData.password
      data.nickname = formData.nickname || null
      data.is_active = formData.is_active
      // 处理各登录字段
      const customFields: Record<string, string> = {}
      loginFields.value.forEach((field) => {
        if (field.key === 'phone') {
          data.phone = formData.phone || null
        } else if (field.key === 'custom' && formData[field.key]) {
          customFields[field.custom_key || field.key] = formData[field.key]
        }
      })
      if (Object.keys(customFields).length) data.custom_fields = customFields
      await api.put(`/sites/${siteId}/accounts/${formData.id}`, data)
      ElMessage.success('保存成功')
    }
    formVisible.value = false
    loadData()
  } catch {
    // 错误已在拦截器处理
  } finally {
    saving.value = false
  }
}

function openPermission(row: any) {
  permForm.account_id = row.id
  permForm.module_ids = [...(row.permitted_module_ids || [])]
  permVisible.value = true
}

async function savePermission() {
  await api.put(`/sites/${siteId}/accounts/${permForm.account_id}/permissions`, { module_ids: permForm.module_ids })
  ElMessage.success('权限已更新')
  permVisible.value = false
  loadData()
}

async function deleteAccount(row: any) {
  await api.delete(`/sites/${siteId}/accounts/${row.id}`)
  ElMessage.success('已删除')
  loadData()
}

onMounted(() => {
  loadSiteConfig()
  loadData()
  loadModules()
})
</script>

<style scoped>
.card-header { display: flex; justify-content: space-between; align-items: center; }
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
.search-form {
  margin-bottom: 8px;
}
</style>
