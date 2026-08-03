<template>
  <div class="stats-page">
    <el-row :gutter="20">
      <el-col :span="6">
        <el-card shadow="hover" class="stat-card">
          <div class="stat-value">{{ overview.total_pv }}</div>
          <div class="stat-label">总访问量(PV)</div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="hover" class="stat-card">
          <div class="stat-value">{{ overview.total_uv }}</div>
          <div class="stat-label">总访客(UV)</div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="hover" class="stat-card">
          <div class="stat-value">{{ overview.today_pv }}</div>
          <div class="stat-label">今日PV</div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="hover" class="stat-card">
          <div class="stat-value">{{ overview.today_uv }}</div>
          <div class="stat-label">今日UV</div>
        </el-card>
      </el-col>
    </el-row>

    <el-card style="margin-top: 20px">
      <template #header>访问趋势(近30天)</template>
      <v-chart :option="trendOption" style="height: 300px" autoresize />
    </el-card>

    <el-card style="margin-top: 20px">
      <template #header>模块点击统计</template>
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
import api from '@/api'

use([CanvasRenderer, LineChart, BarChart, GridComponent, TooltipComponent, LegendComponent])

const route = useRoute()
const siteId = route.params.id as string

const overview = ref({ total_pv: 0, total_uv: 0, today_pv: 0, today_uv: 0, account_count: 0, module_count: 0 })
const trendData = ref<any[]>([])
const moduleData = ref<any[]>([])

const trendOption = computed(() => ({
  tooltip: { trigger: 'axis' },
  legend: { data: ['PV', 'UV'] },
  xAxis: { type: 'category', data: trendData.value.map((i) => i.date) },
  yAxis: { type: 'value' },
  series: [
    { name: 'PV', type: 'line', data: trendData.value.map((i) => i.pv), smooth: true, itemStyle: { color: '#1890ff' } },
    { name: 'UV', type: 'line', data: trendData.value.map((i) => i.uv), smooth: true, itemStyle: { color: '#52c41a' } },
  ],
}))

const moduleOption = computed(() => ({
  tooltip: { trigger: 'axis' },
  xAxis: { type: 'category', data: moduleData.value.map((i) => i.title), axisLabel: { rotate: 30 } },
  yAxis: { type: 'value' },
  series: [{ type: 'bar', data: moduleData.value.map((i) => i.click_count), itemStyle: { color: '#722ed1' } }],
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
.stat-card { text-align: center; padding: 20px 0; }
.stat-value { font-size: 28px; font-weight: bold; color: #1890ff; }
.stat-label { color: #999; margin-top: 8px; }
</style>
