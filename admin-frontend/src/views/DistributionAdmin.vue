<template>
  <div class="distribution-admin">
    <el-tabs v-model="activeTab">
      <!-- 分销设置 -->
      <el-tab-pane label="分销设置" name="config">
        <el-card shadow="never">
          <el-form label-width="110px" class="config-form">
            <el-form-item label="启用分销">
              <el-switch v-model="config.enabled" @change="saveConfig" />
              <span class="form-tip">关闭后不再产生新的返佣，已有返佣记录不受影响</span>
            </el-form-item>
            <el-form-item label="返佣比例">
              <div class="rate-row">
                <el-input-number v-model="config.rebate_rate" :min="0" :max="20" :disabled="!config.enabled" />
                <span class="form-tip">%　（0%–20%，默认 10%；按被推荐客户实付金额计算）</span>
                <el-button class="rate-save" :disabled="!config.enabled" @click="saveConfig">保存比例</el-button>
              </div>
            </el-form-item>
            <el-alert type="info" :closable="false" show-icon title="规则说明">
              <template #default>
                <ul class="rule-list">
                  <li>一级返佣：仅返直接推荐人，不设团队计酬、不设晋级奖励，规避多级分销 / 拉人头合规风险。</li>
                  <li>返佣对象：被推荐客户<b>首次</b>购买会员或上线额度（有历史消费的账号不返佣）。</li>
                  <li>结算方式：支付成功后自动入账推荐人钱包余额（流水类型 rebate_in）；推荐人为超管时不返佣。</li>
                  <li>退款处理：订单退款自动扣回返佣（rebate_refund）；推荐人余额不足则挂起，入账后优先补扣。</li>
                  <li>绑定方式：新建账号时填写「推荐人推广码」建立绑定；超管可在账号管理中手动调整推荐人。</li>
                </ul>
              </template>
            </el-alert>
          </el-form>
        </el-card>
      </el-tab-pane>

      <!-- 返佣记录 -->
      <el-tab-pane label="返佣记录" name="rebates">
        <el-card shadow="never">
          <div class="filter-row">
            <el-input v-model="filters.keyword" placeholder="搜索分销商 / 客户用户名或昵称" clearable style="width: 260px" @change="loadRebates(1)" />
            <el-select v-model="filters.status" placeholder="状态" clearable style="width: 140px" @change="loadRebates(1)">
              <el-option label="已入账" value="settled" />
              <el-option label="已随退款扣回" value="refunded" />
              <el-option label="已撤销" value="revoked" />
              <el-option label="待扣回" value="pending_clawback" />
            </el-select>
          </div>
          <el-table :data="rebates" v-loading="rebatesLoading" stripe>
            <el-table-column label="时间" width="150">
              <template #default="{ row }">{{ formatTime(row.created_at) }}</template>
            </el-table-column>
            <el-table-column prop="distributor_name" label="分销商" min-width="100" />
            <el-table-column prop="customer_name" label="客户" min-width="100" />
            <el-table-column label="订单类型" width="120">
              <template #default="{ row }">{{ orderTypeText(row.order_type) }}</template>
            </el-table-column>
            <el-table-column label="订单金额" width="100" align="right">
              <template #default="{ row }">¥{{ yuan(row.order_amount) }}</template>
            </el-table-column>
            <el-table-column label="比例" width="70" align="center">
              <template #default="{ row }">{{ row.rebate_rate }}%</template>
            </el-table-column>
            <el-table-column label="返佣金额" width="100" align="right">
              <template #default="{ row }">¥{{ yuan(row.rebate_amount) }}</template>
            </el-table-column>
            <el-table-column label="状态" width="120" align="center">
              <template #default="{ row }">
                <el-tag :type="statusTagType(row.status)" size="small">{{ statusText(row.status) }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column label="操作" width="90" fixed="right" align="center">
              <template #default="{ row }">
                <el-button v-if="row.status !== 'revoked'" link type="danger" size="small" @click="revoke(row)">撤销</el-button>
              </template>
            </el-table-column>
          </el-table>
          <div class="pagination-wrap" v-if="rebatesTotal > pageSize">
            <el-pagination
              layout="prev, pager, next"
              :total="rebatesTotal"
              :page-size="pageSize"
              :current-page="rebatesPage"
              @current-change="loadRebates"
            />
          </div>
        </el-card>
      </el-tab-pane>

      <!-- 分销商排行 -->
      <el-tab-pane label="分销商排行" name="ranking">
        <el-card shadow="never">
          <el-table :data="ranking" v-loading="rankingLoading" stripe>
            <el-table-column type="index" label="排名" width="80" align="center" />
            <el-table-column prop="distributor_name" label="分销商" min-width="140" />
            <el-table-column prop="referral_count" label="拉新账号数" width="120" align="center" />
            <el-table-column label="成交金额" width="130" align="right">
              <template #default="{ row }">¥{{ yuan(row.total_order_amount) }}</template>
            </el-table-column>
            <el-table-column label="累计返佣" width="130" align="right">
              <template #default="{ row }"><span class="rebate-in">¥{{ yuan(row.total_rebate) }}</span></template>
            </el-table-column>
          </el-table>
        </el-card>
      </el-tab-pane>
    </el-tabs>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import api from '@/api'
import dayjs from 'dayjs'

const activeTab = ref('config')

// ---- 配置 ----
const config = reactive({ enabled: false, rebate_rate: 10 })

async function loadConfig() {
  const res: any = await api.get('/distribution/config')
  config.enabled = !!res?.enabled
  config.rebate_rate = res?.rebate_rate ?? 10
}

async function saveConfig() {
  try {
    await api.put('/distribution/config', { enabled: config.enabled, rebate_rate: config.rebate_rate })
    ElMessage.success('已保存')
  } catch {
    // 拦截器已提示
  }
}

// ---- 返佣记录 ----
const filters = reactive({ keyword: '', status: '' })
const rebates = ref<any[]>([])
const rebatesLoading = ref(false)
const rebatesPage = ref(1)
const pageSize = 20
const rebatesTotal = ref(0)

async function loadRebates(p = 1) {
  rebatesLoading.value = true
  try {
    const res: any = await api.get('/distribution/admin/rebates', {
      params: { page: p, page_size: pageSize, keyword: filters.keyword || undefined, status: filters.status || undefined },
    })
    rebates.value = res?.items || []
    rebatesTotal.value = res?.total || 0
    rebatesPage.value = p
  } finally {
    rebatesLoading.value = false
  }
}

async function revoke(row: any) {
  await ElMessageBox.confirm(
    `确认撤销该笔返佣？将从分销商「${row.distributor_name || row.distributor_id}」钱包扣回 ¥${yuan(row.rebate_amount)}。`,
    '撤销返佣',
    { type: 'warning', confirmButtonText: '确认撤销', cancelButtonText: '取消' },
  )
  await api.post(`/distribution/admin/rebates/${row.id}/revoke`)
  ElMessage.success('已撤销')
  loadRebates(rebatesPage.value)
}

// ---- 排行 ----
const ranking = ref<any[]>([])
const rankingLoading = ref(false)

async function loadRanking() {
  rankingLoading.value = true
  try {
    ranking.value = (await api.get('/distribution/admin/ranking')) || []
  } finally {
    rankingLoading.value = false
  }
}

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

onMounted(() => {
  loadConfig()
  loadRebates(1)
  loadRanking()
})
</script>

<style scoped>
.config-form {
  max-width: 760px;
}
.form-tip {
  margin-left: 10px;
  font-size: 12px;
  color: #909399;
}
.rate-row {
  display: flex;
  align-items: center;
}
.rate-save {
  margin-left: 12px;
}
.rule-list {
  margin: 0;
  padding-left: 18px;
  line-height: 1.9;
}
.filter-row {
  display: flex;
  gap: 12px;
  margin-bottom: 14px;
}
.pagination-wrap {
  margin-top: 12px;
  display: flex;
  justify-content: flex-end;
}
.rebate-in {
  color: #67c23a;
  font-weight: 600;
}
</style>
