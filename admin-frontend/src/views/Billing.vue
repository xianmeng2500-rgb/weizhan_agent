<template>
  <div class="billing-page">
    <!-- 钱包卡片 -->
    <el-row :gutter="16">
      <el-col :span="24">
        <el-card shadow="never" class="wallet-card">
          <div class="wallet-inner">
            <div class="wallet-left">
              <div class="wallet-label">钱包余额</div>
              <div class="wallet-amount">{{ wallet?.balance_yuan || '0.00' }}</div>
              <div class="wallet-tip">余额不足时，请联系管理员充值</div>
            </div>
            <div class="wallet-right">
              <el-tag v-if="auth.isSuperAdmin" type="danger" effect="plain">超级管理员无需购买</el-tag>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 会员 + 场次额度 -->
    <el-row :gutter="16" class="mt16">
      <el-col :xs="24" :md="12">
        <el-card shadow="never">
          <template #header>
            <div class="card-header">
              <span>会员状态</span>
              <el-tag v-if="membershipTag" :type="membershipTag.type" effect="light">{{ membershipTag.text }}</el-tag>
            </div>
          </template>
          <div v-if="wallet?.membership?.status === 'active'">
            <div class="info-row"><span class="label">套餐</span><span>{{ wallet.membership.plan_name }}</span></div>
            <div class="info-row"><span class="label">到期时间</span><span>{{ fmtDate(wallet.membership.end_at) }}</span></div>
            <div class="info-row"><span class="label">剩余天数</span><span>{{ wallet.membership.days_remaining }} 天</span></div>
          </div>
          <el-empty v-else-if="wallet?.membership?.status === 'expired'" description="会员已过期，微站已变为只读" :image-size="60" />
          <el-empty v-else description="尚未开通会员" :image-size="60" />
          <div class="action-bar">
            <el-button type="primary" :disabled="!canBuy" @click="openMembershipDialog">
              {{ wallet?.membership?.status === 'active' ? '续费' : '购买' }}
            </el-button>
          </div>
        </el-card>
      </el-col>

      <el-col :xs="24" :md="12">
        <el-card shadow="never">
          <template #header>
            <div class="card-header">
              <span>上线场次额度</span>
              <el-tag type="info" effect="plain">有效期1年</el-tag>
            </div>
          </template>
          <div class="credit-num">{{ wallet?.session_credits ?? 0 }} <span class="unit">次</span></div>
          <div class="form-tip" style="margin-top: 4px">微站每上线一次消耗 1 个额度，下线不退、再次上线重新消耗</div>
          <div v-if="wallet?.session_credits_expiring?.length" class="credit-warning">
            <el-icon color="#e6a23c"><Warning /></el-icon>
            有 {{ wallet.session_credits_expiring.length }} 个额度将于30天内过期（最近 {{ fmtDate(wallet.session_credits_expiring[0].expire_at) }}）
          </div>
          <div class="action-bar">
            <el-button type="primary" plain :disabled="!canBuy" @click="openCreditDialog">购买上线额度</el-button>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 交易流水 -->
    <el-card shadow="never" class="mt16">
      <template #header><span>交易流水</span></template>
      <el-table :data="transactions" stripe>
        <el-table-column label="时间" width="170">
          <template #default="{ row }">{{ fmtDateTime(row.created_at) }}</template>
        </el-table-column>
        <el-table-column label="类型" width="120">
          <template #default="{ row }">{{ txTypeText(row.tx_type) }}</template>
        </el-table-column>
        <el-table-column label="金额" width="120">
          <template #default="{ row }">
            <span :class="row.amount > 0 ? 'amount-in' : 'amount-out'">
              {{ row.amount > 0 ? '+' : '' }}{{ (row.amount / 100).toFixed(2) }}
            </span>
          </template>
        </el-table-column>
        <el-table-column label="交易后余额" width="120">
          <template #default="{ row }">{{ (row.balance_after / 100).toFixed(2) }}</template>
        </el-table-column>
        <el-table-column prop="remark" label="备注" show-overflow-tooltip />
      </el-table>
      <div class="pager">
        <el-pagination
          v-model:current-page="txPage"
          :page-size="20"
          :total="txTotal"
          layout="total, prev, pager, next"
          @current-change="loadTransactions"
        />
      </div>
    </el-card>

    <!-- 购买会员弹窗 -->
    <el-dialog v-model="membershipDialog" title="购买会员" width="420px">
      <el-form label-width="90px">
        <el-form-item label="套餐">
          <el-select v-model="selectedMembershipPlan" placeholder="选择套餐" style="width: 100%">
            <el-option
              v-for="p in membershipPlans"
              :key="p.id"
              :label="`${p.name}（${fmtYuan(p.price)} / ${p.duration_days}天）`"
              :value="p.id"
            />
          </el-select>
        </el-form-item>
      </el-form>
      <div v-if="selectedMembershipPlanObj" class="purchase-summary">
        <div>价格：{{ fmtYuan(selectedMembershipPlanObj.price) }}</div>
        <div>当前余额：{{ wallet?.balance_yuan }}</div>
        <div>支付后余额：{{ fmtYuan((wallet?.balance ?? 0) - selectedMembershipPlanObj.price) }}</div>
      </div>
      <template #footer>
        <el-button @click="membershipDialog = false">取消</el-button>
        <el-button type="primary" :loading="purchasing" @click="confirmPurchaseMembership">确认购买</el-button>
      </template>
    </el-dialog>

    <!-- 购买上线额度弹窗 -->
    <el-dialog v-model="creditDialog" title="购买上线额度" width="420px">
      <el-form label-width="90px">
        <el-form-item label="单价">
          <span>{{ creditPlan ? fmtYuan(creditPlan.price) + ' / 次' : '-' }}</span>
        </el-form-item>
        <el-form-item label="数量">
          <el-input-number v-model="creditQuantity" :min="1" :max="50" />
        </el-form-item>
      </el-form>
      <div v-if="creditPlan" class="purchase-summary">
        <div>合计：{{ fmtYuan(creditPlan.price * creditQuantity) }}</div>
        <div>当前余额：{{ wallet?.balance_yuan }}</div>
        <div>支付后余额：{{ fmtYuan((wallet?.balance ?? 0) - creditPlan.price * creditQuantity) }}</div>
        <div class="summary-tip">购买后1年内有效，过期作废；微站每上线一次消耗 1 个</div>
      </div>
      <template #footer>
        <el-button @click="creditDialog = false">取消</el-button>
        <el-button type="primary" :loading="purchasing" @click="confirmPurchaseCredits">确认购买</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Warning } from '@element-plus/icons-vue'
