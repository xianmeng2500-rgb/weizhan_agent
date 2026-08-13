"""模块管理路由"""
import csv
import io
import logging
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import User, Module, Site
from app.models.stats import ModuleClickLog
from app.utils.deps import get_current_admin, assert_site_access
from app.schemas.module import (
    ModuleCreate, ModuleUpdate, ModuleOut,
    ModuleSortRequest, ModulePositionRequest,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/sites/{site_id}/modules", tags=["模块管理"])


def _get_site_or_404(db: Session, site_id: int, current: User) -> Site:
    site = db.query(Site).filter(Site.id == site_id).first()
    if not site:
        raise HTTPException(status_code=404, detail="微站不存在")
    assert_site_access(site, current)
    return site


@router.get("", response_model=list[ModuleOut])
def list_modules(
    site_id: int,
    db: Session = Depends(get_db),
    current: User = Depends(get_current_admin),
):
    """模块列表"""
    _get_site_or_404(db, site_id, current)
    modules = db.query(Module).filter(Module.site_id == site_id).order_by(Module.sort_order).all()
    return [ModuleOut.model_validate(m) for m in modules]


@router.post("", response_model=ModuleOut)
def create_module(
    site_id: int,
    req: ModuleCreate,
    db: Session = Depends(get_db),
    current: User = Depends(get_current_admin),
):
    """创建模块"""
    _get_site_or_404(db, site_id, current)
    module = Module(site_id=site_id, **req.model_dump())
    try:
        db.add(module)
        db.commit()
        db.refresh(module)
    except Exception as e:
        db.rollback()
        logger.error(f"创建模块失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"创建失败: {str(e)}")
    return ModuleOut.model_validate(module)


@router.put("/sort")
def sort_modules(
    site_id: int,
    req: ModuleSortRequest,
    db: Session = Depends(get_db),
    current: User = Depends(get_current_admin),
):
    """批量排序模块"""
    _get_site_or_404(db, site_id, current)
    try:
        for item in req.items:
            module = db.query(Module).filter(Module.id == item.module_id, Module.site_id == site_id).first()
            if module:
                module.sort_order = item.sort_order
        db.commit()
    except Exception as e:
        db.rollback()
        logger.error(f"排序模块失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"排序失败: {str(e)}")
    return {"message": "排序已更新"}


@router.put("/positions")
def update_positions(
    site_id: int,
    req: ModulePositionRequest,
    db: Session = Depends(get_db),
    current: User = Depends(get_current_admin),
):
    """批量更新模块位置(自由拖拽布局)"""
    _get_site_or_404(db, site_id, current)
    try:
        for item in req.items:
            module = db.query(Module).filter(Module.id == item.module_id, Module.site_id == site_id).first()
            if module:
                module.position_x = item.position_x
                module.position_y = item.position_y
        db.commit()
    except Exception as e:
        db.rollback()
        logger.error(f"更新模块位置失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"更新位置失败: {str(e)}")
    return {"message": "位置已更新"}


@router.get("/schedule-template")
def download_schedule_template(
    site_id: int,
    db: Session = Depends(get_db),
    current: User = Depends(get_current_admin),
):
    """下载日程安排 CSV 导入模板"""
    _get_site_or_404(db, site_id, current)
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["日期", "时间", "题目", "人员"])
    writer.writerow(["2026-08-10", "09:00-10:00", "开幕式", "张三"])
    writer.writerow(["2026-08-10", "10:30-12:00", "主题演讲", "李四、王五"])
    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue().encode("utf-8-sig")]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=schedule_template.csv"},
    )


@router.post("/{module_id}/schedule/import")
def import_schedule_csv(
    site_id: int,
    module_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current: User = Depends(get_current_admin),
):
    """从 CSV 导入日程安排数据"""
    _get_site_or_404(db, site_id, current)
    module = db.query(Module).filter(Module.id == module_id, Module.site_id == site_id).first()
    if not module:
        raise HTTPException(status_code=404, detail="模块不存在")

    try:
        content = file.file.read().decode("utf-8-sig")
    except UnicodeDecodeError:
        try:
            file.file.seek(0)
            content = file.file.read().decode("gbk")
        except Exception:
            raise HTTPException(status_code=400, detail="无法解析文件编码，请使用 UTF-8 或 GBK 编码的 CSV 文件")

    reader = csv.reader(io.StringIO(content))
    rows = list(reader)
    if len(rows) < 2:
        raise HTTPException(status_code=400, detail="CSV 文件至少需要包含表头和一行数据")

    # 跳过表头
    items = []
    for row in rows[1:]:
        if len(row) < 4:
            continue
        date_val = row[0].strip()
        time_val = row[1].strip()
        topic_val = row[2].strip()
        personnel_val = row[3].strip()
        if not date_val or not topic_val:
            continue
        items.append({
            "date": date_val,
            "time": time_val,
            "topic": topic_val,
            "personnel": personnel_val,
        })

    if not items:
        raise HTTPException(status_code=400, detail="未解析到有效的日程数据")

    # 合并模式：如果有留空日期/时间的行，继承上一行的值
    merged = []
    last_date = ""
    last_time = ""
    for item in items:
        if not item["date"]:
            item["date"] = last_date
        else:
            last_date = item["date"]
        if not item["time"]:
            item["time"] = last_time
        else:
            last_time = item["time"]
        merged.append(item)

    module.schedule_config = {"items": merged}
    try:
        db.commit()
    except Exception as e:
        db.rollback()
        logger.error(f"导入日程失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"导入失败: {str(e)}")

    return {"message": f"成功导入 {len(merged)} 条日程", "count": len(merged), "items": merged}


@router.get("/{module_id}", response_model=ModuleOut)
def get_module(
    site_id: int,
    module_id: int,
    db: Session = Depends(get_db),
    current: User = Depends(get_current_admin),
):
    """模块详情"""
    _get_site_or_404(db, site_id, current)
    module = db.query(Module).filter(Module.id == module_id, Module.site_id == site_id).first()
    if not module:
        raise HTTPException(status_code=404, detail="模块不存在")
    return ModuleOut.model_validate(module)


@router.put("/{module_id}", response_model=ModuleOut)
def update_module(
    site_id: int,
    module_id: int,
    req: ModuleUpdate,
    db: Session = Depends(get_db),
    current: User = Depends(get_current_admin),
):
    """更新模块"""
    _get_site_or_404(db, site_id, current)
    module = db.query(Module).filter(Module.id == module_id, Module.site_id == site_id).first()
    if not module:
        raise HTTPException(status_code=404, detail="模块不存在")
    for field, value in req.model_dump(exclude_unset=True).items():
        setattr(module, field, value)
    try:
        db.commit()
        db.refresh(module)
    except Exception as e:
        db.rollback()
        logger.error(f"更新模块失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"更新失败: {str(e)}")
    return ModuleOut.model_validate(module)


@router.delete("/{module_id}")
def delete_module(
    site_id: int,
    module_id: int,
    db: Session = Depends(get_db),
    current: User = Depends(get_current_admin),
):
    """删除模块"""
    _get_site_or_404(db, site_id, current)
    module = db.query(Module).filter(Module.id == module_id, Module.site_id == site_id).first()
    if not module:
        raise HTTPException(status_code=404, detail="模块不存在")
    try:
        # 先删除关联的点击日志
        db.query(ModuleClickLog).filter(ModuleClickLog.module_id == module_id).delete()
        db.delete(module)
        db.commit()
    except Exception as e:
        db.rollback()
        logger.error(f"删除模块失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"删除失败: {str(e)}")
    return {"message": "已删除"}
