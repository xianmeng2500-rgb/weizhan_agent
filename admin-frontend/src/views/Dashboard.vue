<template>
  <div class="dashboard">
    <!-- 欢迎横幅 -->
    <div class="welcome-banner">
      <div>
        <div class="banner-title">{{ greeting }}，{{ auth.nickname || '朋友' }}</div>
        <div class="banner-sub">欢迎使用微站系统，今天也要加油运营哦</div>
      </div>
      <div class="banner-date">{{ todayText }}</div>
    </div>

    <!-- 统计卡片 -->
    <el-row :gutter="16" class="stat-row">
      <el-col :xs="12" :sm="8" :md="4" v-for="(item, index) in statCards" :key="index">
        <div class="stat-card" :class="'stat-' + item.theme">
          <div class="stat-icon-wrap">
            <el-icon :size="26"><component :is="item.icon" /></el-icon>
          </div>
          <div class="stat-body">
            <div class="stat-value">{{ item.value }}</div>
            <div class="stat-label">{{ item.label }}</div>
          </div>
        </div>
      </el-col>
    </el-row>

    <!-- 经营数据（超管）/ 账户状态（普通用户） -->
    <el-row :gutter="16" class="second-row">
      <template v-if="auth.isSuperAdmin">
        <el-col :xs="24" :md="12">
          <el-card shadow="hover">
            <template #header>
              <div class="card-header">
                <span class="card-title"><el-icon><TrendCharts /></el-icon>收入统计</span>
                <el-button link type="primary" @click="$router.push('/admin/members')">会员管理</el-button>
              </div>
            </template>
            <div class="metric-grid">
              <div class="metric-item" v-for="m in revenueMetrics" :key="m.label">
                <div class="metric-value">{{ m.value }}</div>
                <div class="metric-label">{{ m.label }}</div>
              </div>
            </div>
          </el-card>
        </el-col>
        <el-col :xs="24" :md="12">
          <el-card shadow="hover">
            <template #header>
              <div class="card-header">
                <span class="card-title"><el-icon><Money /></el-icon>分销概况</span>
                <el-button link type="primary" @click="$router.push('/admin/distribution')">分销管理</el-button>
              </div>
            </template>
            <div class="metric-grid">
              <div class="metric-item" v-for="m in distMetrics" :key="m.label">
                <div class="metric-value">{{ m.value }}</div>
                <div class="metric-label">{{ m.label }}</div>
              </div>
            </div>
          </el-card>
        </el-col>
      </template>
      <template v-else>
        <el-col :xs="24" :md="12">
          <el-card shadow="hover">
            <template #header>
              <div class="card-header">
                <span class="card-title"><el-icon><Wallet /></el-icon>我的账户</span>
                <el-button link type="primary" @click="$router.push('/billing')">会员中心</el-button>
              </div>
            </template>
            <div class="metric-grid">
              <div class="metric-item">
                <div class="metric-value">{{ walletBalanceText }}<span class="metric-unit"> 元</span></div>
                <div class="metric-label">钱包余额</div>
              </div>
              <div class="metric-item">
                <div class="metric-value">
                  <el-tag v-if="wallet?.membership?.status === 'active'" type="success" effect="plain" size="small">生效中</el-tag>
                  <el-tag v-else-if="wallet?.membership?.status === 'expired'" type="danger" effect="plain" size="small">已过期</el-tag>
                  <el-tag v-else type="info" effect="plain" size="small">未开通</el-tag>
                </div>
                <div class="metric-label">会员状态</div>
              </div>
              <div class="metric-item">
                <div class="metric-value">{{ wallet?.session_credits ?? 0 }}<span class="metric-unit"> 次</span></div>
                <div class="metric-label">剩余上线额度</div>
              </div>
              <div class="metric-item">
                <div class="metric-value">{{ distInfo.total_rebate > 0 ? '¥' + yuan(distInfo.total_rebate) : '-' }}</div>
                <div class="metric-label">累计返佣</div>
              </div>
            </div>
          </el-card>
        </el-col>
        <el-col :xs="24" :md="12">
          <el-card shadow="hover">
            <template #header>
              <div class="card-header">
                <span class="card-title"><el-icon><Promotion /></el-icon>我的推广</span>
                <el-button link type="primary" @click="$router.push('/distribution')">推广中心</el-button>
              </div>
            </template>
            <div class="metric-grid">
              <div class="metric-item">
                <div class="metric-value promo-code">{{ distInfo.recommend_code || '--' }}</div>
                <div class="metric-label">我的推广码</div>
              </div>
              <div class="metric-item">
                <div class="metric-value">{{ distInfo.referral_count }}</div>
                <div class="metric-label">累计拉新</div>
              </div>
              <div class="metric-item">
                <div class="metric-value">{{ distInfo.total_order_amount > 0 ? '¥' + yuan(distInfo.total_order_amount) : '-' }}</div>
                <div class="metric-label">累计成交</div>
              </div>
              <div class="metric-item">
                <div class="metric-value">{{ distInfo.enabled ? distInfo.rebate_rate + '%' : '未开启' }}</div>
                <div class="metric-label">当前返佣比例</div>
              </div>
            </div>
          </el-card>
        </el-col>
      </template>
    </el-row>

    <!-- 访问趋势 + 最近微站 -->
    <el-row :gutter="16" class="third-row">
      <el-col :xs="24" :md="16">
        <el-card shadow="hover">
          <template #header>
            <div class="card-header">
              <span class="card-title"><el-icon><DataLine /></el-icon>访问趋势（近 14 天）</span>
            </div>
          </template>
          <VChart v-if="trendData.length" :option="trendOption" class="trend-chart" autoresize />
          <el-empty v-else description="暂无访问数据" :image-size="80" />
        </el-card>
      </el-col>
      <el-col :xs="24" :md="8">
        <el-card shadow="hover" class="recent-card">
          <template #header>
            <div class="card-header">
              <span class="card-title"><el-icon><Monitor /></el-icon>最近微站</span>
              <el-button link type="primary" @click="$router.push('/sites')">查看全部</el-button>
            </div>
          </template>
          <div v-loading="sitesLoading" class="recent-list">
            <div v-for="site in recentSites" :key="site.id" class="recent-item" @click="$router.push(`/sites/${site.id}/edit`)">
              <div class="recent-info">
                <div class="recent-name">{{ site.name }}</div>
                <div class="recent-meta">创建于 {{ fmtDate(site.created_at) }}</div>
              </div>
              <el-tag :type="site.status === 'online' ? 'success' : site.status === 'offline' ? 'info' : 'warning'" size="small" effect="plain">
                {{ site.status === 'online' ? '在线' : site.status === 'offline' ? '已下线' : '草稿' }}
              </el-tag>
            </div>
            <el-empty v-if="!sitesLoading && recentSites.length === 0" description="还没有微站，去创建一个吧" :image-size="60">
              <el-button type="primary" size="small" @click="$router.push('/sites/create')">创建微站</el-button>
            </el-empty>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 快捷操作 + 个人信息 -->
    <el-row :gutter="16" class="fourth-row">
      <el-col :xs="24" :md="16">
        <el-card shadow="hover">
          <template #header>
            <div class="card-header">
              <span class="card-title"><el-icon><Promotion /></el-icon>快捷操作</span>
            </div>
          </template>
          <div class="quick-actions">
            <div class="action-item" @click="$router.push('/sites/create')">
              <div class="action-icon action-icon-blue"><el-icon :size="24"><Plus /></el-icon></div>
              <span class="action-text">创建微站</span>
            </div>
            <div class="action-item" @click="$router.push('/sites')">
              <div class="action-icon action-icon-cyan"><el-icon :size="24"><Monitor /></el-icon></div>
              <span class="action-text">管理微站</span>
            </div>
            <div class="action-item" @click="$router.push('/templates')" v-if="auth.canManageAccounts">
              <div class="action-icon action-icon-orange"><el-icon :size="24"><Files /></el-icon></div>
              <span class="action-text">模板管理</span>
            </div>
            <div class="action-item" @click="$router.push('/ai-generate')">
              <div class="action-icon action-icon-purple"><el-icon :size="24"><MagicStick /></el-icon></div>
              <span class="action-text">AI 生图</span>
            </div>
            <div class="action-item" @click="$router.push('/checkin')">
              <div class="action-icon action-icon-green"><el-icon :size="24"><Checked /></el-icon></div>
              <span class="action-text">签到管理</span>
            </div>
            <div class="action-item" @click="$router.push('/distribution')">
              <div class="action-icon action-icon-pink"><el-icon :size="24"><Share /></el-icon></div>
              <span class="action-text">推广中心</span>
            </div>
            <div class="action-item" @click="$router.push('/admin/accounts')" v-if="auth.canManageAccounts">
              <div class="action-icon action-icon-cyan"><el-icon :size="24"><UserFilled /></el-icon></div>
              <span class="action-text">账号管理</span>
            </div>
            <div class="action-item" @click="$router.push('/admin/system-config')" v-if="auth.isSuperAdmin">
              <div class="action-icon action-icon-orange"><el-icon :size="24"><Setting /></el-icon></div>
              <span class="action-text">系统配置</span>
            </div>
          </div>
        </el-card>
      </el-col>
      <el-col :xs="24" :md="8">
        <el-card shadow="hover" class="welcome-card">
          <template #header>
            <div class="card-header">
              <span class="card-title"><el-icon><User /></el-icon>个人信息</span>
            </div>
          </template>
          <div class="welcome-body">
            <el-avatar :size="56" class="welcome-avatar">{{ (auth.nickname || 'U').charAt(0).toUpperCase() }}</el-avatar>
            <div class="welcome-info">
              <div class="welcome-name">{{ auth.nickname }}</div>
              <el-tag size="small" :type="auth.role === 'super_admin' ? 'danger' : auth.role === 'admin' ? 'warning' : 'info'" effect="plain">
                {{ roleText }}
              </el-tag>
              <div class="welcome-meta">{{ auth.isSuperAdmin ? '平台运营方' : '商家运营者' }}</div>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue'
