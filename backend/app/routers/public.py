"""公开接口路由 - H5前端访问"""
from datetime import datetime, timezone
from hashlib import sha1
import json
import time
from urllib.parse import urlencode
from urllib.request import urlopen
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Site, Module, SiteAccount, AccessLog, ModuleClickLog, AccountModulePermission, SystemConfig
from app.models import FormSubmission, CheckinConfig, CheckinRecord, CheckinSession
from app.utils.security import verify_password, create_access_token
from app.utils.deps import get_optional_frontend_account
from app.utils.checkin_code import generate_checkin_code
from app.schemas.auth import FrontendLoginRequest, TokenResponse
from app.schemas.module import ModuleOut
from pydantic import BaseModel

router = APIRouter(prefix="/p", tags=["公开接口"])


def _utcnow() -> datetime:
    """获取当前UTC时间(naive, 与MySQL DateTime列返回值一致)"""
    return datetime.now(timezone.utc).replace(tzinfo=None)


def _now() -> datetime:
    """获取当前本地时间(naive, 与前端日期选择器存储的本地时间一致)"""
    return datetime.now()


class AccessRequest(BaseModel):
    ip: str | None = None


class ClickRequest(BaseModel):
    module_id: int


def _get_wechat_access_token(app_id: str, app_secret: str) -> str:
    params = urlencode({"grant_type": "client_credential", "appid": app_id, "secret": app_secret})
    with urlopen(f"https://api.weixin.qq.com/cgi-bin/token?{params}", timeout=8) as response:
        payload = json.loads(response.read().decode("utf-8"))
    token = payload.get("access_token")
    if not token:
        errcode = payload.get("errcode", "unknown")
        errmsg = payload.get("errmsg", "unknown")
        raise HTTPException(status_code=502, detail=f"获取微信 access_token 失败: errcode={errcode}, errmsg={errmsg}")
    return token


def _get_wechat_ticket(access_token: str) -> str:
    with urlopen(f"https://api.weixin.qq.com/cgi-bin/ticket/getticket?access_token={access_token}&type=jsapi", timeout=8) as response:
        payload = json.loads(response.read().decode("utf-8"))
    ticket = payload.get("ticket")
    if not ticket:
        errcode = payload.get("errcode", "unknown")
        errmsg = payload.get("errmsg", "unknown")
        raise HTTPException(status_code=502, detail=f"获取微信 JSAPI ticket 失败: errcode={errcode}, errmsg={errmsg}")
    return ticket


def _service_config(site: Site) -> dict:
    """将客服配置 JSON 安全转换为公开配置。"""
    if not site.customer_service_config:
        return {}
    try:
        return json.loads(site.customer_service_config)
    except (TypeError, json.JSONDecodeError):
        return {}


def _title_config(site: Site) -> dict | None:
    """将数据库中的微站标题配置 JSON 安全转换为字典。"""
    if not site.title_config:
        return None
    try:
        return json.loads(site.title_config)
    except (TypeError, json.JSONDecodeError):
        return None


def _login_fields_config(site: Site) -> list[dict]:
    """将登录字段配置 JSON 安全转换为公开配置。"""
    if not site.login_fields_config:
        return [{"key": "username", "display_name": "账号", "type": "text"}]
    try:
        return json.loads(site.login_fields_config)
    except (TypeError, json.JSONDecodeError):
        return [{"key": "username", "display_name": "账号", "type": "text"}]


def _login_form_config(site: Site) -> dict:
    """将登录表单配置 JSON 安全转换为公开配置。"""
    if not site.login_form_config:
        return {"position": "center"}
    try:
        return json.loads(site.login_form_config)
    except (TypeError, json.JSONDecodeError):
        return {"position": "center"}


