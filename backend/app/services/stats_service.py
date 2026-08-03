"""统计服务"""
from datetime import date, datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import func, distinct
from app.models import AccessLog, ModuleClickLog, SiteAccount, Module
from app.schemas.stats import StatsOverview, ModuleStatItem, TrendItem, StatsTrend


def get_overview(db: Session, site_id: int) -> StatsOverview:
    """获取微站总览统计"""
    total_pv = db.query(func.count(AccessLog.id)).filter(AccessLog.site_id == site_id).scalar() or 0
    total_uv = db.query(func.count(distinct(AccessLog.ip))).filter(AccessLog.site_id == site_id).scalar() or 0

    today = date.today()
    today_pv = (
        db.query(func.count(AccessLog.id))
        .filter(AccessLog.site_id == site_id, AccessLog.visit_date == today)
        .scalar() or 0
    )
    today_uv = (
        db.query(func.count(distinct(AccessLog.ip)))
        .filter(AccessLog.site_id == site_id, AccessLog.visit_date == today)
        .scalar() or 0
    )

    account_count = db.query(func.count(SiteAccount.id)).filter(SiteAccount.site_id == site_id).scalar() or 0
    module_count = db.query(func.count(Module.id)).filter(Module.site_id == site_id).scalar() or 0

    return StatsOverview(
        total_pv=total_pv,
        total_uv=total_uv,
        today_pv=today_pv,
        today_uv=today_uv,
        account_count=account_count,
        module_count=module_count,
    )


def get_module_stats(db: Session, site_id: int) -> list[ModuleStatItem]:
    """获取模块点击统计"""
    modules = db.query(Module).filter(Module.site_id == site_id).all()
    result = []
    for m in modules:
        click_count = (
            db.query(func.count(ModuleClickLog.id))
            .filter(ModuleClickLog.module_id == m.id)
            .scalar() or 0
        )
        result.append(ModuleStatItem(
            module_id=m.id,
            title=m.title,
            click_count=click_count,
        ))
    return result


def get_trend(db: Session, site_id: int, days: int = 30) -> StatsTrend:
    """获取访问趋势"""
    start_date = date.today() - timedelta(days=days - 1)
    rows = (
        db.query(
            AccessLog.visit_date.label("d"),
            func.count(AccessLog.id).label("pv"),
            func.count(distinct(AccessLog.ip)).label("uv"),
        )
        .filter(AccessLog.site_id == site_id, AccessLog.visit_date >= start_date)
        .group_by(AccessLog.visit_date)
        .order_by(AccessLog.visit_date)
        .all()
    )

    # 填充无数据的日期
    date_map = {row.d: (row.pv, row.uv) for row in rows}
    items = []
    for i in range(days):
        d = start_date + timedelta(days=i)
        pv, uv = date_map.get(d, (0, 0))
        items.append(TrendItem(date=d, pv=pv, uv=uv))

    return StatsTrend(items=items)
