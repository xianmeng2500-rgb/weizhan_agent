"""分销业务逻辑：推广码、返佣入账、退款扣回、撤销、挂起扣回"""
import logging
import secrets
import string
from datetime import datetime

from sqlalchemy.orm import Session

from app.models import User, SystemConfig, WalletTransaction, RebateRecord

logger = logging.getLogger(__name__)

PURCHASE_TX_TYPES = ("purchase_membership", "purchase_credit")
DEFAULT_RATE = 10
MAX_RATE = 20


# ---------- 配置 ----------

def get_distribution_config(db: Session) -> tuple[bool, int]:
    """读取分销配置 (enabled, rebate_rate)"""
    config = db.query(SystemConfig).filter(SystemConfig.id == 1).first()
    if not config:
        return False, DEFAULT_RATE
    rate = config.rebate_rate if config.rebate_rate is not None else DEFAULT_RATE
    rate = max(0, min(rate, MAX_RATE))
    return bool(config.distribution_enabled), rate


# ---------- 推广码 ----------

_CODE_ALPHABET = string.ascii_uppercase + string.digits


def _generate_code(db: Session) -> str:
    """生成全局唯一推广码（8 位大写字母+数字，排除易混淆字符 O/0/I/1）"""
    alphabet = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"
    for _ in range(50):
        code = "".join(secrets.choice(alphabet) for _ in range(8))
        if not db.query(User).filter(User.recommend_code == code).first():
            return code
    raise RuntimeError("推广码生成失败，请重试")


def get_or_create_recommend_code(db: Session, user: User) -> str:
    """获取用户的推广码，不存在则生成"""
    if not user.recommend_code:
        user.recommend_code = _generate_code(db)
        db.commit()
        db.refresh(user)
    return user.recommend_code


def resolve_recommend_code(db: Session, code: str) -> User | None:
    """按推广码解析推荐人账号（仅启用账号）"""
    if not code:
        return None
    user = db.query(User).filter(User.recommend_code == code.strip().upper()).first()
    if not user or not user.is_active:
        return None
    return user


# ---------- 返佣入账（购买成功后调用，与购买在同一事务，由调用方 commit） ----------

def credit_rebate(
    db: Session,
    buyer: User,
    order_type: str,
    order_amount: int,
    order_ref: int,
) -> RebateRecord | None:
    """被推荐账号消费后为推荐人入账返佣。

    规则：
    - 分销未启用 / 买家无推荐人 / 推荐人为超管或停用账号 → 不返佣
    - 首次消费校验：买家在本次购买前已有任何购买流水 → 不返佣
    - 返佣金额 = 实付金额 × 比例（向下取整到分），比例由系统配置决定
    - 入账推荐人钱包（rebate_in），同时优先处理其挂起扣回
    """
    enabled, rate = get_distribution_config(db)
    if not enabled or rate <= 0:
        return None
    if not buyer.recommend_by:
        return None
    distributor = db.query(User).filter(User.id == buyer.recommend_by).first()
    if not distributor or not distributor.is_active or distributor.role == "super_admin":
        return None

    # 首次消费校验：本次购买之前已有任何购买流水则不返佣（排除当前 order_ref）
    prior = db.query(WalletTransaction).filter(
        WalletTransaction.user_id == buyer.id,
        WalletTransaction.tx_type.in_(PURCHASE_TX_TYPES),
        WalletTransaction.id != order_ref,
    ).first()
    if prior:
        return None

    rebate_amount = int(order_amount * rate / 100)
    if rebate_amount <= 0:
        return None

    distributor.wallet_balance += rebate_amount
    tx = WalletTransaction(
        user_id=distributor.id,
        tx_type="rebate_in",
        amount=rebate_amount,
        balance_after=distributor.wallet_balance,
        remark=f"分销返佣: {buyer.username or buyer.nickname or ''} {order_type} [tx:{order_ref}]",
    )
    db.add(tx)
    db.flush()

    record = RebateRecord(
        distributor_id=distributor.id,
        customer_id=buyer.id,
        order_type=order_type,
        order_ref=order_ref,
        order_amount=order_amount,
        rebate_rate=rate,
        rebate_amount=rebate_amount,
        status="settled",
    )
    db.add(record)
    db.flush()

    # 优先扣回该推荐人的挂起扣回
    process_pending_clawbacks(db, distributor.id)

    logger.info(
        "[DIST] 返佣入账: 分销商#%s +%s分, 客户#%s %s tx:%s",
        distributor.id, rebate_amount, buyer.id, order_type, order_ref,
    )
    return record