def _check_site_status(site: Site) -> None:
    """检查微站时间状态"""
    now = _now()
    if site.status == "offline":
        raise HTTPException(status_code=403, detail=site.close_message or "微站已关闭")
    if site.start_time and now < site.start_time:
        raise HTTPException(status_code=403, detail="微站尚未开启")
    if site.end_time and now > site.end_time:
        raise HTTPException(status_code=403, detail=site.close_message or "微站已关闭")


@router.get("/runtime-config")
def get_runtime_config(db: Session = Depends(get_db)):
    """H5 运行时公开配置，仅返回可公开的访问域名。"""
    config = db.query(SystemConfig).filter(SystemConfig.id == 1).first()
    return {"h5_domain": (config.h5_domain or "").rstrip("/") if config else ""}


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
        "title_config": _title_config(site),
        "background_color": site.background_color,
        "background_image": site.background_image,
        "share_image": site.share_image or site.kv_image,
        "share_title": site.share_title or site.name,
        "share_subtitle": site.share_subtitle or "",
        "customer_service_config": _service_config(site),
        "login_fields_config": _login_fields_config(site),
        "login_form_config": _login_form_config(site),
        "grid_offset_y": site.grid_offset_y,
        "need_login": site.need_login,
        "login_require_password": site.login_require_password,
        "need_checkin": site.need_checkin,
        "start_time": site.start_time,
        "end_time": site.end_time,
        "close_message": site.close_message,
    }


@router.get("/sites/{code}/wechat-signature")
def get_wechat_signature(
    code: str,
    url: str,
    db: Session = Depends(get_db),
):
    """为已上线微站生成微信 JS-SDK 签名，不暴露全局密钥。"""
    site = db.query(Site).filter(Site.code == code, Site.status == "online").first()
    if not site:
        raise HTTPException(status_code=404, detail="微站不存在或未上线")
    _check_site_status(site)
    config = db.query(SystemConfig).filter(SystemConfig.id == 1).first()
    if not config or not config.wechat_share_enabled:
        return {"enabled": False}
    if not config.wechat_app_id or not config.wechat_app_secret:
        raise HTTPException(status_code=409, detail="微信分享参数未完整配置")
    try:
        access_token = _get_wechat_access_token(config.wechat_app_id, config.wechat_app_secret)
        ticket = _get_wechat_ticket(access_token)
        timestamp = int(time.time())
        nonce_str = sha1(f"{timestamp}-{code}".encode("utf-8")).hexdigest()[:16]
        raw = f"jsapi_ticket={ticket}&noncestr={nonce_str}&timestamp={timestamp}&url={url.split('#')[0]}"
        signature = sha1(raw.encode("utf-8")).hexdigest()
        return {
            "enabled": True,
            "app_id": config.wechat_app_id,
            "timestamp": timestamp,
            "nonce_str": nonce_str,
            "signature": signature,
        }
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"微信分享签名失败: {str(exc)}")


@router.get("/sites/{code}/session")
def get_frontend_session(
    code: str,
    db: Session = Depends(get_db),
    account: SiteAccount | None = Depends(get_optional_frontend_account),
):
    """H5 - 校验当前微站的前端登录状态。"""
    site = db.query(Site).filter(Site.code == code, Site.status == "online").first()
    if not site:
        raise HTTPException(status_code=404, detail="微站不存在或未上线")
    _check_site_status(site)
    if not site.need_login:
        return {"need_login": False, "authenticated": True}
    if not account or account.site_id != site.id:
        raise HTTPException(status_code=401, detail="请先登录")
    return {"need_login": True, "authenticated": True, "nickname": account.nickname or account.username}


@router.get("/sites/{code}/account/profile")
def get_account_profile(
    code: str,
    db: Session = Depends(get_db),
    account: SiteAccount | None = Depends(get_optional_frontend_account),
):
    """H5 - 获取当前登录用户的个人信息，用于二维码签到展示"""
    site = db.query(Site).filter(Site.code == code, Site.status == "online").first()
    if not site:
        raise HTTPException(status_code=404, detail="微站不存在或未上线")
    _check_site_status(site)
    if not account or account.site_id != site.id:
        raise HTTPException(status_code=401, detail="请先登录")
    return {
        "username": account.username,
        "phone": account.phone or "",
        "nickname": account.nickname or account.username,
    }


