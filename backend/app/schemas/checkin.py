"""签到系统相关Schema"""
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field


class CheckinConfigUpdate(BaseModel):
    """后台保存签到配置（站点级，已废弃时间窗，保留兼容）"""
    checkin_start_at: Optional[datetime] = Field(None, description="[已废弃] 站点级开始时间")
    checkin_end_at: Optional[datetime] = Field(None, description="[已废弃] 站点级结束时间")


class SessionCreate(BaseModel):
    """创建签到场次"""
    name: str = Field(..., max_length=64, description="场次名称")
    start_at: Optional[datetime] = Field(None, description="签到开始时间, 可空")
    end_at: Optional[datetime] = Field(None, description="签到结束时间, 可空")
    enabled: bool = Field(True, description="是否启用")
    sort_order: int = Field(0, description="排序")


class SessionUpdate(BaseModel):
    """更新签到场次"""
    name: Optional[str] = Field(None, max_length=64, description="场次名称")
    start_at: Optional[datetime] = Field(None, description="签到开始时间")
    end_at: Optional[datetime] = Field(None, description="签到结束时间")
    enabled: Optional[bool] = Field(None, description="是否启用")
    sort_order: Optional[int] = Field(None, description="排序")


class ScanCheckinRequest(BaseModel):
    """后台扫码核销请求"""
    code: str = Field(..., description="二维码内容(静态签到码)")
    session_id: Optional[int] = Field(None, description="签到场次ID，不传则取第一个启用的场次")


class ManualCheckinRequest(BaseModel):
    """后台人工补签请求"""
    account_id: int = Field(..., description="微站登录账号ID")
    session_id: Optional[int] = Field(None, description="签到场次ID")
    remark: Optional[str] = Field(None, max_length=255, description="补签原因")


class RevokeCheckinRequest(BaseModel):
    """后台撤销签到请求"""
    remark: Optional[str] = Field(None, max_length=255, description="撤销原因")


class CheckinSessionOut(BaseModel):
    """场次信息（H5 端用）"""
    id: int
    name: str
    start_at: Optional[datetime] = None
    end_at: Optional[datetime] = None
    enabled: bool = True
    status: str = "pending"  # pending/done/not_started/ended/disabled


class CheckinStatusOut(BaseModel):
    """H5 - 查询当前用户签到状态（多场次）"""
    site_id: int
    need_checkin: bool
    registered: bool = False
    sessions: List[CheckinSessionOut] = []
    all_checked_in: bool = False
    status: str = "unknown"  # disabled/not_registered/no_sessions/pending/done


class CheckinQrcodeOut(BaseModel):
    """H5 - 获取静态二维码内容"""
    code: str
    status: str