# ---------- 退款扣回（退款成功后调用，与退款在同一事务，由调用方 commit） ----------

def clawback_rebate(db: Session, order_ref: int) -> int:
    """订单退款时自动扣回对应返佣；余额不足则标记 pending_clawback。

    返回处理的返佣记录条数。
    """
    records = db.query(RebateRecord).filter(
        RebateRecord.order_ref == order_ref,
        RebateRecord.status.in_(("settled", "pending_clawback")),
    ).all()
    for record in records:
        distributor = db.query(User).filter(User.id == record.distributor_id).first()
        if not distributor:
            continue
        if distributor.wallet_balance >= record.rebate_amount:
            distributor.wallet_balance -= record.rebate_amount
            db.add(WalletTransaction(
                user_id=distributor.id,
                tx_type="rebate_refund",
                amount=-record.rebate_amount,
                balance_after=distributor.wallet_balance,
                remark=f"返佣扣回(订单退款) [rebate:{record.id}]",
            ))
            record.status = "refunded"
        else:
            record.status = "pending_clawback"
        record.updated_at = datetime.now()
    db.flush()
    return len(records)


# ---------- 挂起扣回优先处理（推荐人钱包入账时调用） ----------

def process_pending_clawbacks(db: Session, distributor_id: int) -> None:
    """推荐人钱包有余额时优先扣回其 pending_clawback 记录"""
    pending = db.query(RebateRecord).filter(
        RebateRecord.distributor_id == distributor_id,
        RebateRecord.status == "pending_clawback",
    ).order_by(RebateRecord.id.asc()).all()
    distributor = db.query(User).filter(User.id == distributor_id).first()
    if not distributor:
        return
    for record in pending:
        if distributor.wallet_balance < record.rebate_amount:
            break
        distributor.wallet_balance -= record.rebate_amount
        db.add(WalletTransaction(
            user_id=distributor.id,
            tx_type="rebate_refund",
            amount=-record.rebate_amount,
            balance_after=distributor.wallet_balance,
            remark=f"返佣补扣回(挂起) [rebate:{record.id}]",
        ))
        record.status = "refunded"
        record.updated_at = datetime.now()


# ---------- 超管撤销 ----------

def revoke_rebate(db: Session, rebate_id: int, operator: User) -> RebateRecord:
    """超管撤销返佣：扣回推荐人钱包并标记 revoked（不区分原订单是否退款）"""
    record = db.query(RebateRecord).filter(RebateRecord.id == rebate_id).first()
    if not record:
        raise ValueError("返佣记录不存在")
    if record.status == "revoked":
        raise ValueError("该记录已撤销")

    distributor = db.query(User).filter(User.id == record.distributor_id).first()
    if distributor and distributor.wallet_balance >= record.rebate_amount:
        distributor.wallet_balance -= record.rebate_amount
        db.add(WalletTransaction(
            user_id=distributor.id,
            tx_type="rebate_refund",
            amount=-record.rebate_amount,
            balance_after=distributor.wallet_balance,
            remark=f"返佣撤销(超管) [rebate:{record.id}]",
        ))
        record.status = "revoked"
    else:
        record.status = "pending_clawback"
    record.updated_at = datetime.now()
    db.commit()
    db.refresh(record)
    return record


# ---------- 统计 ----------

def distributor_stats(db: Session, distributor_id: int) -> dict:
    """分销商统计：累计拉新数 / 累计成交金额 / 累计返佣金额 / 待扣回金额"""
    records = db.query(RebateRecord).filter(RebateRecord.distributor_id == distributor_id).all()
    customers = set()
    total_order = 0
    total_rebate = 0
    pending = 0
    for r in records:
        customers.add(r.customer_id)
        total_order += r.order_amount
        if r.status in ("settled", "pending_clawback"):
            total_rebate += r.rebate_amount
        if r.status == "pending_clawback":
            pending += r.rebate_amount
    return {
        "referral_count": len(customers),
        "total_order_amount": total_order,
        "total_rebate": total_rebate,
        "pending_clawback": pending,
    }