import { useAuthStore } from '@/store/auth'
import {
  getWalletMe, getMyTransactions, getPlans,
  purchaseMembership, purchaseCredits,
  fmtYuan, TX_TYPE_TEXT,
  type WalletMe, type Transaction, type Plan,
} from '@/api/billing'

const auth = useAuthStore()
const wallet = ref<WalletMe | null>(null)
const transactions = ref<Transaction[]>([])
const txPage = ref(1)
const txTotal = ref(0)
const plans = ref<Plan[]>([])

const membershipDialog = ref(false)
const creditDialog = ref(false)
const selectedMembershipPlan = ref<number | null>(null)
const creditQuantity = ref(1)
const purchasing = ref(false)

const canBuy = computed(() => !auth.isSuperAdmin)

const membershipPlans = computed(() => plans.value.filter((p) => p.plan_type === 'membership'))
const creditPlan = computed(() => plans.value.find((p) => p.plan_type === 'session_credit'))

const selectedMembershipPlanObj = computed(() =>
  membershipPlans.value.find((p) => p.id === selectedMembershipPlan.value)
)

const membershipTag = computed(() => {
  const s = wallet.value?.membership?.status
  if (s === 'active') return { type: 'success', text: '有效' }
  if (s === 'expired') return { type: 'danger', text: '已过期' }
  return null
})

