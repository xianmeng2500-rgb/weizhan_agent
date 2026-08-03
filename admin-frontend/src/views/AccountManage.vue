<template>
  <div class="account-manage">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>账号管理</span>
          <div>
            <el-button type="primary" @click="importVisible = true">批量导入账号</el-button>
            <el-button @click="exportTemplate">下载导入模板</el-button>
          </div>
        </div>
      </template>

      <div class="toolbar">
        <el-input v-model="keyword" placeholder="搜索账号/昵称/手机号" style="width: 250px" clearable @keyup.enter="loadData" />
        <el-button style="margin-left: 10px" @click="loadData">搜索</el-button>
      </div>

      <el-table :data="list" v-loading="loading" border style="margin-top: 16px">
        <el-table-column prop="id" label="ID" width="60" />
        <el-table-column prop="username" label="账号" width="120" />
        <el-table-column prop="nickname" label="昵称" width="120" />
        <el-table-column prop="phone" label="手机号" width="150" />
        <el-table-column label="权限模块" min-width="200">
          <template #default="{ row }">
            <template v-if="row.permitted_module_ids.length">
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
        格式：每行一个账号，用逗号分隔：账号,密码,昵称,手机号<br>
        示例：<br>user001,pass123,张三,13800138000<br>user002,pass456,李四,13900139000
      </el-alert>
      <el-input v-model="importText" type="textarea" :rows="10" placeholder="请按格式粘贴账号数据" />
      <template #footer>
        <el-button @click="importVisible = false">取消</el-button>
        <el-button type="primary" :loading="importing" @click="doImport">导入</el-button>
      </template>
    </el-dialog>

    <!-- 编辑弹窗 -->
    <el-dialog v-model="editVisible" title="编辑账号" width="500px">
      <el-form :model="editForm" label-width="80px">
        <el-form-item label="账号">
          <el-input :model-value="editForm.username" disabled />
        </el-form-item>
        <el-form-item label="新密码">
          <el-input v-model="editForm.password" placeholder="留空则不修改" />
        </el-form-item>
        <el-form-item label="昵称"><el-input v-model="editForm.nickname" /></el-form-item>
        <el-form-item label="手机号"><el-input v-model="editForm.phone" /></el-form-item>
        <el-form-item label="状态"><el-switch v-model="editForm.is_active" /></el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="editVisible = false">取消</el-button>
        <el-button type="primary" @click="saveEdit">保存</el-button>
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
import { ref, reactive, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import api from '@/api'

const route = useRoute()
const siteId = route.params.id as string

const list = ref([])
const loading = ref(false)
const page = ref(1)
const pageSize = ref(20)
const total = ref(0)
const keyword = ref('')

const modules = ref<any[]>([])

const importVisible = ref(false)
const importText = ref('')
const importing = ref(false)

const editVisible = ref(false)
const editForm = reactive({ id: 0, username: '', password: '', nickname: '', phone: '', is_active: true })

const permVisible = ref(false)
const permForm = reactive({ account_id: 0, module_ids: [] as number[] })

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

function exportTemplate() {
  const content = '账号,密码,昵称,手机号\nuser001,pass123,张三,13800138000\nuser002,pass456,李四,13900139000'
  const blob = new Blob([content], { type: 'text/csv;charset=utf-8' })
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
    const lines = importText.value.trim().split('\n').filter((l) => l.trim() && !l.includes('账号,'))
    const accounts = lines.map((line) => {
      const parts = line.split(',').map((s) => s.trim())
      return { username: parts[0], password: parts[1], nickname: parts[2] || null, phone: parts[3] || null }
    }).filter((a) => a.username && a.password)
    await api.post(`/sites/${siteId}/accounts/import`, { accounts })
    ElMessage.success('导入成功')
    importVisible.value = false
    importText.value = ''
    loadData()
  } finally {
    importing.value = false
  }
}

function openEdit(row: any) {
  Object.assign(editForm, { id: row.id, username: row.username, password: '', nickname: row.nickname || '', phone: row.phone || '', is_active: row.is_active })
  editVisible.value = true
}

async function saveEdit() {
  const data: any = {}
  if (editForm.password) data.password = editForm.password
  data.nickname = editForm.nickname || null
  data.phone = editForm.phone || null
  data.is_active = editForm.is_active
  await api.put(`/sites/${siteId}/accounts/${editForm.id}`, data)
  ElMessage.success('保存成功')
  editVisible.value = false
  loadData()
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
  loadData()
  loadModules()
})
</script>

<style scoped>
.card-header { display: flex; justify-content: space-between; align-items: center; }
.toolbar { display: flex; align-items: center; }
</style>