@router.post("/sites/{code}/login", response_model=TokenResponse)
def login_frontend(
    code: str,
    req: FrontendLoginRequest,
    db: Session = Depends(get_db),
):
    """H5 - 前端用户登录，支持多字段登录"""
    site = db.query(Site).filter(Site.code == code).first()
    if not site:
        raise HTTPException(status_code=404, detail="微站不存在")
    _check_site_status(site)

    # 收集提交的登录字段值
    submitted: dict[str, str] = {}
    if req.login_fields:
        submitted = {k: v for k, v in req.login_fields.items() if v and v.strip()}
    if not submitted:
        submitted["username"] = req.username  # 兼容旧前端

    # 确定登录字段列表
    login_fields: list[dict] = []
    if site.login_fields_config:
        try:
            login_fields = json.loads(site.login_fields_config)
        except (TypeError, json.JSONDecodeError):
            pass
    if not login_fields:
        login_fields = [{"key": "username", "display_name": "账号", "type": "text"}]

    # 查询该微站下所有有效账号
    candidates = db.query(SiteAccount).filter(
        SiteAccount.site_id == site.id,
        SiteAccount.is_active == True,
    ).all()

    # 逐步过滤：每个登录字段都必须匹配同一个账号
    acc = None
    for field_conf in login_fields:
        field_key = field_conf.get("key", "")
        value = submitted.get(field_key, "").strip()
        if not value:
            continue  # 该字段未提交，跳过

        next_candidates = []
        for a in candidates:
            if field_key == "username":
                if a.username == value:
                    next_candidates.append(a)
            elif field_key == "phone":
                if a.phone == value:
                    next_candidates.append(a)
            else:
                # 自定义字段：在 custom_fields JSON 中查找
                custom_key = field_conf.get("custom_key") or field_key
                if a.custom_fields:
                    try:
                        cf = json.loads(a.custom_fields)
                        if cf.get(custom_key) == value:
                            next_candidates.append(a)
                    except (TypeError, json.JSONDecodeError):
                        pass
        candidates = next_candidates
        if not candidates:
            break

    if len(candidates) == 1:
        acc = candidates[0]
    elif not candidates:
        raise HTTPException(status_code=401, detail="账号或密码错误")
    else:
        raise HTTPException(status_code=401, detail="账号信息存在多账号匹配，请联系管理员")

    # 无密码模式: 站点配置 login_require_password=False 时不校验密码
    if site.login_require_password and not verify_password(req.password, acc.password_hash):
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
    now = _now()
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
            position_x=m.position_x,
            position_y=m.position_y,
            width=m.width,
            height=m.height,
            border_radius=m.border_radius,
            bg_color=m.bg_color,
            font_color=m.font_color,
            icon_position=m.icon_position,
            content_align=m.content_align,
            show_arrow=m.show_arrow,
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
    now = _now()
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
        "form_config": module.form_config,
        "schedule_config": module.schedule_config,
        "qrcode_config": module.qrcode_config,
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
        visit_date=_utcnow().date(),
        visit_time=_utcnow(),
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
        click_date=_utcnow().date(),
        click_time=_utcnow(),
    )
    db.add(log)
    db.commit()
    return {"message": "ok"}


