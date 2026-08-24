"""FastAPI 应用入口"""
import asyncio
import logging
import traceback
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
import os

from app.config import settings
from app.database import engine, Base, SessionLocal
from app.models import User, SystemConfig, MembershipPlan
from app.utils.security import hash_password
from app.routers import auth, sites, modules, accounts, upload, stats, public, form_submissions, system_config, checkin
from app.routers import billing, admin_billing
from app.routers import ai_generate
from app.routers import templates
from app.routers import distribution
from app.services import billing_service
from app.utils.rate_limit import RateLimitMiddleware

# 配置日志
logging.basicConfig(level=logging.DEBUG if settings.DEBUG else logging.INFO)
logger = logging.getLogger(__name__)


async def _billing_expiry_loop():
    """后台定时任务：会员过期检查(每小时) + 场次额度过期检查(每天)"""
    while True:
        try:
            db = SessionLocal()
            try:
                expired_members = billing_service.expire_memberships(db)
                expired_credits = billing_service.expire_credits(db)
                if expired_members or expired_credits:
                    logger.info(f"[BILLING] 过期检查: 会员 {expired_members} 个, 额度 {expired_credits} 条")
            finally:
                db.close()
        except Exception as e:
            logger.error(f"[BILLING] 过期检查任务异常: {e}", exc_info=True)
        # 每 10 分钟检查一次（额度过期检查逻辑幂等，无需严格按天）
        await asyncio.sleep(600)


def _init_default_plans(db: Session):
    """初始化默认套餐（已存在则跳过）"""
    if not db.query(MembershipPlan).filter(MembershipPlan.plan_type == "membership").first():
        db.add(MembershipPlan(
            name="年费会员", plan_type="membership", price=49900,
            duration_days=365, description="可创建和管理微站，有效期365天",
        ))
    if not db.query(MembershipPlan).filter(MembershipPlan.plan_type == "session_credit").first():
        db.add(MembershipPlan(
            name="上线场次", plan_type="session_credit", price=29900,
            credit_quantity=1, description="单次上线额度，微站每上线一次消耗1个，购买后1年内有效",
        ))
    db.commit()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期: 启动时创建表并初始化默认管理员"""
    # 创建上传目录
    upload_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), settings.UPLOAD_DIR)
    os.makedirs(upload_dir, exist_ok=True)

    # 尝试连接数据库并初始化
    try:
        # 创建所有表
        Base.metadata.create_all(bind=engine)

        # 初始化单例系统配置
        db = SessionLocal()
        try:
            if not db.query(SystemConfig).filter(SystemConfig.id == 1).first():
                db.add(SystemConfig(id=1))
                db.commit()

            # 创建默认管理员（账号密码可在 .env 中配置 ADMIN_USERNAME / ADMIN_PASSWORD）
            admin = db.query(User).filter(User.username == settings.ADMIN_USERNAME).first()
            if not admin:
                admin = User(
                    username=settings.ADMIN_USERNAME,
                    password_hash=hash_password(settings.ADMIN_PASSWORD),
                    nickname="超级管理员",
                    role="super_admin",
                )
                db.add(admin)
                db.commit()
                logger.info(f"[INFO] 默认管理员已创建: {settings.ADMIN_USERNAME} / {settings.ADMIN_PASSWORD}")

            # 初始化默认计费套餐
            _init_default_plans(db)
        finally:
            db.close()
        logger.info("[INFO] 数据库连接成功，所有表已就绪")
    except Exception as e:
        logger.error(f"[ERROR] 数据库连接失败，请检查 MySQL 服务和 .env 配置")
        logger.error(f"[ERROR] 错误详情: {e}")
        logger.error(f"[ERROR] 堆栈: {traceback.format_exc()}")
        logger.warning("[WARNING] 服务仍将启动，但所有数据库操作将失败！")

    # 启动计费过期检查后台任务
    expiry_task = asyncio.create_task(_billing_expiry_loop())

    yield

    expiry_task.cancel()


app = FastAPI(
    title=settings.APP_NAME,
    description="微站系统后端API",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs" if settings.DEBUG else None,
    redoc_url="/redoc" if settings.DEBUG else None,
)

# IP 限流中间件（先注册, 使 CORS 保持最外层, 429 响应也带跨域头）
# 中间件内部判断 settings.RATE_LIMIT_ENABLED
app.add_middleware(RateLimitMiddleware)

# CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 静态文件(本地上传)
upload_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), settings.UPLOAD_DIR)
os.makedirs(upload_dir, exist_ok=True)
app.mount("/static", StaticFiles(directory=upload_dir), name="static")

# 注册路由
api_prefix = settings.API_V1_PREFIX
app.include_router(auth.router, prefix=api_prefix)
app.include_router(sites.router, prefix=api_prefix)
app.include_router(modules.router, prefix=api_prefix)
app.include_router(accounts.router, prefix=api_prefix)
app.include_router(upload.router, prefix=api_prefix)
app.include_router(stats.router, prefix=api_prefix)
app.include_router(stats.dashboard_router, prefix=api_prefix)
app.include_router(form_submissions.router, prefix=api_prefix)
app.include_router(system_config.router, prefix=api_prefix)
app.include_router(checkin.router, prefix=api_prefix)
app.include_router(billing.router, prefix=api_prefix)
app.include_router(admin_billing.router, prefix=api_prefix)
app.include_router(ai_generate.router, prefix=api_prefix)
app.include_router(templates.router, prefix=api_prefix)
app.include_router(distribution.router, prefix=api_prefix)
# 公开接口不在/api/v1下, 直接挂在/p
app.include_router(public.router)
app.include_router(form_submissions.public_router)


@app.get("/")
def health():
    return {"status": "ok", "app": settings.APP_NAME}


# 全局异常处理：捕获未预料的数据库错误
from fastapi.responses import JSONResponse
from sqlalchemy.exc import SQLAlchemyError

@app.exception_handler(SQLAlchemyError)
async def sqlalchemy_exception_handler(request, exc: SQLAlchemyError):
    """捕获所有 SQLAlchemy 异常，返回友好的错误信息"""
    logger.error(f"数据库异常: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": f"数据库操作失败: {str(exc)}"},
    )


@app.exception_handler(Exception)
async def general_exception_handler(request, exc: Exception):
    """捕获所有未处理的异常"""
    logger.error(f"未处理异常: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": f"服务器内部错误: {str(exc)}"},
    )
