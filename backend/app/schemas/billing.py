"""计费相关Schema（钱包/会员/场次额度）"""
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field


# ---------- 钱包 ----------

class RechargeRequest(BaseModel):
    """超管充值"""
    user_id: int = Field(..., description="用户ID")
    amount: int = Field(..., gt=0, description="充值金额(分)")
    remark: Optional[str] = Field(None, max_length=500, description="备注")


class RefundRequest(BaseModel):
    """超管退款（针对某笔购买流水）"""
    transaction_id: int = Field(..., description="原购买流水ID")
    remark: Optional[str] = Field(None, max_length=500, description="退款原因")


class WalletTransactionOut(BaseModel):
    """流水记录"""
    id: int
    user_id: int
    username: Optional[str] = None
    tx_type: str
    amount: int
    balance_after: int
    plan_id: Optional[int] = None
    plan_name: Optional[str] = None
    remark: Optional[str] = None
    operator_id: Optional[int] = None
    operator_name: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class PaginatedTransactions(BaseModel):
    total: int
    page: int
    page_size: int
    items: List[WalletTransactionOut]


class WalletMeOut(BaseModel):
    """我的钱包+会员+额度汇总"""
    balance: int = Field(..., description="钱包余额(分)")
    balance_yuan: str = Field(..., description="钱包余额(元)")
    membership: Optional[dict] = None
    session_credits: int = 0
    session_credits_expiring: List[dict] = Field(default_factory=list, description="即将过期的额度")


# ---------- 会员 ----------

class PlanOut(BaseModel):
    """套餐"""
    id: int
    name: str
    plan_type: str
    price: int
    duration_days: Optional[int] = None
    credit_quantity: Optional[int] = None
    description: Optional[str] = None
    is_active: bool

    class Config:
        from_attributes = True


class PlanCreate(BaseModel):
    """新增套餐（仅超管）"""
    name: str = Field(..., max_length=50)
    plan_type: str = Field(..., pattern="^(membership|session_credit)$")
    price: int = Field(..., ge=0)
    duration_days: Optional[int] = Field(None, ge=1)
    credit_quantity: Optional[int] = Field(None, ge=1)
    description: Optional[str] = Field(None, max_length=500)
    is_active: bool = True


class PlanUpdate(BaseModel):
    """编辑套餐（仅超管）"""
    name: Optional[str] = Field(None, max_length=50)
    price: Optional[int] = Field(None, ge=0)
    duration_days: Optional[int] = Field(None, ge=1)
    credit_quantity: Optional[int] = Field(None, ge=1)
    description: Optional[str] = Field(None, max_length=500)
    is_active: Optional[bool] = None


class MembershipPurchaseRequest(BaseModel):
    """用户自助购买会员"""
    plan_id: int


# ---------- 场次额度 ----------

class CreditPurchaseRequest(BaseModel):
    """用户自助购买场次额度"""
    plan_id: int
    quantity: int = Field(1, ge=1, le=50)


# ---------- 超管会员管理 ----------

class AdminMemberOut(BaseModel):
    """超管会员管理列表项"""
    id: int
    username: str
    nickname: Optional[str] = None
    role: str
    wallet_balance: int
    membership_status: str
    membership_end_at: Optional[datetime] = None
    session_credit_balance: int

    class Config:
        from_attributes = True


class PaginatedMembers(BaseModel):
    total: int
    page: int
    page_size: int
    items: List[AdminMemberOut]


class RevenueStatsOut(BaseModel):
    """收入统计"""
    total_recharge: int = Field(0, description="累计充值(分)")
    total_consume: int = Field(0, description="累计消费(分)")
    total_refund: int = Field(0, description="累计退款(分)")
    month_recharge: int = Field(0, description="本月充值(分)")
    month_consume: int = Field(0, description="本月消费(分)")
    active_members: int = Field(0, description="有效会员数")
    active_credits: int = Field(0, description="未使用场次数")