import { use } from 'echarts/core'
import { CanvasRenderer } from 'echarts/renderers'
import { LineChart } from 'echarts/charts'
import { GridComponent, TooltipComponent, LegendComponent } from 'echarts/components'
import VChart from 'vue-echarts'
import api from '@/api'
import { useAuthStore } from '@/store/auth'
import { Plus, Monitor, UserFilled, Setting, Promotion, User, TrendCharts, Money, Wallet, DataLine, MagicStick, Checked, Files, Share, CircleCheck, View, DataAnalysis } from '@element-plus/icons-vue'
import { getWalletMe, fmtYuan } from '@/api/billing'
import dayjs from 'dayjs'

use([CanvasRenderer, LineChart, GridComponent, TooltipComponent, LegendComponent])

const auth = useAuthStore()

// ---- 欢迎横幅 ----
const greeting = computed(() => {
  const h = new Date().getHours()
  if (h < 6) return '夜深了'
  if (h < 12) return '早上好'
  if (h < 14) return '中午好'
  if (h < 18) return '下午好'
  return '晚上好'
})
const todayText = dayjs().format('YYYY年MM月DD日')

// ---- 统计卡 ----
const stats = ref({
  total_sites: 0,
  online_sites: 0,
  total_pv: 0,
  total_uv: 0,
  today_pv: 0,
  today_uv: 0,
})
const statCards = computed(() => [
  { label: '微站总数', value: stats.value.total_sites, theme: 'blue', icon: 'Monitor' },
  { label: '在线微站', value: stats.value.online_sites, theme: 'green', icon: 'CircleCheck' },
  { label: '今日访问', value: stats.value.today_pv, theme: 'orange', icon: 'View' },
  { label: '今日访客', value: stats.value.today_uv, theme: 'purple', icon: 'User' },
  { label: '总访问量', value: stats.value.total_pv, theme: 'cyan', icon: 'TrendCharts' },
  { label: '总访客数', value: stats.value.total_uv, theme: 'pink', icon: 'DataAnalysis' },
])

