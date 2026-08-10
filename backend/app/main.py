"""FastAPI 应用入口"""
import logging
import traceback
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os

from app.config import settings
from app.database import engine, Base, SessionLocal
from app.models import User, SystemConfig
from app.utils.security import hash_password
from app.routers import auth, sites, modules, accounts, upload, stats, public, form_submissions, system_config, checkin

# 配置日志
logging.basicConfig(level=logging.DEBUG if settings.DEBUG else logging.INFO)
logger = logging.getLogger(__name__)


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

            # 创建默认管理员
            admin = db.query(User).filter(User.username == "admin").first()
            if not admin:
                admin = User(
                    username="admin",
                    password_hash=hash_password("admin123"),
                    nickname="超级管理员",
                    role="super_admin",
                )
                db.add(admin)
                db.commit()
                logger.info("[INFO] 默认管理员已创建: admin / admin123")
        finally:
            db.close()
        logger.info("[INFO] 数据库连接成功，所有表已就绪")
    except Exception as e:
        logger.error(f"[ERROR] 数据库连接失败，请检查 MySQL 服务和 .env 配置")
        logger.error(f"[ERROR] 错误详情: {e}")
        logger.error(f"[ERROR] 堆栈: {traceback.format_exc()}")
        logger.warning("[WARNING] 服务仍将启动，但所有数据库操作将失败！")

    yield


app = FastAPI(
    title=settings.APP_NAME,
    description="微站系统后端API",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs" if settings.DEBUG else None,
    redoc_url="/redoc" if settings.DEBUG else None,
)

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
