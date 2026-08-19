import request from './index'

export interface Plan {
  id: number
  name: string
  plan_type: 'membership' | 'session_credit'
  price: number
  duration_days: number | null
  credit_quantity: number | null
  description: string | null
  is_active: boolean
}

export interface WalletMe {
  balance: number
  balance_yuan: string
  membership: {
    status: string
    plan_name?: string
    start_at?: string
    end_at?: string
    days_remaining?: number
  } | null
  session_credits: number
  session_credits_expiring: { id: number; expire_at: string }[]
}

export interface Transaction {
  id: number
  user_id: number
  username: string | null
  tx_type: string
  amount: number
  balance_after: number
  plan_name: string | null
  remark: string | null
  operator_name: string | null
  created_at: string
}

export interface AdminMember {
  id: number
  username: string
  nickname: string | null
  role: string
  wallet_balance: number
  membership_status: string
  membership_end_at: string | null
  session_credit_balance: number
}

export const TX_TYPE_TEXT: Record<string, string> = {
  recharge: '充值',
  purchase_membership: '购买会员',
  purchase_credit: '购买场次',
  ai_generate: 'AI生图',
  refund: '退款',
}

export const fmtYuan = (cents: number) => `¥${(cents / 100).toFixed(2)}`

// ---- 用户侧 ----

export const getWalletMe = () => request.get<any, WalletMe>('/billing/me')

export const getMyTransactions = (params: { page: number; page_size: number }) =>
  request.get<any, { total: number; items: Transaction[] }>('/billing/transactions', { params })

export const getPlans = () => request.get<any, Plan[]>('/billing/plans')

export const purchaseMembership = (plan_id: number) =>
  request.post<any, { message: string }>('/billing/membership/purchase', { plan_id })

export const purchaseCredits = (plan_id: number, quantity: number) =>
  request.post<any, { message: string }>('/billing/credits/purchase', { plan_id, quantity })

// ---- 超管侧 ----

export const recharge = (data: { user_id: number; amount: number; remark?: string }) =>
  request.post<any, Transaction>('/admin/billing/recharge', data)

export const refundTransaction = (data: { transaction_id: number; remark?: string }) =>
  request.post<any, Transaction>('/admin/billing/refund', data)

export const getAdminMembers = (params: { page: number; page_size: number; keyword?: string; membership_status?: string }) =>
  request.get<any, { total: number; items: AdminMember[] }>('/admin/billing/members', { params })

export const getMemberDetail = (userId: number, params: { page: number; page_size: number }) =>
  request.get<any, { user: AdminMember; transactions: { total: number; items: Transaction[] } }>(
    `/admin/billing/members/${userId}`,
    { params }
  )

export const getAdminTransactions = (params: { page: number; page_size: number; user_id?: number; tx_type?: string }) =>
  request.get<any, { total: number; items: Transaction[] }>('/admin/billing/transactions', { params })

export const getAdminPlans = (include_inactive = true) =>
  request.get<any, Plan[]>('/admin/billing/plans', { params: { include_inactive } })

export const updatePlan = (id: number, data: Partial<Plan>) =>
  request.put<any, Plan>(`/admin/billing/plans/${id}`, data)

export const getRevenueStats = () => request.get<any, any>('/admin/billing/revenue/stats')