// ---- 访问趋势 ----
const trendData = ref<any[]>([])
const trendOption = computed(() => ({
  tooltip: { trigger: 'axis' },
  legend: { data: ['PV', 'UV'], top: 0 },
  grid: { left: '3%', right: '4%', bottom: '3%', containLabel: true },
  xAxis: { type: 'category', data: trendData.value.map((i) => dayjs(i.date).format('MM-DD')), boundaryGap: false },
  yAxis: { type: 'value' },
  series: [
    { name: 'PV', type: 'line', data: trendData.value.map((i) => i.pv), smooth: true, itemStyle: { color: '#409eff' }, areaStyle: { color: 'rgba(64,158,255,0.12)' } },
    { name: 'UV', type: 'line', data: trendData.value.map((i) => i.uv), smooth: true, itemStyle: { color: '#67c23a' }, areaStyle: { color: 'rgba(103,194,58,0.12)' } },
  ],
}))

// ---- 最近微站 ----
const recentSites = ref<any[]>([])
const sitesLoading = ref(false)
function fmtDate(v: string) {
  return v ? dayjs(v).format('YYYY-MM-DD') : '-'
}

// ---- 账户/经营数据 ----
const wallet = ref<any>(null)
const walletBalanceText = computed(() => (wallet.value ? fmtYuan(wallet.value.balance) : '0.00'))

