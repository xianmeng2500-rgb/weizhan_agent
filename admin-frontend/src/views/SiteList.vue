<template>
  <div class="site-list">
    <div class="toolbar">
      <el-input v-model="keyword" placeholder="搜索微站名称" style="width: 250px" clearable @clear="loadData" @keyup.enter="loadData" />
      <el-select v-model="statusFilter" placeholder="状态筛选" clearable style="width: 150px; margin-left: 10px" @change="loadData">
        <el-option label="草稿" value="draft" />
        <el-option label="在线" value="online" />
        <el-option label="已下线" value="offline" />
      </el-select>
      <el-button type="primary" style="margin-left: 10px" @click="loadData">搜索</el-button>
      <el-button type="success" @click="$router.push('/sites/create')">创建微站</el-button>
    </div>

    <el-table :data="list" v-loading="loading" border stripe style="margin-top: 16px">
      <el-table-column prop="id" label="ID" width="60" />
      <el-table-column prop="name" label="微站名称" min-width="150" />
      <el-table-column prop="code" label="访问码" width="120" />
      <el-table-column label="模板" width="100">
        <template #default="{ row }">{{ templateMap[row.template] || row.template }}</template>
      </el-table-column>
      <el-table-column label="布局" width="100">
        <template #default="{ row }">{{ row.layout === 'grid' ? '九宫格' : '按钮' }}</template>
      </el-table-column>
      <el-table-column prop="need_login" label="登录" width="80">
        <template #default="{ row }">
          <el-tag :type="row.need_login ? 'warning' : 'info'" size="small">{{ row.need_login ? '需要' : '不需要' }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column label="状态" width="100">
        <template #default="{ row }">
          <el-tag :type="statusType(row.status)" size="small">{{ statusMap[row.status] }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="module_count" label="模块数" width="80" />
      <el-table-column prop="account_count" label="账号数" width="80" />
      <el-table-column label="操作" width="320" fixed="right">
        <template #default="{ row }">
          <el-button size="small" @click="$router.push(`/sites/${row.id}/modules`)">模块</el-button>
          <el-button size="small" @click="$router.push(`/sites/${row.id}/accounts`)" v-if="row.need_login">账号</el-button>
          <el-button size="small" @click="$router.push(`/sites/${row.id}/stats`)">统计</el-button>
          <el-button size="small" type="primary" @click="$router.push(`/sites/${row.id}/edit`)">编辑</el-button>
          <el-button size="small" :type="row.status === 'online' ? 'danger' : 'success'" @click="toggleStatus(row)">
            {{ row.status === 'online' ? '下线' : '上线' }}
          </el-button>
          <el-popconfirm title="确认删除此微站？" @confirm="deleteSite(row)">
            <template #reference>
              <el-button size="small" type="danger">删除</el-button>
            </template>
          </el-popconfirm>
        </template>
      </el-table-column>
    </el-table>

    <el-pagination
      v-model:current-page="page"
      v-model:page-size="pageSize"
      :total="total"
      :page-sizes="[10, 20, 50]"
      layout="total, sizes, prev, pager, next"
      style="margin-top: 16px; justify-content: flex-end"
      @size-change="loadData"
      @current-change="loadData"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import api from '@/api'

const list = ref([])
const loading = ref(false)
const page = ref(1)
const pageSize = ref(20)
const total = ref(0)
const keyword = ref('')
const statusFilter = ref('')

const templateMap: Record<string, string> = { classic: '经典', dark: '暗黑', festive: '节日' }
const statusMap: Record<string, string> = { draft: '草稿', online: '在线', offline: '已下线' }
const statusType = (s: string) => ({ draft: 'info', online: 'success', offline: 'danger' }[s] || 'info')

async function loadData() {
  loading.value = true
  try {
    const res: any = await api.get('/sites', {
      params: { page: page.value, page_size: pageSize.value, keyword: keyword.value || undefined, status: statusFilter.value || undefined },
    })
    list.value = res.items
    total.value = res.total
  } finally {
    loading.value = false
  }
}

async function toggleStatus(row: any) {
  const newStatus = row.status === 'online' ? 'offline' : 'online'
  await api.put(`/sites/${row.id}/status`, { status: newStatus })
  ElMessage.success(newStatus === 'online' ? '已上线' : '已下线')
  loadData()
}

async function deleteSite(row: any) {
  await api.delete(`/sites/${row.id}`)
  ElMessage.success('已删除')
  loadData()
}

onMounted(loadData)
</script>

<style scoped>
.toolbar { display: flex; align-items: center; }
</style>
