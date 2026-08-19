"""计费路由（用户侧）：钱包查询/流水/套餐列表/自助购买"""
import logging
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import User, WalletTransaction, MembershipPlan, SessionCredit, Membership
from app.utils.deps import get_current_admin
from app.services import billing_service
from app.services.billing_service import InsufficientBalanceError
from app.schemas.billing import (
    WalletMeOut, WalletTransactionOut, PaginatedTransactions,
    PlanOut, MembershipPurchaseRequest, CreditPurchaseRequest,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/billing", tags=["计费"])


def _utcnow() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


def _fmt_yuan(cents: int) -> str:
    return f"{cents / 100:.2f}"


@router.get("/me", response_model=WalletMeOut)
def my_wallet(
    db: Session = Depends(get_db),
    current: User = Depends(get_current_admin),
):
    """我的钱包+会员+额度汇总"""
    owner = billing_service.get_billing_owner(db, current)
    membership = None
    if owner.membership_status == "active":
        m = db.query(Membership).filter(
            Membership.user_id == owner.id,
            Membership.status == "active",
        ).order_by(Membership.end_at.desc()).first()
        if m:
            plan = db.query(MembershipPlan).filter(MembershipPlan.id == m.plan_id).first()
            membership = {
                "status": "active",
                "plan_name": plan.name if plan else "",
                "start_at": m.start_at,
                "end_at": m.end_at,
                "days_remaining": max(0, (m.end_at - _utcnow()).days),
            }
    elif owner.membership_status == "expired":
        membership = {"status": "expired"}

    # 即将过期的额度（30天内）
    soon = _utcnow() + timedelta(days=30)
    expiring = db.query(SessionCredit).filter(
        SessionCredit.user_id == owner.id,
        SessionCredit.status == "unused",
        SessionCredit.expire_at <= soon,
    ).order_by(SessionCredit.expire_at.asc()).all()

    return WalletMeOut(
        balance=owner.wallet_balance,
        balance_yuan=_fmt_yuan(owner.wallet_balance),
        membership=membership,
        session_credits=owner.session_credit_balance,
        session_credits_expiring=[
            {"id": c.id, "expire_at": c.expire_at} for c in expiring
        ],
    )


@router.get("/transactions", response_model=PaginatedTransactions)
def my_transactions(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current: User = Depends(get_current_admin),
):
    """我的交易流水"""
    owner = billing_service.get_billing_owner(db, current)
    q = db.query(WalletTransaction).filter(WalletTransaction.user_id == owner.id)
    total = q.count()
    items = q.order_by(WalletTransaction.created_at.desc()).offset((page - 1) * page_size).limit(page_size).all()
    return PaginatedTransactions(
        total=total, page=page, page_size=page_size,
        items=[WalletTransactionOut(
            id=t.id, user_id=t.user_id, username=owner.username, tx_type=t.tx_type,
            amount=t.amount, balance_after=t.balance_after, plan_id=t.plan_id,
            plan_name=t.plan.name if t.plan else None, remark=t.remark,
            operator_id=t.operator_id, created_at=t.created_at,
        ) for t in items],
    )


@router.get("/plans", response_model=list[PlanOut])
def list_plans(
    db: Session = Depends(get_db),
    current: User = Depends(get_current_admin),
):
    """套餐列表（购买页展示，仅启用的）"""
    return db.query(MembershipPlan).filter(MembershipPlan.is_active == True).all()  # noqa: E712


@router.post("/membership/purchase")
def purchase_membership(
    req: MembershipPurchaseRequest,
    db: Session = Depends(get_db),
    current: User = Depends(get_current_admin),
):
    """用余额购买会员"""
    if current.role == "super_admin":
        raise HTTPException(status_code=400, detail="超级管理员无需购买会员")
    try:
        m = billing_service.purchase_membership(db, current, req.plan_id)
    except InsufficientBalanceError as e:
        raise HTTPException(status_code=403, detail=f"INSUFFICIENT_BALANCE:当前余额{_fmt_yuan(e.balance)}元, 需要{_fmt_yuan(e.required)}元, 请联系管理员充值")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return {"message": "购买成功", "membership_id": m.id, "end_at": m.end_at}


@router.post("/credits/purchase")
def purchase_credits(
    req: CreditPurchaseRequest,
    db: Session = Depends(get_db),
    current: User = Depends(get_current_admin),
):
    """用余额购买场次额度"""
    if current.role == "super_admin":
        raise HTTPException(status_code=400, detail="超级管理员无需购买场次额度")
    try:
        credits = billing_service.purchase_credits(db, current, req.plan_id, req.quantity)
    except InsufficientBalanceError as e:
        raise HTTPException(status_code=403, detail=f"INSUFFICIENT_BALANCE:当前余额{_fmt_yuan(e.balance)}元, 需要{_fmt_yuan(e.required)}元, 请联系管理员充值")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return {"message": "购买成功", "credits": len(credits), "expire_at": credits[0].expire_at if credits else None}
