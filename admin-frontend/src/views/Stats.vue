<template>
  <div class="stats-page">
    <!-- 统计卡片 -->
    <el-row :gutter="16" class="stat-row">
      <el-col :xs="12" :sm="12" :md="6" v-for="(item, index) in statCards" :key="index">
        <div class="stat-card" :class="'stat-' + item.theme">
          <div class="stat-icon-wrap">
            <el-icon :size="24"><component :is="item.icon" /></el-icon>
          </div>
          <div class="stat-body">
            <div class="stat-value">{{ item.value }}</div>
            <div class="stat-label">{{ item.label }}</div>
          </div>
        </div>
      </el-col>
    </el-row>

    <el-card shadow="never" style="margin-top: 16px">
      <template #header>
        <div class="card-title"><el-icon><TrendCharts /></el-icon>访问趋势（近30天）</div>
      </template>
      <v-chart :option="trendOption" style="height: 300px" autoresize />
    </el-card>

    <el-card shadow="never" style="margin-top: 16px">
      <template #header>
        <div class="card-title"><el-icon><DataAnalysis /></el-icon>模块点击统计</div>
      </template>
      <v-chart :option="moduleOption" style="height: 300px" autoresize />
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useRoute } from 'vue-router'
import { use } from 'echarts/core'
import { CanvasRenderer } from 'echarts/renderers'
import { LineChart, BarChart } from 'echarts/charts'
import { GridComponent, TooltipComponent, LegendComponent } from 'echarts/components'
import VChart from 'vue-echarts'
import { TrendCharts, DataAnalysis, View, User } from '@element-plus/icons-vue'
import api from '@/api'

use([CanvasRenderer, LineChart, BarChart, GridComponent, TooltipComponent, LegendComponent])

const route = useRoute()
const siteId = route.params.id as string

const overview = ref({ total_pv: 0, total_uv: 0, today_pv: 0, today_uv: 0, account_count: 0, module_count: 0 })
const trendData = ref<any[]>([])
const moduleData = ref<any[]>([])

const statCards = computed(() => [
  { label: '总访问量(PV)', value: overview.value.total_pv, theme: 'blue', icon: 'View' },
  { label: '总访客(UV)', value: overview.value.total_uv, theme: 'green', icon: 'User' },
  { label: '今日PV', value: overview.value.today_pv, theme: 'orange', icon: 'TrendCharts' },
  { label: '今日UV', value: overview.value.today_uv, theme: 'purple', icon: 'DataAnalysis' },
])

const trendOption = computed(() => ({
  tooltip: { trigger: 'axis' },
  legend: { data: ['PV', 'UV'] },
  grid: { left: '3%', right: '4%', bottom: '3%', containLabel: true },
  xAxis: { type: 'category', data: trendData.value.map((i) => i.date), boundaryGap: false },
  yAxis: { type: 'value' },
  series: [
    { name: 'PV', type: 'line', data: trendData.value.map((i) => i.pv), smooth: true, itemStyle: { color: '#409eff' }, areaStyle: { color: 'rgba(64,158,255,0.15)' } },
    { name: 'UV', type: 'line', data: trendData.value.map((i) => i.uv), smooth: true, itemStyle: { color: '#67c23a' }, areaStyle: { color: 'rgba(103,194,58,0.15)' } },
  ],
}))

const moduleOption = computed(() => ({
  tooltip: { trigger: 'axis' },
  grid: { left: '3%', right: '4%', bottom: '3%', containLabel: true },
  xAxis: { type: 'category', data: moduleData.value.map((i) => i.title), axisLabel: { rotate: 30 } },
  yAxis: { type: 'value' },
  series: [{ type: 'bar', data: moduleData.value.map((i) => i.click_count), itemStyle: { color: '#409eff', borderRadius: [4, 4, 0, 0] } }],
}))

async function loadData() {
  const [ov, tr, ml]: any[] = await Promise.all([
    api.get(`/sites/${siteId}/stats/overview`),
    api.get(`/sites/${siteId}/stats/trend`, { params: { days: 30 } }),
    api.get(`/sites/${siteId}/stats/modules`),
  ])
  overview.value = ov
  trendData.value = tr.items
  moduleData.value = ml
}

onMounted(loadData)
</script>

<style scoped>
.stat-card {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 20px;
  background: #fff;
  border-radius: 4px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04);
  transition: all var(--transition-time-02);
  margin-bottom: 16px;
}
.stat-card:hover {
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.08);
  transform: translateY(-2px);
}
.stat-icon-wrap {
  width: 52px;
  height: 52px;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}
.stat-body {
  flex: 1;
  min-width: 0;
}
.stat-value {
  font-size: 26px;
  font-weight: 700;
  line-height: 1.2;
}
.stat-label {
  font-size: 13px;
  color: #909399;
  margin-top: 4px;
}
.stat-blue .stat-icon-wrap { background: #e8f3ff; color: #409eff; }
.stat-blue .stat-value { color: #409eff; }
.stat-green .stat-icon-wrap { background: #e8f7e8; color: #67c23a; }
.stat-green .stat-value { color: #67c23a; }
.stat-orange .stat-icon-wrap { background: #fdf3e8; color: #e6a23c; }
.stat-orange .stat-value { color: #e6a23c; }
.stat-purple .stat-icon-wrap { background: #f3e8ff; color: #8b5cf6; }
.stat-purple .stat-value { color: #8b5cf6; }

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
