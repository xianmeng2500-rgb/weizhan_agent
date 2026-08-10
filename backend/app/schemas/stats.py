"""统计相关Schema"""
from datetime import date
from pydantic import BaseModel


class StatsOverview(BaseModel):
    total_pv: int = 0
    total_uv: int = 0
    today_pv: int = 0
    today_uv: int = 0
    account_count: int = 0
    module_count: int = 0


class DashboardOverview(BaseModel):
    """工作台首页全局统计"""
    total_sites: int = 0
    online_sites: int = 0
    total_pv: int = 0
    total_uv: int = 0


class ModuleStatItem(BaseModel):
    module_id: int
    title: str
    click_count: int


class TrendItem(BaseModel):
    date: date
    pv: int
    uv: int


class StatsTrend(BaseModel):
    items: list[TrendItem]
