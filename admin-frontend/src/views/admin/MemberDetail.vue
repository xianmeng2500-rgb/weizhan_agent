<template>
  <div class="member-detail-page" v-if="user">
    <el-card shadow="never">
      <template #header>
        <div class="page-header">
          <div class="header-left">
            <el-button link @click="router.back()">
              <el-icon><ArrowLeft /></el-icon>返回
            </el-button>
            <span>用户详情 - {{ user.username }}</span>
          </div>
          <el-button type="primary" @click="openRecharge">充值</el-button>
        </div>
      </template>

      <el-descriptions :column="3" border>
        <el-descriptions-item label="用户名">{{ user.username }}</el-descriptions-item>
        <el-descriptions-item label="昵称">{{ user.nickname || '-' }}</el-descriptions-item>
        <el-descriptions-item label="角色">{{ roleText }}</el-descriptions-item>
        <el-descriptions-item label="钱包余额">
          <span class="balance">{{ fmtYuan(user.wallet_balance) }}</span>
        </el-descriptions-item>
        <el-descriptions-item label="会员状态">
          <el-tag v-if="user.membership_status === 'active'" type="success" size="small">有效</el-tag>
          <el-tag v-else-if="user.membership_status === 'expired'" type="danger" size="small">已过期</el-tag>
          <el-tag v-else type="info" size="small">未开通</el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="会员到期">{{ fmtDate(user.membership_end_at) }}</el-descriptions-item>
        <el-descriptions-item label="上线额度">{{ user.session_credit_balance }} 次</el-descriptions-item>
      </el-descriptions>
    </el-card>

    <el-card shadow="never" class="mt16">
      <template #header><span>交易流水</span></template>
      <el-table :data="transactions" stripe v-loading="loading">
        <el-table-column label="时间" width="170">
          <template #default="{ row }">{{ fmtDateTime(row.created_at) }}</template>
        </el-table-column>
        <el-table-column label="类型" width="110">
          <template #default="{ row }">{{ txTypeText(row.tx_type) }}</template>
        </el-table-column>
        <el-table-column label="金额" width="110">
          <template #default="{ row }">
            <span :class="row.amount > 0 ? 'amount-in' : 'amount-out'">
              {{ row.amount > 0 ? '+' : '' }}{{ (row.amount / 100).toFixed(2) }}
            </span>
          </template>
        </el-table-column>
        <el-table-column label="交易后余额" width="110">
          <template #default="{ row }">{{ (row.balance_after / 100).toFixed(2) }}</template>
        </el-table-column>
        <el-table-column prop="remark" label="备注" show-overflow-tooltip />
        <el-table-column label="操作" width="90" fixed="right">
          <template #default="{ row }">
            <el-button
              v-if="row.tx_type.startsWith('purchase')"
              type="danger"
              link
              size="small"
              @click="openRefund(row)"
            >退款</el-button>
          </template>
        </el-table-column>
      </el-table>
      <div class="pager">
        <el-pagination
          v-model:current-page="page"
          :page-size="pageSize"
          :total="total"
          layout="total, prev, pager, next"
          @current-change="load"
        />
      </div>
    </el-card>

    <!-- 充值弹窗 -->
    <el-dialog v-model="rechargeDialog" title="钱包充值" width="420px">
      <el-form label-width="90px">
        <el-form-item label="用户">{{ user.username }}</el-form-item>
        <el-form-item label="当前余额">{{ fmtYuan(user.wallet_balance) }}</el-form-item>
        <el-form-item label="充值金额">
          <el-input-number v-model="rechargeAmount" :min="0.01" :step="100" :precision="2" />
          <span class="unit">元</span>
        </el-form-item>
        <el-form-item label="备注">
          <el-input v-model="rechargeRemark" type="textarea" :rows="2" />
        </el-form-item>
      </el-form>
      <el-alert type="warning" :closable="false" title="请确认已收到客户转账后再充值" />
      <template #footer>
        <el-button @click="rechargeDialog = false">取消</el-button>
        <el-button type="primary" :loading="submitting" @click="confirmRecharge">确认充值</el-button>
      </template>
    </el-dialog>

    <!-- 退款弹窗 -->
    <el-dialog v-model="refundDialog" title="退款" width="420px">
      <el-alert type="warning" :closable="false" title="退款将退回钱包余额并撤销对应权益，已使用的上线额度不退" />
      <el-form label-width="90px" class="mt16">
        <el-form-item label="原交易">{{ refundTarget ? txTypeText(refundTarget.tx_type) + ' ' + fmtYuan(-refundTarget.amount) : '' }}</el-form-item>
        <el-form-item label="退款原因">
          <el-input v-model="refundRemark" type="textarea" :rows="2" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="refundDialog = false">取消</el-button>
        <el-button type="danger" :loading="submitting" @click="confirmRefund">确认退款</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { ArrowLeft } from '@element-plus/icons-vue'