const revenueMetrics = ref<{ label: string; value: string }[]>([])
const distMetrics = ref<{ label: string; value: string }[]>([])

const distInfo = reactive({
  recommend_code: '',
  enabled: false,
  rebate_rate: 0,
  referral_count: 0,
  total_order_amount: 0,
  total_rebate: 0,
})

function yuan(cents: number) {
  return (cents / 100).toFixed(2)
}

const roleText = computed(() => {
  const map: Record<string, string> = { super_admin: '超级管理员', admin: '管理员', sub_admin: '子账号' }
  return map[auth.role] || auth.role
})

onMounted(async () => {
  const tasks: Promise<any>[] = [
    api.get('/stats/overview').then((res: any) => Object.assign(stats.value, res || {})).catch(() => {}),
    api.get('/stats/trend', { params: { days: 14 } }).then((res: any) => (trendData.value = res?.items || [])).catch(() => {}),
    api.get('/sites', { params: { page: 1, page_size: 5 } }).then((res: any) => (recentSites.value = res?.items || [])).catch(() => {}),
  ]

  if (auth.isSuperAdmin) {
    tasks.push(
      api.get('/admin/billing/revenue/stats').then((res: any) => {
        if (!res) return
        revenueMetrics.value = [
          { label: '总充值', value: '¥' + yuan(res.total_recharge || 0) },
          { label: '总消费', value: '¥' + yuan(res.total_consume || 0) },
          { label: '总退款', value: '¥' + yuan(res.total_refund || 0) },
          { label: '活跃会员', value: String(res.active_members || 0) },
        ]
      }).catch(() => {}),
      api.get('/distribution/admin/stats').then((res: any) => {
        if (!res) return
        distMetrics.value = [
          { label: '累计拉新', value: String(res.referral_count || 0) },
          { label: '成交总额', value: '¥' + yuan(res.total_order_amount || 0) },
          { label: '返佣支出', value: '¥' + yuan(res.total_rebate || 0) },
          { label: '活跃分销商', value: String(res.distributor_count || 0) },
        ]
      }).catch(() => {}),
    )
  } else {
    tasks.push(
      getWalletMe().then((res: any) => (wallet.value = res)).catch(() => (wallet.value = null)),
      api.get('/distribution/my-code').then((res: any) => Object.assign(distInfo, res || {})).catch(() => {}),
    )
  }

  await Promise.all(tasks)
})
</script>

