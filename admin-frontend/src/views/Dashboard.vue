<template>
  <div class="dashboard">
    <!-- 统计卡片 -->
    <el-row :gutter="16" class="stat-row">
      <el-col :xs="12" :sm="12" :md="6" v-for="(item, index) in statCards" :key="index">
        <div class="stat-card" :class="'stat-' + item.theme">
          <div class="stat-icon-wrap">
            <el-icon :size="28"><component :is="item.icon" /></el-icon>
          </div>
          <div class="stat-body">
            <div class="stat-value">{{ item.value }}</div>
            <div class="stat-label">{{ item.label }}</div>
          </div>
        </div>
      </el-col>
    </el-row>

    <!-- 商业化: 会员信息卡片（超管不展示） -->
    <el-card v-if="!auth.isSuperAdmin && wallet" shadow="hover" class="billing-card">
      <div class="billing-body">
        <div class="billing-item">
          <div class="billing-value">{{ walletBalanceText }}</div>
          <div class="billing-label">钱包余额</div>
        </div>
        <div class="billing-divider"></div>
        <div class="billing-item">
          <div class="billing-value">
            <el-tag v-if="wallet.membership?.status === 'active'" type="success" effect="plain">会员生效中</el-tag>
            <el-tag v-else-if="wallet.membership?.status === 'expired'" type="danger" effect="plain">会员已过期</el-tag>
            <el-tag v-else type="info" effect="plain">未开通会员</el-tag>
          </div>
          <div class="billing-label">
            会员状态{{ wallet.membership?.end_at ? ` · ${fmtDate(wallet.membership.end_at)} 到期` : '' }}
          </div>
        </div>
        <div class="billing-divider"></div>
        <div class="billing-item">
          <div class="billing-value">{{ wallet.session_credits ?? 0 }}<span class="billing-unit"> 次</span></div>
          <div class="billing-label">剩余上线额度</div>
        </div>
        <el-button type="primary" plain @click="$router.push('/billing')">前往会员中心</el-button>
      </div>
    </el-card>

    <!-- 快捷操作 + 欢迎区 -->
    <el-row :gutter="16" :style="{ marginTop: '16px' }">
      <el-col :xs="24" :md="16">
        <el-card shadow="hover">
          <template #header>
            <div class="card-header">
              <span class="card-title">
                <el-icon><Promotion /></el-icon>
                快捷操作
              </span>
            </div>
          </template>
          <div class="quick-actions">
            <div class="action-item" @click="$router.push('/sites/create')">
              <div class="action-icon action-icon-blue">
                <el-icon :size="24"><Plus /></el-icon>
              </div>
              <span class="action-text">创建微站</span>
            </div>
            <div class="action-item" @click="$router.push('/sites')">
              <div class="action-icon action-icon-cyan">
                <el-icon :size="24"><Monitor /></el-icon>
              </div>
              <span class="action-text">管理微站</span>
            </div>
            <div class="action-item" @click="$router.push('/admin/accounts')" v-if="auth.canManageAccounts">
              <div class="action-icon action-icon-orange">
                <el-icon :size="24"><UserFilled /></el-icon>
              </div>
              <span class="action-text">账号管理</span>
            </div>
            <div class="action-item" @click="$router.push('/admin/system-config')" v-if="auth.isSuperAdmin">
              <div class="action-icon action-icon-purple">
                <el-icon :size="24"><Setting /></el-icon>
              </div>
              <span class="action-text">系统配置</span>
            </div>
          </div>
        </el-card>
      </el-col>
      <el-col :xs="24" :md="8">
        <el-card shadow="hover" class="welcome-card">
          <template #header>
            <div class="card-header">
              <span class="card-title">
                <el-icon><User /></el-icon>
                个人信息
              </span>
            </div>
          </template>
          <div class="welcome-body">
            <el-avatar :size="56" class="welcome-avatar">{{ (auth.nickname || 'U').charAt(0).toUpperCase() }}</el-avatar>
            <div class="welcome-info">
              <div class="welcome-name">{{ auth.nickname }}</div>
              <el-tag size="small" :type="auth.role === 'super_admin' ? 'danger' : auth.role === 'admin' ? 'warning' : 'info'" effect="plain">
                {{ roleText }}
              </el-tag>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import api from '@/api'
