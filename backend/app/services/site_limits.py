"""微站容量限制读取服务

单个微站的报名人数、需登录账号数均有上限，上限值可在系统配置（SystemConfig）
中由超管调整，读取失败或未配置时回退到默认值 2000。
"""
from sqlalchemy.orm import Session
from app.models import SystemConfig

DEFAULT_ACCOUNTS_LIMIT = 2000
DEFAULT_SUBMISSIONS_LIMIT = 2000


def get_site_limits(db: Session) -> tuple[int, int]:
    """返回 (登录账号数上限, 报名人数上限)。"""
    cfg = db.query(SystemConfig).filter(SystemConfig.id == 1).first()
    accounts = cfg.max_accounts_per_site if cfg and cfg.max_accounts_per_site else DEFAULT_ACCOUNTS_LIMIT
    submissions = cfg.max_submissions_per_site if cfg and cfg.max_submissions_per_site else DEFAULT_SUBMISSIONS_LIMIT
    return accounts, submissions
