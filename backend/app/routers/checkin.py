"""签到管理路由（后台顶级模块：签到管理）

支持多场次：一个微站可配置多场签到，每场有独立时间窗。
扫码核销时操作人选择场次，系统按 (site, account, session) 幂等。"""
import csv
import io
import logging
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import Response
from sqlalchemy.orm import Session
from sqlalchemy import func
from sqlalchemy.exc import IntegrityError

from app.database import get_db
from app.models import User, Site, SiteAccount, FormSubmission, CheckinConfig, CheckinRecord, CheckinSession
from app.utils.deps import get_current_admin, assert_site_access, ROLE_SUPER_ADMIN, ROLE_ADMIN
from app.utils.checkin_code import parse_checkin_code
from app.schemas.checkin import (
    CheckinConfigUpdate, ScanCheckinRequest, ManualCheckinRequest, RevokeCheckinRequest,
    SessionCreate, SessionUpdate,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/checkin", tags=["签到管理"])


def _utcnow() -> datetime:
    from datetime import timezone
    return datetime.now(timezone.utc).replace(tzinfo=None)


def _now() -> datetime:
    """本地时间(naive)，与前端时间选择器存储的本地时间一致"""
    return datetime.now()


def _get_site(db: Session, site_id: int) -> Site:
    site = db.query(Site).filter(Site.id == site_id).first()
    if not site:
        raise HTTPException(status_code=404, detail="微站不存在")
    return site


def _get_config(db: Session, site_id: int) -> CheckinConfig:
    config = db.query(CheckinConfig).filter(CheckinConfig.site_id == site_id).first()
    if not config:
        config = CheckinConfig(site_id=site_id)
        db.add(config)
        db.commit()
        db.refresh(config)
    return config


def _get_sessions(db: Session, site_id: int) -> list[CheckinSession]:
    return db.query(CheckinSession).filter(
        CheckinSession.site_id == site_id
    ).order_by(CheckinSession.sort_order, CheckinSession.id).all()


def _get_session(db: Session, session_id: int) -> CheckinSession | None:
    return db.query(CheckinSession).filter(CheckinSession.id == session_id).first()


def _mask_phone(phone: str | None) -> str:
    if not phone:
        return "-"
    if len(phone) >= 7:
        return phone[:3] + "****" + phone[-4:]
    return phone


def _can_manage(current: User) -> bool:
    """配置/补签/撤销/导出需要 admin 及以上权限"""
    return current.role in (ROLE_SUPER_ADMIN, ROLE_ADMIN)


def _is_registered(db: Session, site_id: int, account_id: int) -> bool:
    """用户是否已报名（该微站下存在任一报名记录）"""
    return db.query(FormSubmission).filter(
        FormSubmission.site_id == site_id,
        FormSubmission.account_id == account_id,
    ).first() is not None


def _session_window(session: CheckinSession) -> tuple[bool, str]:
    """校验场次签到时间窗。返回 (是否可签到, 拒绝原因或空串)"""
    if not session.enabled:
        return False, "该场次已停用"
    now = _now()
    if session.start_at and now < session.start_at:
        return False, f"「{session.name}」签到尚未开始"
    if session.end_at and now > session.end_at:
        return False, f"「{session.name}」签到已结束"
    return True, ""


# ---------------------------------------------------------------
# 签到管理列表
# ---------------------------------------------------------------
@router.get("/projects")
def list_checkin_projects(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    keyword: str | None = None,
    db: Session = Depends(get_db),
    current: User = Depends(get_current_admin),
):
    """签到管理列表：展示微站管理中开启签到的项目（need_checkin=true）"""
    q = db.query(Site).filter(Site.need_checkin == True)  # noqa: E712
    if current.role != ROLE_SUPER_ADMIN:
        q = q.filter(Site.created_by == current.id)
    if keyword:
        q = q.filter(Site.name.like(f"%{keyword}%"))
    total = q.count()
    sites = q.order_by(Site.updated_at.desc()).offset((page - 1) * page_size).limit(page_size).all()

    items = []
    for s in sites:
        session_count = db.query(CheckinSession).filter(
            CheckinSession.site_id == s.id,
        ).count()
        reg_count = db.query(FormSubmission).filter(
            FormSubmission.site_id == s.id,
        ).with_entities(FormSubmission.account_id.distinct()).count()
        checked_count = db.query(CheckinRecord).filter(
            CheckinRecord.site_id == s.id,
            CheckinRecord.checkin_status == True,  # noqa: E712
        ).count()
        items.append({
            "id": s.id,
            "name": s.name,
            "code": s.code,
            "status": s.status,
            "checkin_enabled": s.need_checkin,
            "session_count": session_count,
            "registered_count": reg_count,
            "checked_in_count": checked_count,
            "updated_at": s.updated_at,
        })
    return {"total": total, "page": page, "page_size": page_size, "items": items}


# ---------------------------------------------------------------
# 签到配置（站点级，保留兼容）
# ---------------------------------------------------------------
@router.get("/projects/{site_id}/config")
def get_checkin_config(
    site_id: int,
    db: Session = Depends(get_db),
    current: User = Depends(get_current_admin),
):
    """查询项目签到配置"""
    site = _get_site(db, site_id)
    assert_site_access(site, current)
    sessions = _get_sessions(db, site_id)
    return {
        "site_id": site.id,
        "name": site.name,
        "checkin_enabled": site.need_checkin,
        "sessions": [{
            "id": s.id,
            "name": s.name,
            "start_at": s.start_at,
            "end_at": s.end_at,
            "enabled": s.enabled,
            "sort_order": s.sort_order,
        } for s in sessions],
    }


@router.put("/projects/{site_id}/config")
def update_checkin_config(
    site_id: int,
    req: CheckinConfigUpdate,
    db: Session = Depends(get_db),
    current: User = Depends(get_current_admin),
):
    """保存项目签到配置（兼容旧接口，时间窗已迁移至场次）"""
    if not _can_manage(current):
        raise HTTPException(status_code=403, detail="无权限进行签到配置")
    site = _get_site(db, site_id)
    assert_site_access(site, current)
    config = _get_config(db, site_id)
    config.updated_by = current.id
    db.commit()
    return {"site_id": site.id, "checkin_enabled": site.need_checkin}


# ---------------------------------------------------------------
# 场次管理 CRUD
# ---------------------------------------------------------------
@router.get("/projects/{site_id}/sessions")
def list_sessions(
    site_id: int,
    db: Session = Depends(get_db),
    current: User = Depends(get_current_admin),
):
    """查询项目下所有签到场次"""
    site = _get_site(db, site_id)
    assert_site_access(site, current)
    sessions = _get_sessions(db, site_id)
    result = []
    for s in sessions:
        checked = db.query(CheckinRecord).filter(
            CheckinRecord.session_id == s.id,
            CheckinRecord.checkin_status == True,  # noqa: E712
        ).count()
        result.append({
            "id": s.id,
            "name": s.name,
            "start_at": s.start_at,
            "end_at": s.end_at,
            "enabled": s.enabled,
            "sort_order": s.sort_order,
            "checked_in_count": checked,
        })
    return {"items": result}


@router.post("/projects/{site_id}/sessions")
def create_session(
    site_id: int,
    req: SessionCreate,
    db: Session = Depends(get_db),
    current: User = Depends(get_current_admin),
):
    """创建签到场次"""
    if not _can_manage(current):
        raise HTTPException(status_code=403, detail="无权限创建场次")
    site = _get_site(db, site_id)
    assert_site_access(site, current)
    if req.start_at and req.end_at and req.start_at >= req.end_at:
        raise HTTPException(status_code=400, detail="签到开始时间必须早于结束时间")
    session = CheckinSession(
        site_id=site_id,
        name=req.name,
        start_at=req.start_at,
        end_at=req.end_at,
        enabled=req.enabled,
        sort_order=req.sort_order,
        updated_by=current.id,
    )
    db.add(session)
    db.commit()
    db.refresh(session)
    # 商业化(v1.2): 创建场次不再扣减额度，扣减时机改为「微站上线」(见 sites.py /status)
    return {
        "id": session.id,
        "name": session.name,
        "start_at": session.start_at,
        "end_at": session.end_at,
        "enabled": session.enabled,
        "sort_order": session.sort_order,
    }


@router.put("/sessions/{session_id}")
def update_session(
    session_id: int,
    req: SessionUpdate,
    db: Session = Depends(get_db),
    current: User = Depends(get_current_admin),
):
    """更新签到场次"""
    if not _can_manage(current):
        raise HTTPException(status_code=403, detail="无权限修改场次")
    session = _get_session(db, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="场次不存在")
    site = _get_site(db, session.site_id)
    assert_site_access(site, current)
    if req.name is not None:
        session.name = req.name
    if req.start_at is not None:
        session.start_at = req.start_at
    if req.end_at is not None:
        session.end_at = req.end_at
    if req.enabled is not None:
        session.enabled = req.enabled
    if req.sort_order is not None:
        session.sort_order = req.sort_order
    session.updated_by = current.id
    if session.start_at and session.end_at and session.start_at >= session.end_at:
        raise HTTPException(status_code=400, detail="签到开始时间必须早于结束时间")
    db.commit()
    db.refresh(session)
    return {
        "id": session.id,
        "name": session.name,
        "start_at": session.start_at,
        "end_at": session.end_at,
        "enabled": session.enabled,
        "sort_order": session.sort_order,
    }


@router.delete("/sessions/{session_id}")
def delete_session(
    session_id: int,
    db: Session = Depends(get_db),
    current: User = Depends(get_current_admin),
):
    """删除签到场次（已有签到记录的场次不允许删除）"""
    if not _can_manage(current):
        raise HTTPException(status_code=403, detail="无权限删除场次")
    session = _get_session(db, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="场次不存在")
    site = _get_site(db, session.site_id)
    assert_site_access(site, current)
    record_count = db.query(CheckinRecord).filter(
        CheckinRecord.session_id == session_id,
    ).count()
    if record_count > 0:
        raise HTTPException(status_code=400, detail=f"该场次已有 {record_count} 条签到记录，无法删除。可停用该场次。")
    db.delete(session)
    db.commit()
    return {"message": "场次已删除"}


# ---------------------------------------------------------------
# 扫码核销
# ---------------------------------------------------------------
@router.post("/projects/{site_id}/scan")
def scan_checkin(
    site_id: int,
    req: ScanCheckinRequest,
    db: Session = Depends(get_db),
    current: User = Depends(get_current_admin),
):
    """扫码核销：解析静态码 -> 选择场次 -> 校验 -> 原子签到"""
    site = _get_site(db, site_id)
    assert_site_access(site, current)

    parsed = parse_checkin_code(req.code)
    if parsed is None:
        return {"result": "QRCODE_INVALID", "message": "二维码无效，请确认是否为有效签到码"}
    code_site_id, account_id = parsed
    if code_site_id != site.id:
        return {"result": "ACTIVITY_MISMATCH", "message": "非当前微站的二维码"}
    if not site.need_checkin:
        return {"result": "CHECKIN_NOT_OPEN", "message": "该微站未开启签到"}

    account = db.query(SiteAccount).filter(
        SiteAccount.id == account_id,
        SiteAccount.site_id == site.id,
    ).first()
    if not account:
        return {"result": "QRCODE_INVALID", "message": "二维码无效，账号不存在"}

    if not _is_registered(db, site.id, account.id):
        return {"result": "NOT_REGISTERED", "message": "该用户未报名，无法签到"}

    # 确定场次
    sessions = _get_sessions(db, site.id)
    if not sessions:
        return {"result": "NO_SESSION", "message": "尚未配置签到场次，请先在签到设置中添加场次"}

    if req.session_id:
        session = _get_session(db, req.session_id)
        if not session or session.site_id != site.id:
            return {"result": "NO_SESSION", "message": "场次不存在"}
    else:
        # 未指定场次：自动选取第一个启用且在时间窗内的场次
        session = None
        for s in sessions:
            if s.enabled:
                ok, _ = _session_window(s)
                if ok:
                    session = s
                    break
        if not session:
            session = sessions[0] if sessions else None
    if not session:
        return {"result": "NO_SESSION", "message": "没有可用场次"}

    # 场次时间窗校验
    ok, reason = _session_window(session)
    if not ok:
        return {"result": "CHECKIN_NOT_OPEN", "message": reason, "session_name": session.name}

    # 已签到校验（同一场次幂等）
    existing = db.query(CheckinRecord).filter(
        CheckinRecord.site_id == site.id,
        CheckinRecord.account_id == account.id,
        CheckinRecord.session_id == session.id,
        CheckinRecord.checkin_status == True,  # noqa: E712
    ).first()
    if existing:
        return {
            "result": "ALREADY_CHECKED_IN",
            "message": f"该用户在「{session.name}」已签到，签到时间 {existing.checkin_at}",
            "user_name": account.nickname or account.username,
            "mobile_masked": _mask_phone(account.phone),
            "checkin_at": existing.checkin_at,
            "session_name": session.name,
        }

    record = CheckinRecord(
        site_id=site.id,
        account_id=account.id,
        session_id=session.id,
        checkin_status=True,
        checkin_at=_utcnow(),
        checkin_method="QR_SCAN",
        operator_id=current.id,
        operator_name=current.nickname or current.username,
    )
    try:
        db.add(record)
        db.commit()
        db.refresh(record)
    except IntegrityError:
        db.rollback()
        existing = db.query(CheckinRecord).filter(
            CheckinRecord.site_id == site.id,
            CheckinRecord.account_id == account.id,
            CheckinRecord.session_id == session.id,
            CheckinRecord.checkin_status == True,  # noqa: E712
        ).first()
        return {
            "result": "ALREADY_CHECKED_IN",
            "message": f"该用户在「{session.name}」已签到",
            "user_name": account.nickname or account.username,
            "mobile_masked": _mask_phone(account.phone),
            "checkin_at": existing.checkin_at if existing else None,
            "session_name": session.name,
        }
    except Exception as e:
        db.rollback()
        logger.error(f"扫码签到失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="签到失败，请重试")

    return {
        "result": "SUCCESS",
        "message": f"「{session.name}」签到成功",
        "user_name": account.nickname or account.username,
        "mobile_masked": _mask_phone(account.phone),
        "checkin_at": record.checkin_at,
        "session_name": session.name,
        "registration_status": "registered",
    }


# ---------------------------------------------------------------
# 签到记录
# ---------------------------------------------------------------
@router.get("/projects/{site_id}/records")
def list_checkin_records(
    site_id: int,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status: int | None = Query(None, description="1有效 0已撤销"),
    method: str | None = Query(None, description="QR_SCAN/MANUAL"),
    session_id: int | None = Query(None, description="场次ID"),
    keyword: str | None = Query(None, description="姓名或手机号"),
    db: Session = Depends(get_db),
    current: User = Depends(get_current_admin),
):
    """签到记录分页查询"""
    site = _get_site(db, site_id)
    assert_site_access(site, current)

    q = db.query(CheckinRecord).filter(CheckinRecord.site_id == site_id)
    if status is not None:
        q = q.filter(CheckinRecord.checkin_status == (status == 1))
    if method:
        q = q.filter(CheckinRecord.checkin_method == method)
    if session_id is not None:
        q = q.filter(CheckinRecord.session_id == session_id)

    if keyword:
        account_ids = [
            a.id for a in db.query(SiteAccount).filter(
                SiteAccount.site_id == site_id,
                SiteAccount.is_active == True,  # noqa: E712
            ).all()
            if (a.nickname and keyword in a.nickname) or (a.phone and keyword in a.phone) or (a.username and keyword in a.username)
        ]
        q = q.filter(CheckinRecord.account_id.in_(account_ids)) if account_ids else q.filter(CheckinRecord.id == 0)

    total = q.count()
    rows = q.order_by(CheckinRecord.checkin_at.desc()).offset((page - 1) * page_size).limit(page_size).all()

    # 预加载场次名称
    session_map = {}
    if rows:
        sids = {r.session_id for r in rows if r.session_id}
        if sids:
            for s in db.query(CheckinSession).filter(CheckinSession.id.in_(sids)).all():
                session_map[s.id] = s.name

    items = []
    for r in rows:
        account = db.query(SiteAccount).filter(SiteAccount.id == r.account_id).first()
        items.append({
            "id": r.id,
            "account_id": r.account_id,
            "user_name": (account.nickname or account.username) if account else "-",
            "mobile_masked": _mask_phone(account.phone if account else None),
            "session_name": session_map.get(r.session_id, "-") if r.session_id else "-",
            "checkin_status": r.checkin_status,
            "checkin_at": r.checkin_at,
            "checkin_method": r.checkin_method,
            "operator_name": r.operator_name or "-",
            "remark": r.remark,
        })
    return {"total": total, "page": page, "page_size": page_size, "items": items}


# ---------------------------------------------------------------
# 人工补签 / 撤销
# ---------------------------------------------------------------
@router.post("/projects/{site_id}/manual")
def manual_checkin(
    site_id: int,
    req: ManualCheckinRequest,
    db: Session = Depends(get_db),
    current: User = Depends(get_current_admin),
):
    """管理员人工补签"""
    if not _can_manage(current):
        raise HTTPException(status_code=403, detail="无权限进行人工补签")
    site = _get_site(db, site_id)
    assert_site_access(site, current)

    account = db.query(SiteAccount).filter(
        SiteAccount.id == req.account_id,
        SiteAccount.site_id == site.id,
    ).first()
    if not account:
        raise HTTPException(status_code=404, detail="账号不存在")

    # 确定场次
    sessions = _get_sessions(db, site.id)
    if not sessions:
        raise HTTPException(status_code=400, detail="尚未配置签到场次")

    if req.session_id:
        session = _get_session(db, req.session_id)
        if not session or session.site_id != site.id:
            raise HTTPException(status_code=404, detail="场次不存在")
    else:
        session = sessions[0]

    existing = db.query(CheckinRecord).filter(
        CheckinRecord.site_id == site.id,
        CheckinRecord.account_id == account.id,
        CheckinRecord.session_id == session.id,
        CheckinRecord.checkin_status == True,  # noqa: E712
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail=f"该用户在「{session.name}」已签到，签到时间 {existing.checkin_at}")

    record = CheckinRecord(
        site_id=site.id,
        account_id=account.id,
        session_id=session.id,
        checkin_status=True,
        checkin_at=_utcnow(),
        checkin_method="MANUAL",
        operator_id=current.id,
        operator_name=current.nickname or current.username,
        remark=req.remark,
    )
    try:
        db.add(record)
        db.commit()
        db.refresh(record)
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail=f"该用户在「{session.name}」已签到")
    except Exception as e:
        db.rollback()
        logger.error(f"人工补签失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="补签失败，请重试")
    return {"message": f"「{session.name}」补签成功", "id": record.id, "checkin_at": record.checkin_at, "session_name": session.name}


@router.post("/records/{record_id}/revoke")
def revoke_checkin(
    record_id: int,
    req: RevokeCheckinRequest,
    db: Session = Depends(get_db),
    current: User = Depends(get_current_admin),
):
    """管理员撤销签到"""
    if not _can_manage(current):
        raise HTTPException(status_code=403, detail="无权限进行撤销操作")
    record = db.query(CheckinRecord).filter(CheckinRecord.id == record_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="签到记录不存在")
    site = _get_site(db, record.site_id)
    assert_site_access(site, current)

    if not record.checkin_status:
        raise HTTPException(status_code=400, detail="该记录已撤销")
    record.checkin_status = False
    record.remark = req.remark or record.remark
    try:
        db.commit()
        db.refresh(record)
    except Exception as e:
        db.rollback()
        logger.error(f"撤销签到失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="撤销失败，请重试")
    return {"message": "已撤销", "id": record.id}


# ---------------------------------------------------------------
# 导出
# ---------------------------------------------------------------
@router.post("/projects/{site_id}/export")
def export_checkin_records(
    site_id: int,
    session_id: int | None = None,
    db: Session = Depends(get_db),
    current: User = Depends(get_current_admin),
):
    """导出签到记录 CSV（手机号脱敏）"""
    if not _can_manage(current):
        raise HTTPException(status_code=403, detail="无权限导出数据")
    site = _get_site(db, site_id)
    assert_site_access(site, current)

    q = db.query(CheckinRecord).filter(CheckinRecord.site_id == site_id)
    if session_id is not None:
        q = q.filter(CheckinRecord.session_id == session_id)
    rows = q.order_by(CheckinRecord.checkin_at.desc()).all()

    # 预加载场次名称
    session_map = {}
    sids = {r.session_id for r in rows if r.session_id}
    if sids:
        for s in db.query(CheckinSession).filter(CheckinSession.id.in_(sids)).all():
            session_map[s.id] = s.name

    buffer = io.StringIO()
    buffer.write("\ufeff")  # BOM for Excel
    writer = csv.writer(buffer)
    writer.writerow(["姓名", "手机号", "场次", "签到状态", "签到时间", "签到方式", "操作人", "备注"])
    for r in rows:
        account = db.query(SiteAccount).filter(SiteAccount.id == r.account_id).first()
        writer.writerow([
            (account.nickname or account.username) if account else "-",
            _mask_phone(account.phone if account else None),
            session_map.get(r.session_id, "-") if r.session_id else "-",
            "已签到" if r.checkin_status else "已撤销",
            r.checkin_at.strftime("%Y-%m-%d %H:%M:%S") if r.checkin_at else "",
            "扫码签到" if r.checkin_method == "QR_SCAN" else "人工补签",
            r.operator_name or "-",
            r.remark or "",
        ])
    csv_data = buffer.getvalue()

    import urllib.parse
    filename = urllib.parse.quote(f"签到记录_{site.name}.csv")
    return Response(
        content=csv_data,
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": f"attachment; filename*=UTF-8''{filename}"},
    )
