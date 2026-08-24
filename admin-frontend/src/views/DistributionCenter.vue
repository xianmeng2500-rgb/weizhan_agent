<template>
  <div class="distribution-center">
    <!-- 推广码卡片 -->
    <el-card shadow="never" class="code-card">
      <div class="code-row">
        <div class="code-left">
          <div class="code-label">我的推广码</div>
          <div class="code-value" v-if="info.recommend_code">{{ info.recommend_code }}</div>
          <div class="code-value" v-else>--</div>
          <div class="code-tip">
            {{ info.enabled ? `当前返佣比例 ${info.rebate_rate}%：被推荐客户首次购买会员 / 上线额度，返佣自动入账钱包余额。` : '分销功能暂未开启，开启后可获得返佣。' }}
          </div>
        </div>
        <div class="code-actions">
          <el-button type="primary" :icon="CopyDocument" :disabled="!info.recommend_code" @click="copyCode">复制推广码</el-button>
        </div>
      </div>
    </el-card>

    <!-- 统计卡 -->
    <div class="stat-grid">
      <div class="stat-card">
        <div class="stat-num">{{ info.referral_count }}</div>
        <div class="stat-label">累计拉新账号</div>
      </div>
      <div class="stat-card">
        <div class="stat-num">¥{{ yuan(info.total_order_amount) }}</div>
        <div class="stat-label">累计成交金额</div>
      </div>
      <div class="stat-card">
        <div class="stat-num">¥{{ yuan(info.total_rebate) }}</div>
        <div class="stat-label">累计返佣</div>
      </div>
      <div class="stat-card" v-if="info.pending_clawback > 0">
        <div class="stat-num warn">¥{{ yuan(info.pending_clawback) }}</div>
        <div class="stat-label">待扣回（退款）</div>
      </div>
    </div>

    <!-- 返佣流水 -->
    <el-card shadow="never">
      <template #header>
        <div class="card-header">
          <span class="card-title">返佣流水</span>
        </div>
      </template>
      <el-table :data="records" v-loading="loading" stripe>
        <el-table-column label="时间" width="160">
          <template #default="{ row }">{{ formatTime(row.created_at) }}</template>
        </el-table-column>
        <el-table-column prop="customer_name" label="客户" min-width="100" />
        <el-table-column label="订单类型" width="120">
          <template #default="{ row }">{{ orderTypeText(row.order_type) }}</template>
        </el-table-column>
        <el-table-column label="订单金额" width="110" align="right">
          <template #default="{ row }">¥{{ yuan(row.order_amount) }}</template>
        </el-table-column>
        <el-table-column label="返佣金额" width="110" align="right">
          <template #default="{ row }"><span class="rebate-in">+¥{{ yuan(row.rebate_amount) }}</span></template>
        </el-table-column>
        <el-table-column label="状态" width="110" align="center">
          <template #default="{ row }">
            <el-tag :type="statusTagType(row.status)" size="small">{{ statusText(row.status) }}</el-tag>
          </template>
        </el-table-column>
      </el-table>
      <div class="pagination-wrap" v-if="total > pageSize">
        <el-pagination
          layout="prev, pager, next"
          :total="total"
          :page-size="pageSize"
          :current-page="page"
          @current-change="loadRecords"
        />
      </div>
    </el-card>

    <!-- 分销规则说明 -->
    <el-alert type="info" :closable="false" show-icon class="rule-alert" title="分销规则">
      <template #default>
        <ul class="rule-list">
          <li>一级分销：仅返直接推荐人，不设团队计酬。</li>
          <li>返佣对象：被推荐客户<b>首次</b>购买会员或上线额度，按当前比例返佣。</li>
          <li>结算方式：返佣自动入账钱包余额，可在「会员中心」查看与使用。</li>
          <li>退款处理：客户订单退款时对应返佣自动扣回；余额不足则挂起，入账后优先补扣。</li>
        </ul>
      </template>
    </el-alert>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { CopyDocument } from '@element-plus/icons-vue'
import api from '@/api'
import dayjs from 'dayjs'

const info = reactive({
  recommend_code: '',
  enabled: false,
  rebate_rate: 0,
  referral_count: 0,
  total_order_amount: 0,
  total_rebate: 0,
  pending_clawback: 0,
})

const records = ref<any[]>([])
const loading = ref(false)
const page = ref(1)
const pageSize = 20
const total = ref(0)

function yuan(cents: number) {
  return (cents / 100).toFixed(2)
}

function formatTime(t: string) {
  return t ? dayjs(t).format('YYYY-MM-DD HH:mm') : '-'
}

function orderTypeText(t: string) {
  return t === 'membership' ? '购买会员' : t === 'session_credit' ? '购买上线额度' : t
}

function statusText(s: string) {
  const map: Record<string, string> = {
    settled: '已入账',
    refunded: '已随退款扣回',
    revoked: '已撤销',
    pending_clawback: '待扣回',
  }
  return map[s] || s
}

function statusTagType(s: string) {
  const map: Record<string, string> = { settled: 'success', refunded: 'info', revoked: 'danger', pending_clawback: 'warning' }
  return map[s] || 'info'
}

async function loadInfo() {
  const res: any = await api.get('/distribution/my-code')
  Object.assign(info, res || {})
}

async function loadRecords(p = 1) {
  loading.value = true
  try {
    const res: any = await api.get('/distribution/rebates', { params: { page: p, page_size: pageSize } })
    records.value = res?.items || []
    total.value = res?.total || 0
    page.value = p
  } finally {
    loading.value = false
  }
}

async function copyCode() {
  try {
    await navigator.clipboard.writeText(info.recommend_code)
    ElMessage.success('推广码已复制')
  } catch {
    ElMessage.warning('复制失败，请手动复制')
  }
}

onMounted(() => {
  loadInfo()
  loadRecords(1)
})
</script>

<style scoped>
.distribution-center {
  display: flex;
  flex-direction: column;
  gap: 16px;
}
.code-card {
  border: none;
}
.code-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
}
.code-left {
  display: flex;
  flex-direction: column;
  gap: 6px;
}
.code-label {
  font-size: 13px;
  color: #909399;
}
.code-value {
  font-size: 32px;
  font-weight: 700;
  letter-spacing: 4px;
  color: var(--el-color-primary);
  font-family: 'Menlo', 'Consolas', monospace;
}
.code-tip {
  font-size: 12px;
  color: #909399;
  max-width: 560px;
}
.stat-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(160px, 1fr));
  gap: 16px;
}
.stat-card {
  background: #fff;
  border-radius: 8px;
  padding: 18px 20px;
  box-shadow: 0 1px 3px rgba(0, 21, 41, 0.06);
  border: 1px solid #ebeef5;
}
.stat-num {
  font-size: 24px;
  font-weight: 700;
  color: #303133;
}
.stat-num.warn {
  color: #e6a23c;
}
.stat-label {
  margin-top: 6px;
  font-size: 13px;
  color: #909399;
}
.card-header {
  display: flex;
  align-items: center;
}
.card-title {
  font-size: 15px;
  font-weight: 600;
  color: #303133;
}
.rebate-in {
  color: #67c23a;
  font-weight: 600;
}
.pagination-wrap {
  margin-top: 12px;
  display: flex;
  justify-content: flex-end;
}
.rule-alert {
  margin-top: 4px;
}
.rule-list {
  margin: 0;
  padding-left: 18px;
  line-height: 1.9;
}</style>
