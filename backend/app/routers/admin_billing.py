"""计费管理路由（超管侧）：充值/退款/会员管理/套餐管理/流水/收入统计"""
import logging
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import User, WalletTransaction, MembershipPlan, Membership, SessionCredit
from app.utils.deps import get_current_admin, ROLE_SUPER_ADMIN
from app.services import billing_service
from app.schemas.billing import (
    RechargeRequest, RefundRequest,
    WalletTransactionOut, PaginatedTransactions,
    PlanOut, PlanCreate, PlanUpdate,
    AdminMemberOut, PaginatedMembers, RevenueStatsOut,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/admin/billing", tags=["计费管理"])


def _require_super_admin(current: User):
    if current.role != ROLE_SUPER_ADMIN:
        raise HTTPException(status_code=403, detail="仅超级管理员可操作")


# ---------- 充值 / 退款 ----------

@router.post("/recharge", response_model=WalletTransactionOut)
def recharge(
    req: RechargeRequest,
    db: Session = Depends(get_db),
    current: User = Depends(get_current_admin),
):
    """为用户充值"""
    _require_super_admin(current)
    try:
        tx = billing_service.recharge(db, req.user_id, req.amount, current, req.remark)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    user = db.query(User).filter(User.id == req.user_id).first()
    return WalletTransactionOut(
        id=tx.id, user_id=tx.user_id, username=user.username if user else None,
        tx_type=tx.tx_type, amount=tx.amount, balance_after=tx.balance_after,
        plan_id=tx.plan_id, remark=tx.remark, operator_id=tx.operator_id,
        operator_name=current.nickname or current.username, created_at=tx.created_at,
    )


@router.post("/refund", response_model=WalletTransactionOut)
def refund(
    req: RefundRequest,
    db: Session = Depends(get_db),
    current: User = Depends(get_current_admin),
):
    """按购买流水退款"""
    _require_super_admin(current)
    try:
        tx = billing_service.refund_transaction(db, current, req.transaction_id, req.remark)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    user = db.query(User).filter(User.id == tx.user_id).first()
    return WalletTransactionOut(
        id=tx.id, user_id=tx.user_id, username=user.username if user else None,
        tx_type=tx.tx_type, amount=tx.amount, balance_after=tx.balance_after,
        plan_id=tx.plan_id, remark=tx.remark, operator_id=tx.operator_id,
        operator_name=current.nickname or current.username, created_at=tx.created_at,
    )


# ---------- 会员管理列表 ----------

@router.get("/members", response_model=PaginatedMembers)
def list_members(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    keyword: str | None = None,
    membership_status: str | None = None,
    db: Session = Depends(get_db),
    current: User = Depends(get_current_admin),
):
    """会员管理列表（含钱包余额/额度余额）"""
    _require_super_admin(current)
    q = db.query(User).filter(User.role != ROLE_SUPER_ADMIN)
    if keyword:
        q = q.filter(User.username.like(f"%{keyword}%"))
    if membership_status:
        q = q.filter(User.membership_status == membership_status)
    total = q.count()
    users = q.order_by(User.id.desc()).offset((page - 1) * page_size).limit(page_size).all()
    return PaginatedMembers(
        total=total, page=page, page_size=page_size,
        items=[AdminMemberOut.model_validate(u) for u in users],
    )


@router.get("/members/{user_id}")
def member_detail(
    user_id: int,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current: User = Depends(get_current_admin),
):
    """用户计费详情（账号+流水）"""
    _require_super_admin(current)
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    q = db.query(WalletTransaction).filter(WalletTransaction.user_id == user_id)
    total = q.count()
    items = q.order_by(WalletTransaction.created_at.desc()).offset((page - 1) * page_size).limit(page_size).all()
    return {
        "user": AdminMemberOut.model_validate(user),
        "transactions": {
            "total": total, "page": page, "page_size": page_size,
            "items": [WalletTransactionOut(
                id=t.id, user_id=t.user_id, username=user.username, tx_type=t.tx_type,
                amount=t.amount, balance_after=t.balance_after, plan_id=t.plan_id,
                plan_name=t.plan.name if t.plan else None, remark=t.remark,
                operator_id=t.operator_id,
                operator_name=(t.operator.nickname or t.operator.username) if t.operator else None,
                created_at=t.created_at,
            ) for t in items],
        },
    }


# ---------- 流水查询 ----------

@router.get("/transactions", response_model=PaginatedTransactions)
def all_transactions(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    user_id: int | None = None,
    tx_type: str | None = None,
    db: Session = Depends(get_db),
    current: User = Depends(get_current_admin),
):
    """所有用户流水（超管）"""
    _require_super_admin(current)
    q = db.query(WalletTransaction)
    if user_id:
        q = q.filter(WalletTransaction.user_id == user_id)
    if tx_type:
        q = q.filter(WalletTransaction.tx_type == tx_type)
    total = q.count()
    items = q.order_by(WalletTransaction.created_at.desc()).offset((page - 1) * page_size).limit(page_size).all()
    out = []
    for t in items:
        u = db.query(User).filter(User.id == t.user_id).first()
        out.append(WalletTransactionOut(
            id=t.id, user_id=t.user_id, username=u.username if u else None,
            tx_type=t.tx_type, amount=t.amount, balance_after=t.balance_after,
            plan_id=t.plan_id, plan_name=t.plan.name if t.plan else None,
            remark=t.remark, operator_id=t.operator_id,
            operator_name=(t.operator.nickname or t.operator.username) if t.operator else None,
            created_at=t.created_at,
        ))
    return PaginatedTransactions(total=total, page=page, page_size=page_size, items=out)


# ---------- 套餐管理 ----------

@router.get("/plans", response_model=list[PlanOut])
def admin_list_plans(
    include_inactive: bool = False,
    db: Session = Depends(get_db),
    current: User = Depends(get_current_admin),
):
    """套餐列表（超管，含停用）"""
    _require_super_admin(current)
    q = db.query(MembershipPlan)
    if not include_inactive:
        q = q.filter(MembershipPlan.is_active == True)  # noqa: E712
    return q.all()


@router.post("/plans", response_model=PlanOut)
def create_plan(
    req: PlanCreate,
    db: Session = Depends(get_db),
    current: User = Depends(get_current_admin),
):
    """新增套餐"""
    _require_super_admin(current)
    plan = MembershipPlan(**req.model_dump())
    db.add(plan)
    db.commit()
    db.refresh(plan)
    return plan


@router.put("/plans/{plan_id}", response_model=PlanOut)
def update_plan(
    plan_id: int,
    req: PlanUpdate,
    db: Session = Depends(get_db),
    current: User = Depends(get_current_admin),
):
    """编辑套餐（含价格调整）"""
    _require_super_admin(current)
    plan = db.query(MembershipPlan).filter(MembershipPlan.id == plan_id).first()
    if not plan:
        raise HTTPException(status_code=404, detail="套餐不存在")
    for field, value in req.model_dump(exclude_unset=True).items():
        setattr(plan, field, value)
    db.commit()
    db.refresh(plan)
    return plan


# ---------- 收入统计 ----------

@router.get("/revenue/stats", response_model=RevenueStatsOut)
def revenue_stats(
    db: Session = Depends(get_db),
    current: User = Depends(get_current_admin),
):
    """收入统计"""
    _require_super_admin(current)
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

    def _sum(tx_type: str, positive: bool, since=None) -> int:
        q = db.query(func.coalesce(func.sum(WalletTransaction.amount), 0)).filter(
            WalletTransaction.tx_type == tx_type,
        )
        if since:
            q = q.filter(WalletTransaction.created_at >= since)
        val = q.scalar() or 0
        return abs(val)

    return RevenueStatsOut(
        total_recharge=_sum("recharge", True),
        total_consume=_sum("purchase_membership", False) + _sum("purchase_credit", False) + _sum("ai_generate", False),
        total_refund=_sum("refund", True),
        month_recharge=_sum("recharge", True, month_start),
        month_consume=_sum("purchase_membership", False, month_start) + _sum("purchase_credit", False, month_start) + _sum("ai_generate", False, month_start),
        active_members=db.query(func.count(User.id)).filter(
            User.membership_status == "active",
        ).scalar() or 0,
        active_credits=db.query(func.count(SessionCredit.id)).filter(
            SessionCredit.status == "unused",
            SessionCredit.expire_at > now,
        ).scalar() or 0,
    )
