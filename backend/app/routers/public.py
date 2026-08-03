"""公开接口路由 - H5前端访问"""
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Site, Module, SiteAccount, AccessLog, ModuleClickLog, AccountModulePermission
from app.utils.security import verify_password, create_access_token
from app.utils.deps import get_optional_frontend_account
from app.schemas.auth import FrontendLoginRequest, TokenResponse
from app.schemas.module import ModuleOut
from pydantic import BaseModel

router = APIRouter(prefix="/p", tags=["公开接口"])


class AccessRequest(BaseModel):
    ip: str | None = None


class ClickRequest(BaseModel):
    module_id: int


def _check_site_status(site: Site) -> None:
    """检查微站时间状态"""
    now = datetime.utcnow()
    if site.status == "offline":
        raise HTTPException(status_code=403, detail=site.close_message or "微站已关闭")
    if site.start_time and now < site.start_time:
        raise HTTPException(status_code=403, detail="微站尚未开启")
    if site.end_time and now > site.end_time:
        raise HTTPException(status_code=403, detail=site.close_message or "微站已关闭")


@router.get("/sites/{code}")
def get_site_public(
    code: str,
    db: Session = Depends(get_db),
):
    """H5 - 获取微站展示信息(无需认证)"""
    site = db.query(Site).filter(Site.code == code, Site.status == "online").first()
    if not site:
        raise HTTPException(status_code=404, detail="微站不存在或未上线")
    _check_site_status(site)
    return {
        "id": site.id,
        "name": site.name,
        "code": site.code,
        "template": site.template,
        "layout": site.layout,
        "kv_image": site.kv_image,
        "background_color": site.background_color,
        "need_login": site.need_login,
        "start_time": site.start_time,
        "end_time": site.end_time,
        "close_message": site.close_message,
    }


@router.post("/sites/{code}/login", response_model=TokenResponse)
def login_frontend(
    code: str,
    req: FrontendLoginRequest,
    db: Session = Depends(get_db),
):
    """H5 - 前端用户登录"""
    site = db.query(Site).filter(Site.code == code).first()
    if not site:
        raise HTTPException(status_code=404, detail="微站不存在")
    _check_site_status(site)

    acc = db.query(SiteAccount).filter(
        SiteAccount.site_id == site.id,
        SiteAccount.username == req.username,
    ).first()
    if not acc or not verify_password(req.password, acc.password_hash):
        raise HTTPException(status_code=401, detail="账号或密码错误")
    if not acc.is_active:
        raise HTTPException(status_code=403, detail="账号已被禁用")

    token = create_access_token(
        subject=str(acc.id),
        extra_claims={"site_id": str(site.id)},
        token_type="frontend",
    )
    return TokenResponse(access_token=token, nickname=acc.nickname or acc.username)


@router.get("/sites/{code}/modules", response_model=list[ModuleOut])
def get_visible_modules(
    code: str,
    db: Session = Depends(get_db),
    account: SiteAccount | None = Depends(get_optional_frontend_account),
):
    """H5 - 获取可见模块列表"""
    site = db.query(Site).filter(Site.code == code, Site.status == "online").first()
    if not site:
        raise HTTPException(status_code=404, detail="微站不存在")
    _check_site_status(site)

    if site.need_login and not account:
        raise HTTPException(status_code=401, detail="请先登录")

    # 获取所有启用的模块
    now = datetime.utcnow()
    query = db.query(Module).filter(
        Module.site_id == site.id,
        Module.is_active == True,
    )
    modules = query.order_by(Module.sort_order).all()

    # 过滤: 时间控制
    visible = []
    for m in modules:
        if m.start_time and now < m.start_time:
            continue
        if m.end_time and now > m.end_time:
            continue
        visible.append(m)

    # 如果需要登录, 过滤权限
    if site.need_login and account:
        permitted_ids = {
            p.module_id for p in
            db.query(AccountModulePermission).filter(
                AccountModulePermission.account_id == account.id
            ).all()
        }
        # 如果没有任何权限分配, 则所有模块可见(默认权限)
        if permitted_ids:
            visible = [m for m in visible if m.id in permitted_ids]

    # 对外部隐藏富文本内容(减少传输量, 需要时单独获取)
    result = []
    for m in visible:
        result.append(ModuleOut(
            id=m.id,
            site_id=m.site_id,
            title=m.title,
            icon=m.icon,
            sort_order=m.sort_order,
            content_type=m.content_type,
            external_url=m.external_url,
            rich_content=None,  # 列表不返回内容
            start_time=m.start_time,
            end_time=m.end_time,
            is_active=m.is_active,
            created_at=m.created_at,
            updated_at=m.updated_at,
        ))
    return result


@router.get("/modules/{module_id}")
def get_module_content(
    module_id: int,
    db: Session = Depends(get_db),
    account: SiteAccount | None = Depends(get_optional_frontend_account),
):
    """H5 - 获取模块内容"""
    module = db.query(Module).filter(Module.id == module_id).first()
    if not module:
        raise HTTPException(status_code=404, detail="模块不存在")
    if not module.is_active:
        raise HTTPException(status_code=404, detail="模块不存在")

    # 检查时间
    now = datetime.utcnow()
    if module.start_time and now < module.start_time:
        raise HTTPException(status_code=403, detail="模块尚未开启")
    if module.end_time and now > module.end_time:
        raise HTTPException(status_code=403, detail="模块已关闭")

    # 检查权限
    site = db.query(Site).filter(Site.id == module.site_id).first()
    if site and site.need_login and account:
        permitted_ids = {
            p.module_id for p in
            db.query(AccountModulePermission).filter(
                AccountModulePermission.account_id == account.id
            ).all()
        }
        if permitted_ids and module.id not in permitted_ids:
            raise HTTPException(status_code=403, detail="无权访问此模块")

    return {
        "id": module.id,
        "title": module.title,
        "content_type": module.content_type,
        "external_url": module.external_url,
        "rich_content": module.rich_content,
    }


@router.post("/sites/{code}/access")
def record_access(
    code: str,
    request: Request,
    db: Session = Depends(get_db),
    account: SiteAccount | None = Depends(get_optional_frontend_account),
):
    """H5 - 上报访问日志"""
    site = db.query(Site).filter(Site.code == code).first()
    if not site:
        raise HTTPException(status_code=404, detail="微站不存在")

    log = AccessLog(
        site_id=site.id,
        account_id=account.id if account else None,
        ip=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent", "")[:500],
        visit_date=datetime.utcnow().date(),
        visit_time=datetime.utcnow(),
    )
    db.add(log)
    db.commit()
    return {"message": "ok"}


@router.post("/sites/{code}/click")
def record_click(
    code: str,
    req: ClickRequest,
    request: Request,
    db: Session = Depends(get_db),
    account: SiteAccount | None = Depends(get_optional_frontend_account),
):
    """H5 - 上报模块点击"""
    site = db.query(Site).filter(Site.code == code).first()
    if not site:
        raise HTTPException(status_code=404, detail="微站不存在")

    log = ModuleClickLog(
        site_id=site.id,
        module_id=req.module_id,
        account_id=account.id if account else None,
        click_date=datetime.utcnow().date(),
        click_time=datetime.utcnow(),
    )
    db.add(log)
    db.commit()
    return {"message": "ok"}
