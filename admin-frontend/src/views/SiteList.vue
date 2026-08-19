<template>
  <div class="site-list">
    <!-- 搜索工具栏 -->
    <el-card shadow="never" class="search-card">
      <el-form :inline="true" :model="searchForm" class="search-form">
        <el-form-item label="微站名称">
          <el-input v-model="searchForm.keyword" placeholder="请输入微站名称" clearable style="width: 220px" @keyup.enter="loadData" />
        </el-form-item>
        <el-form-item label="状态">
          <el-select v-model="searchForm.status" placeholder="全部状态" clearable style="width: 140px" @change="loadData">
            <el-option label="草稿" value="draft" />
            <el-option label="在线" value="online" />
            <el-option label="已下线" value="offline" />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" :icon="Search" @click="loadData">查询</el-button>
          <el-button :icon="Refresh" @click="resetSearch">重置</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <!-- 表格区 -->
    <el-card shadow="never" class="table-card">
      <template #header>
        <div class="card-header">
          <span class="card-title">
            <el-icon><Monitor /></el-icon>
            微站列表
          </span>
          <el-button type="primary" :icon="Plus" @click="goCreate">创建微站</el-button>
        </div>
      </template>

      <el-table :data="list" v-loading="loading" stripe style="width: 100%">
        <el-table-column prop="id" label="ID" width="60" align="center" />
        <el-table-column prop="name" label="微站名称" min-width="150">
          <template #default="{ row }">
            <span class="site-name">{{ row.name }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="code" label="访问码" width="120" />
        <el-table-column label="模板" width="100" align="center">
          <template #default="{ row }">{{ templateMap[row.template] || row.template }}</template>
        </el-table-column>
        <el-table-column label="布局" width="100" align="center">
          <template #default="{ row }">{{ row.layout === 'grid' ? '九宫格' : '按钮' }}</template>
        </el-table-column>
        <el-table-column prop="need_login" label="登录" width="80" align="center">
          <template #default="{ row }">
            <el-tag :type="row.need_login ? 'warning' : 'info'" size="small">{{ row.need_login ? '需要' : '不需要' }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="状态" width="100" align="center">
          <template #default="{ row }">
            <el-tag :type="statusType(row.status)" size="small">{{ statusMap[row.status] }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="module_count" label="模块数" width="80" align="center" />
        <el-table-column prop="account_count" label="账号数" width="80" align="center" />
        <el-table-column label="操作" width="320" fixed="right">
          <template #default="{ row }">
            <el-button link size="small" @click="$router.push(`/sites/${row.id}/modules`)">模块</el-button>
            <el-button link size="small" v-if="row.need_login" @click="$router.push(`/sites/${row.id}/accounts`)">账号</el-button>
            <el-button link size="small" @click="$router.push(`/sites/${row.id}/stats`)">统计</el-button>
            <el-button link type="primary" size="small" @click="$router.push(`/sites/${row.id}/edit`)">编辑</el-button>
            <el-button link size="small" :type="row.status === 'online' ? 'danger' : 'success'" @click="toggleStatus(row)">
              {{ row.status === 'online' ? '下线' : '上线' }}
            </el-button>
            <el-popconfirm title="确认删除此微站？" @confirm="deleteSite(row)">
              <template #reference>
                <el-button link type="danger" size="small">删除</el-button>
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
        layout="total, sizes, prev, pager, next, jumper"
        style="margin-top: 16px"
        @size-change="loadData"
        @current-change="loadData"
      />
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Search, Refresh, Plus, Monitor } from '@element-plus/icons-vue'
import { useAuthStore } from '@/store/auth'
import { getWalletMe } from '@/api/billing'
import api from '@/api'

const router = useRouter()
const auth = useAuthStore()

const list = ref([])
const loading = ref(false)
const page = ref(1)
const pageSize = ref(20)
const total = ref(0)
const searchForm = reactive({ keyword: '', status: '' })

const templateMap: Record<string, string> = { classic: '经典', dark: '暗黑', festive: '节日' }
const statusMap: Record<string, string> = { draft: '草稿', online: '在线', offline: '已下线' }
const statusType = (s: string) => ({ draft: 'info', online: 'success', offline: 'danger' }[s] || 'info')

async function loadData() {
  loading.value = true
  try {
    const res: any = await api.get('/sites', {
      params: {
        page: page.value,
        page_size: pageSize.value,
        keyword: searchForm.keyword || undefined,
        status: searchForm.status || undefined,
      },
    })
    list.value = res.items
    total.value = res.total
  } finally {
    loading.value = false
  }
}

function resetSearch() {
  searchForm.keyword = ''
  searchForm.status = ''
  page.value = 1
  loadData()
}

// 商业化: 创建微站前校验会员状态
async function goCreate() {
  if (auth.isSuperAdmin) {
    router.push('/sites/create')
    return
  }
  try {
    const wallet = await getWalletMe()
    if (wallet.membership?.status === 'active') {
      router.push('/sites/create')
      return
    }
    ElMessageBox.confirm(
      wallet.membership?.status === 'expired' ? '您的会员已过期，续费后可创建微站' : '尚未开通会员，购买会员后可创建微站',
      '提示',
      { confirmButtonText: '前往会员中心', cancelButtonText: '取消', type: 'warning' }
    ).then(() => router.push('/billing')).catch(() => {})
  } catch {
    // 校验失败不阻塞
    router.push('/sites/create')
  }
}

// 商业化(v1.2): 上线前校验场次额度，不足引导去会员中心；下线不退额度
async function toggleStatus(row: any) {
  const newStatus = row.status === 'online' ? 'offline' : 'online'
  if (newStatus === 'online' && !auth.isSuperAdmin) {
    try {
      const wallet = await getWalletMe()
      if (!wallet.session_credits || wallet.session_credits <= 0) {
        ElMessageBox.confirm(
          '场次额度不足，微站每上线一次需消耗 1 个额度（299 元/次）。可前往会员中心购买。',
          '无法上线',
          { confirmButtonText: '前往会员中心', cancelButtonText: '取消', type: 'warning' }
        ).then(() => router.push('/billing')).catch(() => {})
        return
      }
    } catch {
      // 校验失败不阻塞，交给后端兜底
    }
  }
  await api.put(`/sites/${row.id}/status`, { status: newStatus })
  ElMessage.success(newStatus === 'online' ? '已上线（已消耗 1 个场次额度）' : '已下线')
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
.search-card {
  margin-bottom: 16px;
}
.search-card :deep(.el-card__body) {
  padding: 18px 20px 0;
}
.search-form {
  display: flex;
  flex-wrap: wrap;
}
.table-card :deep(.el-card__body) {
  padding: 0;
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
.site-name {
  font-weight: 500;
  color: #303133;
}
</style>