import { useAuthStore } from '@/store/auth'
import { Plus, Monitor, UserFilled, Setting, Promotion, User } from '@element-plus/icons-vue'
import { getWalletMe, fmtYuan } from '@/api/billing'

const auth = useAuthStore()

// 商业化: 会员信息
const wallet = ref<any>(null)
const walletBalanceText = computed(() => (wallet.value ? fmtYuan(wallet.value.balance) : '0.00'))
function fmtDate(v: string) {
  return v ? String(v).slice(0, 10) : ''
}

const stats = ref({
  total_sites: 0,
  online_sites: 0,
  total_pv: 0,
  total_uv: 0,
})

const statCards = computed(() => [
  { label: '微站总数', value: stats.value.total_sites, theme: 'blue', icon: 'Monitor' },
  { label: '在线微站', value: stats.value.online_sites, theme: 'green', icon: 'CircleCheck' },
  { label: '总访问量', value: stats.value.total_pv, theme: 'orange', icon: 'View' },
  { label: '总访客数', value: stats.value.total_uv, theme: 'purple', icon: 'User' },
])

const roleText = computed(() => {
  const map: Record<string, string> = {
    super_admin: '超级管理员',
    admin: '管理员',
    sub_admin: '子账号',
  }
  return map[auth.role] || auth.role
})

onMounted(async () => {
  try {
    const res: any = await api.get('/stats/overview')
    stats.value.total_sites = res.total_sites ?? 0
    stats.value.online_sites = res.online_sites ?? 0
    stats.value.total_pv = res.total_pv ?? 0
    stats.value.total_uv = res.total_uv ?? 0
  } catch (e) {
    console.error('加载工作台统计失败', e)
  }
  if (!auth.isSuperAdmin) {
    try {
      wallet.value = await getWalletMe()
    } catch {
      wallet.value = null
    }
  }
})
</script>

<style scoped>
/* 统计卡片 */
.stat-row {
  margin-bottom: 0;
}
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
  width: 56px;
  height: 56px;
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
  font-size: 28px;
  font-weight: 700;
  line-height: 1.2;
}
.stat-label {
  font-size: 13px;
  color: #909399;
  margin-top: 4px;
}

/* 主题色 */
.stat-blue .stat-icon-wrap { background: #e8f3ff; color: #409eff; }
.stat-blue .stat-value { color: #409eff; }
.stat-green .stat-icon-wrap { background: #e8f7e8; color: #67c23a; }
.stat-green .stat-value { color: #67c23a; }
.stat-orange .stat-icon-wrap { background: #fdf3e8; color: #e6a23c; }
.stat-orange .stat-value { color: #e6a23c; }
.stat-purple .stat-icon-wrap { background: #f3e8ff; color: #8b5cf6; }
.stat-purple .stat-value { color: #8b5cf6; }

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

/* 快捷操作 */
.quick-actions {
  display: flex;
  gap: 24px;
  flex-wrap: wrap;
}
.action-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 10px;
  cursor: pointer;
  padding: 8px 4px;
  transition: all var(--transition-time-02);
}
.action-item:hover {
  transform: translateY(-2px);
}
.action-icon {
  width: 56px;
  height: 56px;
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
.action-item:hover .action-icon {
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
}
.action-text {
  font-size: 13px;
  color: #606266;
}

/* 欢迎卡片 */
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

/* 会员信息卡片 */
.billing-card {
  margin-top: 16px;
}
.billing-body {
  display: flex;
  align-items: center;
  gap: 24px;
  flex-wrap: wrap;
}
.billing-item {
  display: flex;
  flex-direction: column;
  gap: 6px;
}
.billing-value {
  font-size: 22px;
  font-weight: 700;
  color: #303133;
  line-height: 1.2;
}
.billing-unit {
  font-size: 13px;
  font-weight: 400;
  color: #909399;
}
.billing-label {
  font-size: 13px;
  color: #909399;
}
.billing-divider {
  width: 1px;
  height: 36px;
  background: #ebeef5;
}
.billing-body .el-button {
  margin-left: auto;
}
</style>
