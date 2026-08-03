"""统计路由"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import User
from app.utils.deps import get_current_admin
from app.services.stats_service import get_overview, get_module_stats, get_trend
from app.schemas.stats import StatsOverview, ModuleStatItem, StatsTrend

router = APIRouter(prefix="/sites/{site_id}/stats", tags=["统计"])


@router.get("/overview", response_model=StatsOverview)
def overview(
    site_id: int,
    db: Session = Depends(get_db),
    current: User = Depends(get_current_admin),
):
    """总览统计"""
    return get_overview(db, site_id)


@router.get("/modules", response_model=list[ModuleStatItem])
def module_stats(
    site_id: int,
    db: Session = Depends(get_db),
    current: User = Depends(get_current_admin),
):
    """模块点击统计"""
    return get_module_stats(db, site_id)


@router.get("/trend", response_model=StatsTrend)
def trend(
    site_id: int,
    days: int = Query(30, ge=1, le=365),
    db: Session = Depends(get_db),
    current: User = Depends(get_current_admin),
):
    """访问趋势"""
    return get_trend(db, site_id, days)
