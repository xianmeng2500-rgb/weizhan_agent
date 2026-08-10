"""统计路由"""
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import User, Site
from app.utils.deps import get_current_admin, assert_site_access
from app.services.stats_service import get_overview, get_module_stats, get_trend, get_dashboard_overview
from app.schemas.stats import StatsOverview, ModuleStatItem, StatsTrend, DashboardOverview

router = APIRouter(prefix="/sites/{site_id}/stats", tags=["统计"])

dashboard_router = APIRouter(prefix="/stats", tags=["工作台统计"])


def _assert_site(db: Session, site_id: int, current: User) -> Site:
    site = db.query(Site).filter(Site.id == site_id).first()
    if not site:
        raise HTTPException(status_code=404, detail="微站不存在")
    assert_site_access(site, current)
    return site


@router.get("/overview", response_model=StatsOverview)
def overview(
    site_id: int,
    db: Session = Depends(get_db),
    current: User = Depends(get_current_admin),
):
    """总览统计"""
    _assert_site(db, site_id, current)
    return get_overview(db, site_id)


@dashboard_router.get("/overview", response_model=DashboardOverview)
def dashboard_overview(
    db: Session = Depends(get_db),
    current: User = Depends(get_current_admin),
):
    """工作台首页全局统计（跨所有微站聚合，按角色过滤可见范围）"""
    return get_dashboard_overview(db, current)


@router.get("/modules", response_model=list[ModuleStatItem])
def module_stats(
    site_id: int,
    db: Session = Depends(get_db),
    current: User = Depends(get_current_admin),
):
    """模块点击统计"""
    _assert_site(db, site_id, current)
    return get_module_stats(db, site_id)


@router.get("/trend", response_model=StatsTrend)
def trend(
    site_id: int,
    days: int = Query(30, ge=1, le=365),
    db: Session = Depends(get_db),
    current: User = Depends(get_current_admin),
):
    """访问趋势"""
    _assert_site(db, site_id, current)
    return get_trend(db, site_id, days)
