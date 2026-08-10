<template>
  <div class="admin-accounts">
    <el-card shadow="never">
      <template #header>
        <div class="card-header">
          <span class="card-title">
            <el-icon><UserFilled /></el-icon>
            后台账号管理
          </span>
          <el-button v-if="auth.canManageAccounts" type="primary" :icon="Plus" @click="openCreate">新增账号</el-button>
        </div>
      </template>

      <el-alert
        v-if="!auth.canManageAccounts"
        type="warning"
        :closable="false"
        title="当前账号无权限访问此页面（仅超级管理员和管理员可管理后台账号）"
        show-icon
      />

      <template v-else>
        <el-table :data="list" v-loading="loading" stripe>
          <el-table-column prop="username" label="用户名" min-width="120" />
          <el-table-column prop="nickname" label="昵称" min-width="120" />
          <el-table-column label="角色" width="120" align="center">
            <template #default="{ row }">
              <el-tag :type="roleTagType(row.role)" size="small">{{ roleText(row.role) }}</el-tag>
            </template>
          </el-table-column>
          <el-table-column label="状态" width="90" align="center">
            <template #default="{ row }">
              <el-tag :type="row.is_active ? 'success' : 'info'" size="small" effect="plain">{{ row.is_active ? '启用' : '禁用' }}</el-tag>
            </template>
          </el-table-column>
          <el-table-column label="创建时间" min-width="160">
            <template #default="{ row }">{{ formatTime(row.created_at) }}</template>
          </el-table-column>
          <el-table-column label="操作" width="160" fixed="right">
            <template #default="{ row }">
              <el-button link size="small" @click="openEdit(row)">编辑</el-button>
              <el-popconfirm title="确认删除该账号？" @confirm="removeAccount(row)">
                <template #reference><el-button link type="danger" size="small">删除</el-button></template>
              </el-popconfirm>
            </template>
          </el-table-column>
        </el-table>
      </template>
    </el-card>

    <!-- 新增/编辑弹窗 -->
    <el-dialog v-model="dialogVisible" :title="editing.id ? '编辑账号' : '新增账号'" width="520px" :close-on-click-modal="false">
      <el-form :model="editing" label-width="90px">
        <el-form-item label="用户名" required>
          <el-input v-model="editing.username" :disabled="!!editing.id" placeholder="登录用户名" />
        </el-form-item>
        <el-form-item :label="editing.id ? '重置密码' : '密码'" required>
          <el-input
            v-model="editing.password"
            type="password"
            show-password
            :placeholder="editing.id ? '留空则不修改' : '至少6位'"
          />
        </el-form-item>
        <el-form-item label="昵称">
          <el-input v-model="editing.nickname" placeholder="昵称" />
        </el-form-item>
        <el-form-item label="角色">
          <el-select v-model="editing.role" :disabled="auth.role !== 'super_admin' && !!editing.id" placeholder="选择角色">
            <el-option v-for="opt in roleOptions" :key="opt.value" :label="opt.label" :value="opt.value" />
          </el-select>
        </el-form-item>
        <el-form-item v-if="editing.id" label="启用">
          <el-switch v-model="editing.is_active" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="save">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue'
import { useAuthStore } from '@/store/auth'
import { ElMessage } from 'element-plus'
import { UserFilled, Plus } from '@element-plus/icons-vue'
import api from '@/api'
import dayjs from 'dayjs'

const auth = useAuthStore()
const list = ref<any[]>([])
const loading = ref(false)
const saving = ref(false)
const dialogVisible = ref(false)

// 当前用户可选的角色
const roleOptions = computed(() => {
  if (auth.role === 'super_admin') {
    return [
      { value: 'super_admin', label: '超级管理员' },
      { value: 'admin', label: '管理员' },
      { value: 'sub_admin', label: '子账号' },
    ]
  }
  // 管理员只能创建子账号
  return [{ value: 'sub_admin', label: '子账号' }]
})

const editing = reactive({
  id: null as number | null,
  username: '',
  password: '',
  nickname: '',
  role: 'sub_admin',
  is_active: true,
})

function roleText(role: string) {
  const map: Record<string, string> = {
    super_admin: '超级管理员',
    admin: '管理员',
    sub_admin: '子账号',
  }
  return map[role] || role
}

function roleTagType(role: string) {
  if (role === 'super_admin') return 'danger'
  if (role === 'admin') return 'warning'
  return 'info'
}

function formatTime(t: string) {
  return t ? dayjs(t).format('YYYY-MM-DD HH:mm') : '-'
}

async function loadData() {
  if (!auth.canManageAccounts) return
  loading.value = true
  try {
    const res: any = await api.get('/auth/accounts')
    list.value = res || []
  } finally {
    loading.value = false
  }
}

function openCreate() {
  Object.assign(editing, {
    id: null,
    username: '',
    password: '',
    nickname: '',
    role: 'sub_admin',
    is_active: true,
  })
  dialogVisible.value = true
}

function openEdit(row: any) {
  Object.assign(editing, {
    id: row.id,
    username: row.username,
    password: '',
    nickname: row.nickname || '',
    role: row.role,
    is_active: row.is_active,
  })
  dialogVisible.value = true
}

async function save() {
  if (!editing.username) { ElMessage.warning('请输入用户名'); return }
  if (!editing.id && !editing.password) { ElMessage.warning('请输入密码'); return }
  if (editing.password && editing.password.length < 6) { ElMessage.warning('密码至少6位'); return }
  saving.value = true
  try {
    const data: Record<string, any> = {
      username: editing.username,
      nickname: editing.nickname || null,
      role: editing.role,
    }
    if (editing.password) data.password = editing.password
    if (editing.id) {
      data.is_active = editing.is_active
      await api.put(`/auth/accounts/${editing.id}`, data)
      ElMessage.success('更新成功')
    } else {
      await api.post('/auth/accounts', data)
      ElMessage.success('创建成功')
    }
    dialogVisible.value = false
    loadData()
  } finally {
    saving.value = false
  }
}

async function removeAccount(row: any) {
  try {
    await api.delete(`/auth/accounts/${row.id}`)
    ElMessage.success('已删除')
    loadData()
  } catch {
    // 拦截器已提示
  }
}

onMounted(loadData)
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
</style>
