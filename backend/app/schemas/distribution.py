"""分销相关 Schema"""
from datetime import datetime
from pydantic import BaseModel, Field


class DistributionConfigOut(BaseModel):
    enabled: bool
    rebate_rate: int


class DistributionConfigUpdate(BaseModel):
    enabled: bool | None = None
    rebate_rate: int | None = Field(None, ge=0, le=20)


class MyCodeOut(BaseModel):
    recommend_code: str
    enabled: bool
    rebate_rate: int
    referral_count: int
    total_order_amount: int
    total_rebate: int
    pending_clawback: int


class RebateRecordOut(BaseModel):
    id: int
    distributor_id: int
    distributor_name: str | None = None
    customer_id: int
    customer_name: str | None = None
    order_type: str
    order_ref: int
    order_amount: int
    rebate_rate: int
    rebate_amount: int
    status: str
    created_at: datetime | None = None


class PaginatedRebates(BaseModel):
    total: int
    page: int
    page_size: int
    items: list[RebateRecordOut]


class RebateRankItem(BaseModel):
    distributor_id: int
    distributor_name: str | None = None
    referral_count: int
    total_order_amount: int
    total_rebate: int


class DistributionAdminStatsOut(BaseModel):
    """分销渠道概况（超管工作台）"""
    referral_count: int = 0
    total_order_amount: int = 0
    total_rebate: int = 0
    distributor_count: int = 0