<style scoped>
.dashboard {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

/* 欢迎横幅 */
.welcome-banner {
  display: flex;
  align-items: center;
  justify-content: space-between;
  background: linear-gradient(120deg, #2b6cb0, #409eff);
  border-radius: 8px;
  padding: 20px 24px;
  color: #fff;
}
.banner-title {
  font-size: 20px;
  font-weight: 600;
}
.banner-sub {
  margin-top: 6px;
  font-size: 13px;
  opacity: 0.85;
}
.banner-date {
  font-size: 14px;
  opacity: 0.9;
}

/* 统计卡片 */
.stat-card {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 18px 16px;
  background: #fff;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04);
  transition: all var(--transition-time-02);
  margin-bottom: 16px;
  height: 100%;
  box-sizing: border-box;
}
.stat-card:hover {
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.08);
  transform: translateY(-2px);
}
.stat-icon-wrap {
  width: 46px;
  height: 46px;
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
  font-size: 22px;
  font-weight: 700;
  line-height: 1.2;
}
.stat-label {
  font-size: 12px;
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
.stat-cyan .stat-icon-wrap { background: #e6fffb; color: #13c2c2; }
.stat-cyan .stat-value { color: #13c2c2; }
.stat-pink .stat-icon-wrap { background: #fff0f6; color: #eb2f96; }
.stat-pink .stat-value { color: #eb2f96; }

/* 卡片头 */
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

/* 指标网格 */
.metric-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 12px;
}
.metric-item {
  padding: 12px;
  background: #f8fafc;
  border-radius: 8px;
  text-align: center;
}
.metric-value {
  font-size: 20px;
  font-weight: 700;
  color: #303133;
}
.metric-value.promo-code {
  font-size: 18px;
  letter-spacing: 2px;
  color: var(--el-color-primary);
  font-family: 'Menlo', 'Consolas', monospace;
}
.metric-unit {
  font-size: 12px;
  font-weight: 400;
  color: #909399;
}
.metric-label {
  margin-top: 6px;
  font-size: 12px;
  color: #909399;
}

/* 趋势图 */
.trend-chart {
  height: 280px;
}

/* 最近微站 */
.recent-card {
  height: 100%;
}
.recent-list {
  max-height: 280px;
  overflow-y: auto;
}
.recent-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 10px 4px;
  cursor: pointer;
  border-bottom: 1px solid #f0f2f5;
  transition: background var(--transition-time-02);
}
.recent-item:last-child {
  border-bottom: none;
}
.recent-item:hover {
  background: #f8fafc;
}
.recent-name {
  font-size: 14px;
  font-weight: 500;
  color: #303133;
  max-width: 160px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.recent-meta {
  margin-top: 4px;
  font-size: 12px;
  color: #909399;
}

/* 快捷操作 */
.quick-actions {
  display: flex;
  gap: 20px;
  flex-wrap: wrap;
}
.action-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
  cursor: pointer;
  padding: 8px 4px;
  transition: all var(--transition-time-02);
}
.action-item:hover {
  transform: translateY(-2px);
}
.action-icon {
  width: 52px;
  height: 52px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
  transition: all var(--transition-time-02);
}
.action-icon-blue { background: linear-gradient(135deg, #409eff, #36a3f7); }
.action-icon-cyan { background: linear-gradient(135deg, #36cfc9, #13c2c2); }
.action-icon-orange { background: linear-gradient(135deg, #ffa940, #fa8c16); }
.action-icon-purple { background: linear-gradient(135deg, #9254de, #722ed1); }
.action-icon-green { background: linear-gradient(135deg, #73d13d, #52c41a); }
.action-icon-pink { background: linear-gradient(135deg, #ff85c0, #eb2f96); }
.action-item:hover .action-icon {
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
}
.action-text {
  font-size: 13px;
  color: #606266;
}

/* 个人信息 */
.welcome-card {
  height: 100%;
}
.welcome-body {
  display: flex;
  align-items: center;
  gap: 16px;
}
.welcome-avatar {
  background: var(--el-color-primary);
  color: #fff;
  font-size: 24px;
  font-weight: 600;
  flex-shrink: 0;
}
.welcome-info {
  display: flex;
  flex-direction: column;
  gap: 8px;
}
.welcome-name {
  font-size: 18px;
  font-weight: 600;
  color: #303133;
}
.welcome-meta {
  font-size: 12px;
  color: #909399;
}

/* 行间距 */
.second-row,
.third-row,
.fourth-row {
  margin-top: 0;
}
</style>
