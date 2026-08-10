<template>
  <div class="checkin-list">
    <!-- 顶部统计 -->
    <el-row :gutter="16" class="stat-row">
      <el-col :span="8">
        <el-card shadow="never" class="stat-card">
          <div class="stat-num">{{ stats.enabled }}</div>
          <div class="stat-label">开启签到项目数</div>
        </el-card>
      </el-col>
      <el-col :span="8">
        <el-card shadow="never" class="stat-card">
          <div class="stat-num">{{ stats.checkedIn }}</div>
          <div class="stat-label">累计签到人数</div>
        </el-card>
      </el-col>
      <el-col :span="8">
        <el-card shadow="never" class="stat-card">
          <div class="stat-num">{{ stats.registered }}</div>
          <div class="stat-label">累计报名人数</div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 搜索工具栏 -->
    <el-card shadow="never" class="search-card">
      <el-form :inline="true" class="search-form">
        <el-form-item label="项目名称">
          <el-input v-model="keyword" placeholder="请输入项目名称" clearable style="width: 220px" @keyup.enter="loadData" />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="loadData">查询</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <!-- 表格区 -->
    <el-card shadow="never" class="table-card">
      <template #header>
        <div class="card-header">
          <span class="card-title">签到项目列表</span>
          <span class="card-tip">来源于微站管理中开启签到的项目</span>
        </div>
      </template>

      <el-table :data="list" v-loading="loading" stripe style="width: 100%">
        <el-table-column prop="id" label="ID" width="70" align="center" />
        <el-table-column prop="name" label="项目名称" min-width="160">
          <template #default="{ row }">
            <span class="site-name">{{ row.name }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="code" label="访问码" width="110" />
        <el-table-column label="签到状态" width="110" align="center">
          <template #default="{ row }">
            <el-tag :type="row.checkin_enabled ? 'success' : 'info'" size="small">
              {{ row.checkin_enabled ? '已开启' : '未开启' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="场次" width="90" align="center">
          <template #default="{ row }">
            <el-tag size="small" :type="row.session_count > 0 ? 'primary' : 'info'">{{ row.session_count || 0 }}场</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="registered_count" label="报名人数" width="100" align="center" />
        <el-table-column prop="checked_in_count" label="已签到" width="90" align="center" />
        <el-table-column label="操作" width="120" fixed="right" align="center">
          <template #default="{ row }">
            <el-button link type="primary" size="small" @click="$router.push(`/checkin/${row.id}`)">管理签到</el-button>
          </template>
        </el-table-column>
      </el-table>

      <el-pagination
        v-model:current-page="page"
        v-model:page-size="pageSize"
        :total="total"
        :page-sizes="[10, 20, 50]"
        layout="total, sizes, prev, pager, next, jumper"
        class="pagination"
        @current-change="loadData"
        @size-change="loadData"
      />
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import request from '@/api'

const loading = ref(false)
const list = ref<any[]>([])
const total = ref(0)
const page = ref(1)
const pageSize = ref(10)
const keyword = ref('')
const stats = reactive({ enabled: 0, checkedIn: 0, registered: 0 })

function fmtTime(t: string | null): string {
  if (!t) return '不限'
  return t.replace('T', ' ').slice(0, 16)
}

async function loadData() {
  loading.value = true
  try {
    const data: any = await request.get('/checkin/projects', {
      params: { page: page.value, page_size: pageSize.value, keyword: keyword.value || undefined },
    })
    list.value = data.items || []
    total.value = data.total || 0
    stats.enabled = list.value.length
    stats.checkedIn = list.value.reduce((s: number, it: any) => s + (it.checked_in_count || 0), 0)
    stats.registered = list.value.reduce((s: number, it: any) => s + (it.registered_count || 0), 0)
  } finally {
    loading.value = false
  }
}

onMounted(loadData)
</script>

<style scoped>
.stat-row {
  margin-bottom: 16px;
}
.stat-card {
  text-align: center;
  padding: 4px 0;
}
.stat-num {
  font-size: 30px;
  font-weight: 700;
  color: #409eff;
}
.stat-label {
  margin-top: 6px;
  color: #909399;
  font-size: 13px;
}
.search-card {
  margin-bottom: 16px;
}
.search-form {
  margin-bottom: 0;
}
.table-card {
  margin-bottom: 16px;
}
.card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
}
.card-title {
  font-weight: 600;
}
.card-tip {
  color: #909399;
  font-size: 12px;
}
.site-name {
  font-weight: 500;
}
.no-window {
  color: #909399;
}
.pagination {
  margin-top: 16px;
  justify-content: flex-end;
}
</style>