import {
  getMemberDetail, recharge, refundTransaction,
  fmtYuan, TX_TYPE_TEXT, type AdminMember, type Transaction,
} from '@/api/billing'

const route = useRoute()
const router = useRouter()
const userId = Number(route.params.id)

const user = ref<AdminMember | null>(null)
const transactions = ref<Transaction[]>([])
const page = ref(1)
const pageSize = 20
const total = ref(0)
const loading = ref(false)

const rechargeDialog = ref(false)
const rechargeAmount = ref(100)
const rechargeRemark = ref('')
const refundDialog = ref(false)
const refundTarget = ref<Transaction | null>(null)
const refundRemark = ref('')
const submitting = ref(false)

const roleText = computed(() => {
  const map: Record<string, string> = { admin: '管理员', sub_admin: '子账号', super_admin: '超级管理员' }
  return map[user.value?.role || ''] || user.value?.role || '-'
})

const txTypeText = (t: string) => TX_TYPE_TEXT[t] || t
const fmtDate = (d?: string | null) => (d ? new Date(d).toLocaleDateString() : '-')
const fmtDateTime = (d: string) => new Date(d).toLocaleString('zh-CN', { hour12: false })

async function load() {
  loading.value = true
  try {
    const res = await getMemberDetail(userId, { page: page.value, page_size: pageSize })
    user.value = res.user
    transactions.value = res.transactions.items || []
    total.value = res.transactions.total || 0
  } finally {
    loading.value = false
  }
}

function openRecharge() {
  rechargeAmount.value = 100
  rechargeRemark.value = ''
  rechargeDialog.value = true
}

async function confirmRecharge() {
  if (!user.value) return
  const cents = Math.round(rechargeAmount.value * 100)
  if (!cents || cents <= 0) {
    ElMessage.warning('请输入正确的充值金额')
    return
  }
  submitting.value = true
  try {
    await recharge({ user_id: user.value.id, amount: cents, remark: rechargeRemark.value || undefined })
    ElMessage.success('充值成功')
    rechargeDialog.value = false
    await load()
  } finally {
    submitting.value = false
  }
}

function openRefund(row: Transaction) {
  refundTarget.value = row
  refundRemark.value = ''
  refundDialog.value = true
}

async function confirmRefund() {
  if (!refundTarget.value) return
  try {
    await ElMessageBox.confirm('确认对该笔交易执行退款？', '退款确认', { type: 'warning' })
  } catch {
    return
  }
  submitting.value = true
  try {
    await refundTransaction({ transaction_id: refundTarget.value.id, remark: refundRemark.value || undefined })
    ElMessage.success('退款成功')
    refundDialog.value = false
    await load()
  } finally {
    submitting.value = false
  }
}

onMounted(() => {
  load()
})
</script>

<style scoped>
.mt16 { margin-top: 16px; }
.page-header { display: flex; align-items: center; justify-content: space-between; }
.header-left { display: flex; align-items: center; gap: 12px; }
.balance { font-weight: 600; color: #409eff; }
.amount-in { color: #67c23a; font-weight: 600; }
.amount-out { color: #f56c6c; font-weight: 600; }
.pager { display: flex; justify-content: flex-end; margin-top: 12px; }
.unit { margin-left: 6px; }
</style>
