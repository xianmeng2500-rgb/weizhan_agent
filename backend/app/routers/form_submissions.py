"""表单提交记录路由"""
import logging
from datetime import date
from typing import Any
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from sqlalchemy.exc import IntegrityError
from app.database import get_db
from app.models import User, Site, Module, SiteAccount, FormSubmission
from app.utils.deps import get_current_admin, get_optional_frontend_account, assert_site_access
from app.schemas.form_submission import FormSubmissionCreate, FormSubmissionUpdate, FormSubmissionOut

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/sites/{site_id}/modules/{module_id}/form-submissions", tags=["表单提交管理"])
public_router = APIRouter(prefix="/p", tags=["表单提交公开接口"])


def _utcnow():
    from datetime import datetime, timezone
    return datetime.now(timezone.utc).replace(tzinfo=None)


def _now():
    from datetime import datetime
    return datetime.now()


def _check_module_access(db: Session, site_id: int, module_id: int) -> Module:
    """校验模块存在且属于指定微站"""
    module = db.query(Module).filter(Module.id == module_id, Module.site_id == site_id).first()
    if not module:
        raise HTTPException(status_code=404, detail="模块不存在")
    return module


def _assert_site_access(db: Session, site_id: int, current: User) -> Site:
    """校验当前用户对该微站有访问权限"""
    site = db.query(Site).filter(Site.id == site_id).first()
    if not site:
        raise HTTPException(status_code=404, detail="微站不存在")
    assert_site_access(site, current)
    return site


@router.get("", response_model=list[FormSubmissionOut])
def list_submissions(
    site_id: int,
    module_id: int,
    submitter_name: str | None = Query(None, description="按提交者姓名模糊查询"),
    submitter_phone: str | None = Query(None, description="按手机号模糊查询"),
    start_date: date | None = Query(None, description="提交开始日期(含), 格式 YYYY-MM-DD"),
    end_date: date | None = Query(None, description="提交结束日期(含), 格式 YYYY-MM-DD"),
    db: Session = Depends(get_db),
    current: User = Depends(get_current_admin),
):
    """管理后台 - 获取某报名表单的所有提交记录(支持查询)"""
    _assert_site_access(db, site_id, current)
    _check_module_access(db, site_id, module_id)
    q = db.query(FormSubmission).filter(
        FormSubmission.site_id == site_id,
        FormSubmission.module_id == module_id,
    )
    if submitter_name:
        q = q.filter(FormSubmission.submitter_name.like(f"%{submitter_name}%"))
    if submitter_phone:
        q = q.filter(FormSubmission.submitter_phone.like(f"%{submitter_phone}%"))
    if start_date:
        q = q.filter(func.date(FormSubmission.created_at) >= start_date)
    if end_date:
        q = q.filter(func.date(FormSubmission.created_at) <= end_date)
    rows = q.order_by(FormSubmission.created_at.desc()).all()
    return [FormSubmissionOut.model_validate(r) for r in rows]


@router.get("/{submission_id}", response_model=FormSubmissionOut)
def get_submission(
    site_id: int,
    module_id: int,
    submission_id: int,
    db: Session = Depends(get_db),
    current: User = Depends(get_current_admin),
):
    """管理后台 - 提交记录详情"""
    _assert_site_access(db, site_id, current)
    row = db.query(FormSubmission).filter(
        FormSubmission.id == submission_id,
        FormSubmission.site_id == site_id,
        FormSubmission.module_id == module_id,
    ).first()
    if not row:
        raise HTTPException(status_code=404, detail="提交记录不存在")
    return FormSubmissionOut.model_validate(row)


