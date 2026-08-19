"""计费业务逻辑：钱包充值/购买会员/购买额度/扣减额度/退款/过期处理"""
import logging
from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import Session

from app.models import User, MembershipPlan, Membership, SessionCredit, WalletTransaction

logger = logging.getLogger(__name__)

CREDIT_VALID_DAYS = 365  # 场次额度有效期（天）
AI_IMAGE_PRICE_CENTS = 10  # AI 生图单价：0.1 元/张


class InsufficientBalanceError(Exception):
    def __init__(self, balance: int, required: int):
        self.balance = balance
        self.required = required
        super().__init__(f"余额不足: 当前{balance}分, 需要{required}分")


def utcnow() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


def get_billing_owner(db: Session, user: User) -> User:
    """获取计费归属账号：sub_admin 继承父账号（created_by）"""
    if user.role == "sub_admin" and user.created_by:
        parent = db.query(User).filter(User.id == user.created_by).first()
        if parent:
            return parent
    return user


def assert_active_membership(db: Session, user: User):
    """校验会员状态，无效则抛 HTTPException（微站创建/编辑前置校验用）"""
    from fastapi import HTTPException
    if user.role == "super_admin":
        return
    owner = get_billing_owner(db, user)
    if owner.membership_status != "active":
        raise HTTPException(
            status_code=403,
            detail="MEMBERSHIP_EXPIRED",
        )


def recalc_credit_balance(db: Session, user_id: int):
    """重算用户可用额度余额（unused且未过期）并更新缓存"""
    count = db.query(SessionCredit).filter(
        SessionCredit.user_id == user_id,
        SessionCredit.status == "unused",
        SessionCredit.expire_at > utcnow(),
    ).count()
    user = db.query(User).filter(User.id == user_id).first()
    if user:
        user.session_credit_balance = count
    return count


def refresh_membership_cache(db: Session, user_id: int):
    """根据 memberships 表刷新用户会员状态缓存"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        return
    latest = db.query(Membership).filter(
        Membership.user_id == user_id,
        Membership.status == "active",
    ).order_by(Membership.end_at.desc()).first()
    if latest and latest.end_at > utcnow():
        user.membership_status = "active"
        user.membership_end_at = latest.end_at
    else:
        if latest:
            latest.status = "expired"
        user.membership_status = "expired" if user.membership_status != "none" else "none"
        user.membership_end_at = latest.end_at if latest else None


# ---------- 充值 ----------

def recharge(db: Session, user_id: int, amount: int, operator: User, remark: str | None) -> WalletTransaction:
    """超管为用户充值"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise ValueError("用户不存在")
    user.wallet_balance += amount
    tx = WalletTransaction(
        user_id=user_id,
        tx_type="recharge",
        amount=amount,
        balance_after=user.wallet_balance,
        operator_id=operator.id,
        remark=remark,
    )
    db.add(tx)
    db.commit()
    db.refresh(tx)
    return tx


# ---------- 购买会员 ----------

def purchase_membership(db: Session, user: User, plan_id: int) -> Membership:
    """用户用余额购买会员套餐"""
    plan = db.query(MembershipPlan).filter(MembershipPlan.id == plan_id).first()
    if not plan or not plan.is_active or plan.plan_type != "membership":
        raise ValueError("套餐不存在或已停用")

    owner = get_billing_owner(db, user)
    if user.role == "sub_admin":
        raise ValueError("子账号无权购买，请使用主账号购买")
    if owner.wallet_balance < plan.price:
        raise InsufficientBalanceError(owner.wallet_balance, plan.price)

    now = utcnow()
    latest = db.query(Membership).filter(
        Membership.user_id == owner.id,
        Membership.status == "active",
    ).order_by(Membership.end_at.desc()).first()

    if latest and latest.end_at > now:
        start_at = latest.end_at  # 续费：从现有到期时间顺延
        end_at = latest.end_at + timedelta(days=plan.duration_days)
    else:
        start_at = now
        end_at = now + timedelta(days=plan.duration_days)

    membership = Membership(
        user_id=owner.id,
        plan_id=plan.id,
        start_at=start_at,
        end_at=end_at,
        status="active",
    )
    db.add(membership)
    db.flush()  # 拿到 membership.id

    owner.wallet_balance -= plan.price
    tx = WalletTransaction(
        user_id=owner.id,
        tx_type="purchase_membership",
        amount=-plan.price,
        balance_after=owner.wallet_balance,
        plan_id=plan.id,
        membership_id=membership.id,
    )
    db.add(tx)
    owner.membership_status = "active"
    owner.membership_end_at = end_at
    db.commit()
    db.refresh(membership)
    return membership


