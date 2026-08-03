<template>
  <div class="dashboard">
    <el-row :gutter="20">
      <el-col :span="6">
        <el-card shadow="hover" class="stat-card stat-blue">
          <div class="stat-value">{{ stats.total_sites }}</div>
          <div class="stat-label">微站总数</div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="hover" class="stat-card stat-green">
          <div class="stat-value">{{ stats.online_sites }}</div>
          <div class="stat-label">在线微站</div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="hover" class="stat-card stat-orange">
          <div class="stat-value">{{ stats.total_pv }}</div>
          <div class="stat-label">总访问量</div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="hover" class="stat-card stat-purple">
          <div class="stat-value">{{ stats.total_uv }}</div>
          <div class="stat-label">总访客数</div>
        </el-card>
      </el-col>
    </el-row>
    <el-card style="margin-top: 20px;">
      <template #header>快捷操作</template>
      <el-space wrap>
        <el-button type="primary" @click="$router.push('/sites/create')">创建微站</el-button>
        <el-button @click="$router.push('/sites')">管理微站</el-button>
      </el-space>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import api from '@/api'

const stats = ref({
  total_sites: 0,
  online_sites: 0,
  total_pv: 0,
  total_uv: 0,
})

onMounted(async () => {
  try {
    // 简单获取微站列表统计
    const res: any = await api.get('/sites', { params: { page: 1, page_size: 1 } })
    stats.value.total_sites = res.total
    // 在线数量后续补充
  } catch {}
})
</script>

<style scoped>
.stat-card { text-align: center; padding: 20px 0; }
.stat-value { font-size: 32px; font-weight: bold; }
.stat-label { color: #999; margin-top: 8px; }
.stat-blue { background: #e6f7ff; } .stat-blue .stat-value { color: #1890ff; }
.stat-green { background: #f6ffed; } .stat-green .stat-value { color: #52c41a; }
.stat-orange { background: #fff7e6; } .stat-orange .stat-value { color: #fa8c16; }
.stat-purple { background: #f9f0ff; } .stat-purple .stat-value { color: #722ed1; }
</style>