# ============================================================
# 签到（H5 端）— 多场次
# ============================================================
def _checkin_status_of(db: Session, site: Site, account: SiteAccount | None) -> dict:
    """计算当前用户在该微站的签到状态（多场次）

    返回字段: need_checkin / registered / sessions / all_checked_in / status
    sessions: [{id, name, start_at, end_at, enabled, status}]
    status: disabled 未开启 | not_registered 未报名 | no_sessions 无场次
          | done 全部场次已签到 | pending 有场次待签到 | no_right 无权限
    """
    if not site.need_checkin:
        return {"need_checkin": False, "registered": False, "sessions": [],
                "all_checked_in": False, "status": "disabled"}

    registered = False
    if account:
        registered = db.query(FormSubmission).filter(
            FormSubmission.site_id == site.id,
            FormSubmission.account_id == account.id,
        ).first() is not None

    if not account:
        status = "no_right"
    elif not registered:
        status = "not_registered"
    else:
        status = "pending"  # 先给默认值，后续根据场次状态修正

    # 查询场次
    sessions_db = db.query(CheckinSession).filter(
        CheckinSession.site_id == site.id
    ).order_by(CheckinSession.sort_order, CheckinSession.id).all()

    sessions_out = []
    all_done = True
    has_pending = False

    for s in sessions_db:
        # 查该用户在该场次的签到记录
        record = None
        if account:
            record = db.query(CheckinRecord).filter(
                CheckinRecord.site_id == site.id,
                CheckinRecord.account_id == account.id,
                CheckinRecord.session_id == s.id,
                CheckinRecord.checkin_status == True,  # noqa: E712
            ).first()

        if record:
            s_status = "done"
        elif not s.enabled:
            s_status = "disabled"
        elif s.start_at and _now() < s.start_at:
            s_status = "not_started"
        elif s.end_at and _now() > s.end_at:
            s_status = "ended"
        else:
            s_status = "pending"
            has_pending = True

        if s_status != "done":
            all_done = False

        sessions_out.append({
            "id": s.id,
            "name": s.name,
            "start_at": s.start_at,
            "end_at": s.end_at,
            "enabled": s.enabled,
            "status": s_status,
            "checkin_at": record.checkin_at if record else None,
        })

    # 修正整体状态
    if account and registered:
        if not sessions_out:
            status = "no_sessions"
        elif all_done:
            status = "done"
        elif has_pending:
            status = "pending"
        else:
            status = "done"  # 所有场次非 pending 且全 done

    return {
        "need_checkin": site.need_checkin,
        "registered": registered,
        "sessions": sessions_out,
        "all_checked_in": all_done,
        "status": status,
    }


@router.get("/sites/{code}/checkin/status")
def get_checkin_status(
    code: str,
    db: Session = Depends(get_db),
    account: SiteAccount | None = Depends(get_optional_frontend_account),
):
    """H5 - 查询当前登录用户的签到状态（含各场次状态）"""
    site = db.query(Site).filter(Site.code == code, Site.status == "online").first()
    if not site:
        raise HTTPException(status_code=404, detail="微站不存在或未上线")
    _check_site_status(site)
    if not site.need_login:
        raise HTTPException(status_code=400, detail="该微站未开启签到")
    if not account:
        raise HTTPException(status_code=401, detail="请先登录")
    return _checkin_status_of(db, site, account)


@router.get("/sites/{code}/checkin/qrcode")
def get_checkin_qrcode(
    code: str,
    db: Session = Depends(get_db),
    account: SiteAccount | None = Depends(get_optional_frontend_account),
):
    """H5 - 获取静态签到二维码内容（同一用户同一微站恒定，不含明文敏感信息）

    多场次模式下二维码内容不变（仍为 site+account），操作人在后台选择场次核销。
    仅当存在待签到场次时返回二维码。"""
    site = db.query(Site).filter(Site.code == code, Site.status == "online").first()
    if not site:
        raise HTTPException(status_code=404, detail="微站不存在或未上线")
    _check_site_status(site)
    if not site.need_login:
        raise HTTPException(status_code=400, detail="该微站未开启签到")
    if not account:
        raise HTTPException(status_code=401, detail="请先登录")

    info = _checkin_status_of(db, site, account)
    if info["status"] != "pending":
        return {"code": None, **info}
    return {
        "code": generate_checkin_code(site.id, account.id),
        **info,
    }