# ---------- 购买场次额度 ----------

def purchase_credits(db: Session, user: User, plan_id: int, quantity: int) -> list[SessionCredit]:
    """用户用余额购买场次额度"""
    plan = db.query(MembershipPlan).filter(MembershipPlan.id == plan_id).first()
    if not plan or not plan.is_active or plan.plan_type != "session_credit":
        raise ValueError("套餐不存在或已停用")

    if user.role == "sub_admin":
        raise ValueError("子账号无权购买，请使用主账号购买")

    unit = plan.credit_quantity or 1  # 每份套餐包含的额度数
    total_credits = unit * quantity
    total_price = plan.price * quantity
    if user.wallet_balance < total_price:
        raise InsufficientBalanceError(user.wallet_balance, total_price)

    expire_at = utcnow() + timedelta(days=CREDIT_VALID_DAYS)
    user.wallet_balance -= total_price
    tx = WalletTransaction(
        user_id=user.id,
        tx_type="purchase_credit",
        amount=-total_price,
        balance_after=user.wallet_balance,
        plan_id=plan.id,
    )
    db.add(tx)
    db.flush()  # 拿到 tx.id

    credits = []
    for _ in range(total_credits):
        c = SessionCredit(
            user_id=user.id,
            transaction_id=tx.id,
            status="unused",
            expire_at=expire_at,
        )
        db.add(c)
        credits.append(c)
    db.flush()
    tx.session_credit_ids = ",".join(str(c.id) for c in credits)
    recalc_credit_balance(db, user.id)
    db.commit()
    return credits


# ---------- AI 生图按张扣费 ----------

def assert_ai_generate_balance(db: Session, user: User, count: int) -> int:
    """AI 生图预检：返回预计扣费金额(分)。超级管理员免扣费；余额不足抛 InsufficientBalanceError。"""
    if user.role == "super_admin":
        return 0
    owner = get_billing_owner(db, user)
    cost = AI_IMAGE_PRICE_CENTS * count
    if owner.wallet_balance < cost:
        raise InsufficientBalanceError(owner.wallet_balance, cost)
    return cost


def charge_ai_generate(
    db: Session, user: User, count: int, remark: str | None = None
) -> WalletTransaction | None:
    """AI 生图扣费（0.1 元/张）：扣减计费主体余额并写入流水。超级管理员免扣费。

    与生成记录在同一事务内调用（由调用方统一 commit）。超管返回 None（不扣费、不写流水）。
    """
    if user.role == "super_admin":
        return None
    owner = get_billing_owner(db, user)
    cost = AI_IMAGE_PRICE_CENTS * count
    if owner.wallet_balance < cost:
        raise InsufficientBalanceError(owner.wallet_balance, cost)
    owner.wallet_balance -= cost
    tx = WalletTransaction(
        user_id=owner.id,
        tx_type="ai_generate",
        amount=-cost,
        balance_after=owner.wallet_balance,
        remark=remark,
    )
    db.add(tx)
    db.flush()
    return tx


# ---------- 微站上线时扣减额度 ----------

def consume_credit_for_site_online(db: Session, user: User, site_id: int):
    """微站上线后扣减1个额度（优先扣减即将过期的）。额度不足抛 ValueError。

    规则(v1.2)：每次上线扣1个额度；下线不退；再次上线重新扣。
    """
    owner = get_billing_owner(db, user)
    credit = db.query(SessionCredit).filter(
        SessionCredit.user_id == owner.id,
        SessionCredit.status == "unused",
        SessionCredit.expire_at > utcnow(),
    ).order_by(SessionCredit.expire_at.asc()).first()
    if not credit:
        raise ValueError("CREDIT_INSUFFICIENT")
    credit.status = "used"
    credit.site_id = site_id
    credit.used_at = utcnow()
    owner.session_credit_balance = max(0, owner.session_credit_balance - 1)
    db.commit()


