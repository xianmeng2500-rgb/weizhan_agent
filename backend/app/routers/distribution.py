"""分销路由：配置（超管）/ 我的推广码 / 返佣记录 / 撤销 / 排行"""
import logging

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import User, RebateRecord
from app.utils.deps import get_current_admin, ROLE_SUPER_ADMIN
from app.services import distribution_service
from app.services.distribution_service import (
    get_distribution_config,
    get_or_create_recommend_code,
    distributor_stats,
)
from app.schemas.distribution import (
    DistributionConfigOut, DistributionConfigUpdate,
    MyCodeOut, RebateRecordOut, PaginatedRebates, RebateRankItem,
    DistributionAdminStatsOut,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/distribution", tags=["分销"])


def _require_super_admin(current: User):
    if current.role != ROLE_SUPER_ADMIN:
        raise HTTPException(status_code=403, detail="仅超级管理员可操作")


def _to_out(r: RebateRecord, db: Session) -> RebateRecordOut:
    distributor = db.query(User).filter(User.id == r.distributor_id).first()
    customer = db.query(User).filter(User.id == r.customer_id).first()
    return RebateRecordOut(
        id=r.id,
        distributor_id=r.distributor_id,
        distributor_name=(distributor.nickname or distributor.username) if distributor else None,
        customer_id=r.customer_id,
        customer_name=(customer.nickname or customer.username) if customer else None,
        order_type=r.order_type,
        order_ref=r.order_ref,
        order_amount=r.order_amount,
        rebate_rate=r.rebate_rate,
        rebate_amount=r.rebate_amount,
        status=r.status,
        created_at=r.created_at,
    )


# ---------- 分销设置（超管） ----------

@router.get("/config", response_model=DistributionConfigOut)
def read_distribution_config(
    db: Session = Depends(get_db),
    current: User = Depends(get_current_admin),
):
    """分销配置（超管读写；普通用户只读返回，供推广中心展示规则）"""
    enabled, rate = get_distribution_config(db)
    return DistributionConfigOut(enabled=enabled, rebate_rate=rate)


@router.put("/config", response_model=DistributionConfigOut)
def update_distribution_config(
    req: DistributionConfigUpdate,
    db: Session = Depends(get_db),
    current: User = Depends(get_current_admin),
):
    """更新分销配置（超管）"""
    _require_super_admin(current)
    from app.models import SystemConfig
    config = db.query(SystemConfig).filter(SystemConfig.id == 1).first()
    if not config:
        config = SystemConfig(id=1)
        db.add(config)
    if req.enabled is not None:
        config.distribution_enabled = req.enabled
    if req.rebate_rate is not None:
        config.rebate_rate = max(0, min(req.rebate_rate, 20))
    db.commit()
    enabled, rate = get_distribution_config(db)
    return DistributionConfigOut(enabled=enabled, rebate_rate=rate)


# ---------- 我的推广码与统计（分销商） ----------

@router.get("/my-code", response_model=MyCodeOut)
def my_promotion(
    db: Session = Depends(get_db),
    current: User = Depends(get_current_admin),
):
    """我的推广码 + 推广统计"""
    code = get_or_create_recommend_code(db, current)
    enabled, rate = get_distribution_config(db)
    stats = distributor_stats(db, current.id)
    return MyCodeOut(
        recommend_code=code,
        enabled=enabled,
        rebate_rate=rate,
        **stats,
    )


# ---------- 返佣流水（分销商） ----------

@router.get("/rebates", response_model=PaginatedRebates)
def my_rebates(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current: User = Depends(get_current_admin),
):
    """我的返佣流水"""
    q = db.query(RebateRecord).filter(RebateRecord.distributor_id == current.id)
    total = q.count()
    items = q.order_by(RebateRecord.created_at.desc()).offset((page - 1) * page_size).limit(page_size).all()
    return PaginatedRebates(
        total=total, page=page, page_size=page_size,
        items=[_to_out(r, db) for r in items],
    )


# ---------- 全量返佣记录（超管） ----------

@router.get("/admin/rebates", response_model=PaginatedRebates)
def all_rebates(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    keyword: str | None = None,
    status: str | None = None,
    db: Session = Depends(get_db),
    current: User = Depends(get_current_admin),
):
    """全量返佣记录（超管，可按分销商/客户关键字与状态筛选）"""
    _require_super_admin(current)
    q = db.query(RebateRecord)
    if status:
        q = q.filter(RebateRecord.status == status)
    if keyword:
        user_ids = [
            u.id for u in db.query(User).filter(
                (User.username.like(f"%{keyword}%")) | (User.nickname.like(f"%{keyword}%"))
            ).all()
        ]
        q = q.filter((RebateRecord.distributor_id.in_(user_ids)) | (RebateRecord.customer_id.in_(user_ids)))
    total = q.count()
    items = q.order_by(RebateRecord.created_at.desc()).offset((page - 1) * page_size).limit(page_size).all()
    return PaginatedRebates(
        total=total, page=page, page_size=page_size,
        items=[_to_out(r, db) for r in items],
    )


@router.post("/admin/rebates/{rebate_id}/revoke")
def revoke_rebate(
    rebate_id: int,
    db: Session = Depends(get_db),
    current: User = Depends(get_current_admin),
):
    """撤销返佣（超管）"""
    _require_super_admin(current)
    try:
        record = distribution_service.revoke_rebate(db, rebate_id, current)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return _to_out(record, db)


# ---------- 分销渠道概况（超管，工作台卡片） ----------

@router.get("/admin/stats", response_model=DistributionAdminStatsOut)
def admin_distribution_stats(
    db: Session = Depends(get_db),
    current: User = Depends(get_current_admin),
):
    """分销渠道概况：拉新数 / 成交总额 / 返佣支出 / 有返佣的分销商数"""
    _require_super_admin(current)
    rows = db.query(RebateRecord).all()
    customers = set()
    distributors = set()
    total_order = 0
    total_rebate = 0
    for r in rows:
        customers.add(r.customer_id)
        distributors.add(r.distributor_id)
        total_order += r.order_amount
        if r.status in ("settled", "pending_clawback"):
            total_rebate += r.rebate_amount
    return DistributionAdminStatsOut(
        referral_count=len(customers),
        total_order_amount=total_order,
        total_rebate=total_rebate,
        distributor_count=len(distributors),
    )


# ---------- 分销商排行（超管） ----------

@router.get("/admin/ranking", response_model=list[RebateRankItem])
def rebate_ranking(
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current: User = Depends(get_current_admin),
):
    """分销商排行（按累计返佣金额倒序）"""
    _require_super_admin(current)
    rows = db.query(
        RebateRecord.distributor_id,
        func.count(func.distinct(RebateRecord.customer_id)).label("referral_count"),
        func.coalesce(func.sum(RebateRecord.order_amount), 0).label("total_order"),
        func.coalesce(func.sum(RebateRecord.rebate_amount), 0).label("total_rebate"),
    ).group_by(RebateRecord.distributor_id).order_by(func.sum(RebateRecord.rebate_amount).desc()).limit(limit).all()

    items = []
    for row in rows:
        u = db.query(User).filter(User.id == row.distributor_id).first()
        items.append(RebateRankItem(
            distributor_id=row.distributor_id,
            distributor_name=(u.nickname or u.username) if u else None,
            referral_count=row.referral_count,
            total_order_amount=row.total_order,
            total_rebate=row.total_rebate,
        ))
    return items
