<template>
  <div class="member-list-page">
    <el-card shadow="never">
      <template #header>
        <div class="page-header">
          <span>会员管理</span>
          <div class="header-actions">
            <el-input v-model="keyword" placeholder="搜索用户名" clearable style="width: 200px" @keyup.enter="search">
              <template #prefix><el-icon><Search /></el-icon></template>
            </el-input>
            <el-select v-model="statusFilter" placeholder="会员状态" clearable style="width: 130px" @change="search">
              <el-option label="有效" value="active" />
              <el-option label="已过期" value="expired" />
              <el-option label="未开通" value="none" />
            </el-select>
            <el-button @click="showPlansDialog = true">套餐管理</el-button>
          </div>
        </div>
      </template>

      <el-table :data="members" stripe v-loading="loading">
        <el-table-column prop="username" label="用户名" min-width="120" />
        <el-table-column prop="nickname" label="昵称" min-width="100" />
        <el-table-column label="角色" width="100">
          <template #default="{ row }">
            <el-tag size="small" :type="row.role === 'admin' ? 'warning' : 'info'" effect="plain">
              {{ row.role === 'admin' ? '管理员' : '子账号' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="会员状态" width="100">
          <template #default="{ row }">
            <el-tag v-if="row.membership_status === 'active'" type="success" size="small">有效</el-tag>
            <el-tag v-else-if="row.membership_status === 'expired'" type="danger" size="small">已过期</el-tag>
            <el-tag v-else type="info" size="small">未开通</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="到期时间" width="110">
          <template #default="{ row }">{{ fmtDate(row.membership_end_at) }}</template>
        </el-table-column>
        <el-table-column label="钱包余额" width="110">
          <template #default="{ row }">{{ fmtYuan(row.wallet_balance) }}</template>
        </el-table-column>
        <el-table-column label="上线额度" width="90">
          <template #default="{ row }">{{ row.session_credit_balance }} 场</template>
        </el-table-column>
        <el-table-column label="操作" width="150" fixed="right">
          <template #default="{ row }">
            <el-button type="primary" link size="small" @click="openRecharge(row)">充值</el-button>
            <el-button type="primary" link size="small" @click="goDetail(row)">详情</el-button>
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
        <el-form-item label="用户">{{ rechargeTarget?.username }}</el-form-item>
        <el-form-item label="当前余额">{{ fmtYuan(rechargeTarget?.wallet_balance ?? 0) }}</el-form-item>
        <el-form-item label="充值金额">
          <el-input-number v-model="rechargeAmount" :min="0.01" :step="100" :precision="2" />
          <span class="unit">元</span>
        </el-form-item>
        <el-form-item label="备注">
          <el-input v-model="rechargeRemark" type="textarea" :rows="2" placeholder="如：客户微信转账1000元" />
        </el-form-item>
      </el-form>
      <el-alert type="warning" :closable="false" title="请确认已收到客户转账后再充值" />
      <template #footer>
        <el-button @click="rechargeDialog = false">取消</el-button>
        <el-button type="primary" :loading="submitting" @click="confirmRecharge">确认充值</el-button>
      </template>
    </el-dialog>

    <!-- 套餐管理弹窗 -->
    <el-dialog v-model="showPlansDialog" title="套餐管理" width="640px">
      <el-table :data="plans" stripe>
        <el-table-column prop="name" label="名称" width="110" />
        <el-table-column label="类型" width="90">
          <template #default="{ row }">{{ row.plan_type === 'membership' ? '会员' : '场次' }}</template>
        </el-table-column>
        <el-table-column label="价格(元)" width="110">
          <template #default="{ row }">
            <el-input-number
              v-if="editingPlanId === row.id"
              v-model="editPrice"
              :min="0"
              :precision="2"
              :controls="false"
              style="width: 90px"
            />
            <span v-else>{{ (row.price / 100).toFixed(2) }}</span>
          </template>
        </el-table-column>
        <el-table-column label="时长/数量" width="100">
          <template #default="{ row }">
            {{ row.plan_type === 'membership' ? `${row.duration_days}天` : `${row.credit_quantity}场/份` }}
          </template>
        </el-table-column>
        <el-table-column label="状态" width="80">
          <template #default="{ row }">
            <el-tag :type="row.is_active ? 'success' : 'info'" size="small">{{ row.is_active ? '启用' : '停用' }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="130">
          <template #default="{ row }">
            <template v-if="editingPlanId === row.id">
              <el-button type="primary" link size="small" @click="savePlan(row)">保存</el-button>
              <el-button link size="small" @click="editingPlanId = null">取消</el-button>
            </template>
            <template v-else>
              <el-button type="primary" link size="small" @click="startEditPlan(row)">改价</el-button>
              <el-button type="primary" link size="small" @click="togglePlan(row)">
                {{ row.is_active ? '停用' : '启用' }}
              </el-button>
            </template>
          </template>
        </el-table-column>
      </el-table>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { Search } from '@element-plus/icons-vue'
import {
  getAdminMembers, recharge, getAdminPlans, updatePlan,
  fmtYuan, type AdminMember, type Plan,
} from '@/api/billing'

const router = useRouter()
const members = ref<AdminMember[]>([])
const page = ref(1)
const pageSize = 20
const total = ref(0)
const loading = ref(false)
const keyword = ref('')
const statusFilter = ref('')

const rechargeDialog = ref(false)
const rechargeTarget = ref<AdminMember | null>(null)
const rechargeAmount = ref(100)
const rechargeRemark = ref('')
const submitting = ref(false)

const showPlansDialog = ref(false)
const plans = ref<Plan[]>([])
const editingPlanId = ref<number | null>(null)
const editPrice = ref(0)

const fmtDate = (d?: string | null) => (d ? new Date(d).toLocaleDateString() : '-')

async function load() {
  loading.value = true
  try {
    const res = await getAdminMembers({
      page: page.value,
      page_size: pageSize,
      keyword: keyword.value || undefined,
      membership_status: statusFilter.value || undefined,
    })
    members.value = res.items || []
    total.value = res.total || 0
  } finally {
    loading.value = false
  }
}

function search() {
  page.value = 1
  load()
}

function openRecharge(row: AdminMember) {
  rechargeTarget.value = row
  rechargeAmount.value = 100
  rechargeRemark.value = ''
  rechargeDialog.value = true
}

async function confirmRecharge() {
  if (!rechargeTarget.value) return
  const cents = Math.round(rechargeAmount.value * 100)
  if (!cents || cents <= 0) {
    ElMessage.warning('请输入正确的充值金额')
    return
  }
  submitting.value = true
  try {
    await recharge({ user_id: rechargeTarget.value.id, amount: cents, remark: rechargeRemark.value || undefined })
    ElMessage.success('充值成功')
    rechargeDialog.value = false
    await load()
  } finally {
    submitting.value = false
  }
}

function goDetail(row: AdminMember) {
  router.push(`/admin/members/${row.id}`)
}

async function loadPlans() {
  try {
    plans.value = await getAdminPlans(true)
  } catch {
    // ignore
  }
}

function startEditPlan(row: Plan) {
  editingPlanId.value = row.id
  editPrice.value = row.price / 100
}

async function savePlan(row: Plan) {
  const cents = Math.round(editPrice.value * 100)
  if (cents < 0) {
    ElMessage.warning('价格不能为负')
    return
  }
  try {
    await updatePlan(row.id, { price: cents })
    ElMessage.success('价格已更新')
    editingPlanId.value = null
    await loadPlans()
  } catch {
    // ignore
  }
}

async function togglePlan(row: Plan) {
  try {
    await updatePlan(row.id, { is_active: !row.is_active })
    ElMessage.success(row.is_active ? '已停用' : '已启用')
    await loadPlans()
  } catch {
    // ignore
  }
}

onMounted(() => {
  load()
  loadPlans()
})
</script>

<style scoped>
.page-header { display: flex; align-items: center; justify-content: space-between; }
.header-actions { display: flex; gap: 8px; align-items: center; }
.pager { display: flex; justify-content: flex-end; margin-top: 12px; }
.unit { margin-left: 6px; }
</style>