# ---------- 退款 ----------

def refund_transaction(db: Session, operator: User, transaction_id: int, remark: str | None) -> WalletTransaction:
    """超管按购买流水退款：撤销权益并退回余额"""
    tx = db.query(WalletTransaction).filter(WalletTransaction.id == transaction_id).first()
    if not tx:
        raise ValueError("流水不存在")
    if tx.tx_type not in ("purchase_membership", "purchase_credit"):
        raise ValueError("仅支持对购买流水退款")
    # 已有针对该流水的退款，拒绝重复退款
    existed = db.query(WalletTransaction).filter(
        WalletTransaction.user_id == tx.user_id,
        WalletTransaction.tx_type == "refund",
        WalletTransaction.remark.like(f"%[tx:{tx.id}]%"),
    ).first()
    if existed:
        raise ValueError("该流水已退款")

    user = db.query(User).filter(User.id == tx.user_id).first()
    refund_amount = -tx.amount  # 退回金额默认等于原消费金额

    if tx.tx_type == "purchase_membership":
        # 回退会员到期时间
        m = db.query(Membership).filter(Membership.id == tx.membership_id).first() if tx.membership_id else None
        if m and m.status == "active":
            plan = db.query(MembershipPlan).filter(MembershipPlan.id == m.plan_id).first()
            days = plan.duration_days if plan else 365
            new_end = m.end_at - timedelta(days=days)
            if new_end <= utcnow():
                m.status = "refunded"
            else:
                m.end_at = new_end
        elif m and m.status == "expired":
            # 已过期的会员退款：标记后按比例全退（简化：全退）
            m.status = "refunded"
    else:
        # 场次额度退款：仅退未使用的
        credit_ids = [int(x) for x in (tx.session_credit_ids or "").split(",") if x.strip().isdigit()]
        credits = db.query(SessionCredit).filter(SessionCredit.id.in_(credit_ids)).all() if credit_ids else []
        refundable = [c for c in credits if c.status in ("unused",)]
        expired_unexpired = [c for c in refundable if c.expire_at > utcnow()]
        total = len(credits) or 1
        if len(expired_unexpired) == total:
            refund_amount = -tx.amount
        else:
            refund_amount = int(-tx.amount * len(expired_unexpired) / total)
        for c in expired_unexpired:
            c.status = "refunded"
        if refund_amount <= 0:
            raise ValueError("该流水的额度已全部使用，无可退金额")

    user.wallet_balance += refund_amount
    refund_tx = WalletTransaction(
        user_id=tx.user_id,
        tx_type="refund",
        amount=refund_amount,
        balance_after=user.wallet_balance,
        operator_id=operator.id,
        remark=f"[tx:{tx.id}] {remark or '超管退款'}",
    )
    db.add(refund_tx)
    db.flush()  # autoflush=False: 先落库状态变更(额度refunded/会员end_at)，缓存重算才能读到新值
    # 刷新缓存
    refresh_membership_cache(db, tx.user_id)
    recalc_credit_balance(db, tx.user_id)
    db.commit()
    db.refresh(refund_tx)
    return refund_tx


# ---------- 过期处理（定时任务） ----------

def expire_memberships(db: Session) -> int:
    """会员过期检查：将到期用户标记为 expired，返回处理数量"""
    now = utcnow()
    users = db.query(User).filter(
        User.membership_status == "active",
        User.membership_end_at < now,
    ).all()
    count = 0
    for u in users:
        u.membership_status = "expired"
        db.query(Membership).filter(
            Membership.user_id == u.id,
            Membership.status == "active",
            Membership.end_at < now,
        ).update({"status": "expired"}, synchronize_session=False)
        count += 1
    if count:
        db.commit()
    return count


def expire_credits(db: Session) -> int:
    """场次额度过期检查：过期未用的额度标记 expired 并重算余额，返回处理数量"""
    now = utcnow()
    expired = db.query(SessionCredit).filter(
        SessionCredit.status == "unused",
        SessionCredit.expire_at < now,
    ).all()
    user_ids = set()
    for c in expired:
        c.status = "expired"
        user_ids.add(c.user_id)
    if user_ids:
        db.commit()
        for uid in user_ids:
            recalc_credit_balance(db, uid)
        db.commit()
    return len(expired)