const txTypeText = (t: string) => TX_TYPE_TEXT[t] || t
const fmtDate = (d?: string) => (d ? new Date(d).toLocaleDateString() : '-')
const fmtDateTime = (d: string) => new Date(d).toLocaleString('zh-CN', { hour12: false })

async function loadWallet() {
  try {
    wallet.value = await getWalletMe()
  } catch {
    // ignore
  }
}

async function loadTransactions() {
  try {
    const res = await getMyTransactions({ page: txPage.value, page_size: 20 })
    transactions.value = res.items || []
    txTotal.value = res.total || 0
  } catch {
    // ignore
  }
}

async function loadPlans() {
  try {
    plans.value = await getPlans()
  } catch {
    // ignore
  }
}

function openMembershipDialog() {
  selectedMembershipPlan.value = membershipPlans.value[0]?.id ?? null
  membershipDialog.value = true
}

function openCreditDialog() {
  creditQuantity.value = 1
  creditDialog.value = true
}

async function confirmPurchaseMembership() {
  if (!selectedMembershipPlan.value) {
    ElMessage.warning('请选择套餐')
    return
  }
  purchasing.value = true
  try {
    await purchaseMembership(selectedMembershipPlan.value)
    ElMessage.success('购买成功')
    membershipDialog.value = false
    await loadWallet()
    await loadTransactions()
  } catch (e: any) {
    const detail = e?.response?.data?.detail || ''
    if (String(detail).startsWith('INSUFFICIENT_BALANCE')) {
      ElMessage.error(detail.split(':')[1] || '余额不足，请联系管理员充值')
    }
  } finally {
    purchasing.value = false
  }
}

async function confirmPurchaseCredits() {
  if (!creditPlan.value) {
    ElMessage.warning('暂无可购买的额度套餐')
    return
  }
  purchasing.value = true
  try {
    await purchaseCredits(creditPlan.value.id, creditQuantity.value)
    ElMessage.success('购买成功')
    creditDialog.value = false
    await loadWallet()
    await loadTransactions()
  } catch (e: any) {
    const detail = e?.response?.data?.detail || ''
    if (String(detail).startsWith('INSUFFICIENT_BALANCE')) {
      ElMessage.error(detail.split(':')[1] || '余额不足，请联系管理员充值')
    }
  } finally {
    purchasing.value = false
  }
}

onMounted(() => {
  loadWallet()
  loadTransactions()
  loadPlans()
})
</script>

<style scoped>
.mt16 { margin-top: 16px; }
.wallet-card { background: linear-gradient(135deg, #409eff 0%, #6f42c1 100%); border: none; }
.wallet-card :deep(.el-card__body) { padding: 20px 24px; }
.wallet-inner { display: flex; align-items: center; justify-content: space-between; }
.wallet-label { color: rgba(255, 255, 255, 0.8); font-size: 14px; }
.wallet-amount { color: #fff; font-size: 32px; font-weight: 700; margin-top: 4px; }
.wallet-tip { color: rgba(255, 255, 255, 0.6); font-size: 12px; margin-top: 6px; }
.card-header { display: flex; align-items: center; justify-content: space-between; }
.info-row { display: flex; gap: 16px; padding: 6px 0; font-size: 14px; }
.info-row .label { color: #909399; width: 70px; }
.credit-num { font-size: 32px; font-weight: 700; color: #303133; }
.credit-num .unit { font-size: 14px; color: #909399; font-weight: 400; margin-left: 4px; }
.credit-warning { display: flex; align-items: center; gap: 4px; color: #e6a23c; font-size: 13px; margin-top: 8px; }
.action-bar { margin-top: 16px; }
.amount-in { color: #67c23a; font-weight: 600; }
.amount-out { color: #f56c6c; font-weight: 600; }
.pager { display: flex; justify-content: flex-end; margin-top: 12px; }
.purchase-summary { background: #f5f7fa; border-radius: 6px; padding: 12px 16px; font-size: 13px; display: grid; gap: 6px; }
.summary-tip { color: #e6a23c; }
</style>