@router.put("/{submission_id}", response_model=FormSubmissionOut)
def update_submission(
    site_id: int,
    module_id: int,
    submission_id: int,
    req: FormSubmissionUpdate,
    db: Session = Depends(get_db),
    current: User = Depends(get_current_admin),
):
    """管理后台 - 更新提交记录备注"""
    _assert_site_access(db, site_id, current)
    row = db.query(FormSubmission).filter(
        FormSubmission.id == submission_id,
        FormSubmission.site_id == site_id,
        FormSubmission.module_id == module_id,
    ).first()
    if not row:
        raise HTTPException(status_code=404, detail="提交记录不存在")
    if req.note is not None:
        row.note = req.note
    try:
        db.commit()
        db.refresh(row)
    except Exception as e:
        db.rollback()
        logger.error(f"更新提交记录失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"更新失败: {str(e)}")
    return FormSubmissionOut.model_validate(row)


@router.delete("/{submission_id}")
def delete_submission(
    site_id: int,
    module_id: int,
    submission_id: int,
    db: Session = Depends(get_db),
    current: User = Depends(get_current_admin),
):
    """管理后台 - 删除提交记录"""
    _assert_site_access(db, site_id, current)
    row = db.query(FormSubmission).filter(
        FormSubmission.id == submission_id,
        FormSubmission.site_id == site_id,
        FormSubmission.module_id == module_id,
    ).first()
    if not row:
        raise HTTPException(status_code=404, detail="提交记录不存在")
    try:
        db.delete(row)
        db.commit()
    except Exception as e:
        db.rollback()
        logger.error(f"删除提交记录失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"删除失败: {str(e)}")
    return {"message": "已删除"}


@public_router.get("/sites/{code}/modules/{module_id}/form-submissions/mine", response_model=FormSubmissionOut | None)
def get_my_public_submission(
    code: str,
    module_id: int,
    db: Session = Depends(get_db),
    account: SiteAccount | None = Depends(get_optional_frontend_account),
):
    """H5 - 获取当前登录账号的既有报名记录，仅适用于需要登录的微站。"""
    site = db.query(Site).filter(Site.code == code, Site.status == "online").first()
    if not site:
        raise HTTPException(status_code=404, detail="微站不存在")
    if not site.need_login:
        return None
    if not account:
        raise HTTPException(status_code=401, detail="请先登录")
    module = _check_module_access(db, site.id, module_id)
    if module.content_type != "registration_form":
        raise HTTPException(status_code=404, detail="模块不存在")
    row = db.query(FormSubmission).filter(
        FormSubmission.site_id == site.id,
        FormSubmission.module_id == module.id,
        FormSubmission.account_id == account.id,
    ).first()
    return FormSubmissionOut.model_validate(row) if row else None


@public_router.post("/sites/{code}/modules/{module_id}/form-submissions", response_model=FormSubmissionOut)
def create_public_submission(
    code: str,
    module_id: int,
    req: FormSubmissionCreate,
    db: Session = Depends(get_db),
    account: SiteAccount | None = Depends(get_optional_frontend_account),
):
    """H5 - 公开提交报名表单"""
    site = db.query(Site).filter(Site.code == code, Site.status == "online").first()
    if not site:
        raise HTTPException(status_code=404, detail="微站不存在")

    now = _now()
    if site.status == "offline":
        raise HTTPException(status_code=403, detail=site.close_message or "微站已关闭")
    if site.start_time and now < site.start_time:
        raise HTTPException(status_code=403, detail="微站尚未开启")
    if site.end_time and now > site.end_time:
        raise HTTPException(status_code=403, detail=site.close_message or "微站已关闭")

    module = db.query(Module).filter(
        Module.id == module_id,
        Module.site_id == site.id,
        Module.is_active == True,
        Module.content_type == "registration_form",
    ).first()
    if not module:
        raise HTTPException(status_code=404, detail="模块不存在")
    if module.start_time and now < module.start_time:
        raise HTTPException(status_code=403, detail="模块尚未开启")
    if module.end_time and now > module.end_time:
        raise HTTPException(status_code=403, detail="模块已关闭")

    # 登录校验
    if site.need_login and not account:
        raise HTTPException(status_code=401, detail="请先登录")

    # 登录微站：同一账号对同一报名表单仅允许提交一次
    if site.need_login and account:
        existing = db.query(FormSubmission).filter(
            FormSubmission.site_id == site.id,
            FormSubmission.module_id == module.id,
            FormSubmission.account_id == account.id,
        ).first()
        if existing:
            raise HTTPException(status_code=409, detail="您已提交过该报名表单，不能重复提交")

    # 权限校验
    if site.need_login and account:
        from app.models import AccountModulePermission
        permitted_ids = {
            p.module_id for p in
            db.query(AccountModulePermission).filter(
                AccountModulePermission.account_id == account.id
            ).all()
        }
        if permitted_ids and module.id not in permitted_ids:
            raise HTTPException(status_code=403, detail="无权访问此模块")

    # 基础必填校验
    config: dict[str, Any] = module.form_config or {}
    fields = config.get("fields", [])
    field_map = {f.get("id"): f for f in fields if f.get("id")}
    missing = []
    for field in fields:
        fid = field.get("id")
        if field.get("required") and fid:
            value = req.data.get(fid)
            if value is None or value == "" or value == []:
                missing.append(field.get("title", fid))
    if missing:
        raise HTTPException(status_code=422, detail=f"请填写必填项: {', '.join(missing)}")

    # 尝试自动提取姓名/手机号作为提交者信息
    submitter_name = req.submitter_name
    submitter_phone = req.submitter_phone
    for field in fields:
        fid = field.get("id")
        ftype = field.get("type")
        value = req.data.get(fid)
        if not submitter_name and ftype == "text" and "姓名" in (field.get("title") or ""):
            submitter_name = str(value) if value else None
        if not submitter_phone and ftype in ("phone", "mobile") and value:
            submitter_phone = str(value)
        if not submitter_phone and "手机号" in (field.get("title") or "") and value:
            submitter_phone = str(value)

    row = FormSubmission(
        site_id=site.id,
        module_id=module.id,
        # 未启用登录的微站不关联浏览器中可能残留的登录令牌，确保匿名报名可重复提交。
        account_id=account.id if site.need_login and account else None,
        submitter_name=submitter_name,
        submitter_phone=submitter_phone,
        data=req.data,
        created_at=_utcnow(),
    )
    try:
        db.add(row)
        db.commit()
        db.refresh(row)
    except IntegrityError as e:
        db.rollback()
        if site.need_login and account:
            raise HTTPException(status_code=409, detail="您已提交过该报名表单，不能重复提交")
        logger.error(f"保存表单提交失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="提交失败")
    except Exception as e:
        db.rollback()
        logger.error(f"保存表单提交失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"提交失败: {str(e)}")
    return FormSubmissionOut.model_validate(row)
