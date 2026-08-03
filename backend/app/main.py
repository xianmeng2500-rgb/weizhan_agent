"""FastAPI 应用入口"""
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os

from app.config import settings
from app.database import engine, Base, SessionLocal
from app.models import User
from app.utils.security import hash_password
from app.routers import auth, sites, modules, accounts, upload, stats, public


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

        # 创建默认管理员
        db = SessionLocal()
        try:
            admin = db.query(User).filter(User.username == "admin").first()
            if not admin:
                admin = User(
                    username="admin",
                    password_hash=hash_password("admin123"),
                    nickname="管理员",
                    role="admin",
                )
                db.add(admin)
                db.commit()
                print("[INFO] 默认管理员已创建: admin / admin123")
        finally:
            db.close()
    except Exception as e:
        print(f"[WARNING] 数据库连接失败，服务仍将启动但数据库功能不可用: {e}")

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
# 公开接口不在/api/v1下, 直接挂在/p
app.include_router(public.router)


@app.get("/")
def health():
    return {"status": "ok", "app": settings.APP_NAME}
