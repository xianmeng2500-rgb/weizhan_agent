# 微站系统 (Weizhan)

面向移动端的轻量级内容展示平台，支持后台创建多个微站项目，配置九宫格/按钮布局，管理富文本内容和外部链接，控制开启/关闭时间，支持账号登录与模块级权限。

## 技术栈

| 层级 | 技术 |
|------|------|
| 后端 | FastAPI + SQLAlchemy + MySQL 8.0 |
| 后台前端 | Vue3 + Element Plus + wangEditor + ECharts |
| H5前端 | Vue3 + Vant |
| 图片存储 | 阿里云OSS（可降级为本地存储） |
| 部署 | Nginx + Uvicorn |

## 项目结构

```
weizhan_agent/
├── backend/           # FastAPI 后端
├── admin-frontend/    # 后台管理前端 (Vue3 + Element Plus)
├── h5-frontend/       # 移动端H5前端 (Vue3 + Vant)
├── docs/DESIGN.md     # 系统设计文档
└── nginx.conf         # Nginx 配置
```

## 快速开始

### 1. 后端

```bash
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# 编辑 .env 配置数据库、OSS等
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

默认管理员(超级管理员): `admin` / `admin123`

API文档: http://localhost:8000/docs

### 2. 后台管理前端

```bash
cd admin-frontend
npm install
npm run dev  # → http://localhost:5173/admin/
```

### 3. H5微站前端

```bash
cd h5-frontend
npm install
npm run dev  # → http://localhost:5174/
```

微站访问地址: `http://localhost:5174/s/{微站code}`

### 4. 部署

```bash
# 构建前端
cd admin-frontend && npm run build
cd h5-frontend && npm run build

# 启动后端
cd backend
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4

# 配置 Nginx (参考 nginx.conf)
# 将 admin-frontend/dist 放到 /app/admin-frontend/dist
# 将 h5-frontend/dist 放到 /app/h5-frontend/dist
```

## 核心功能

- **多微站并行**: 同时运行多个微站，每个有独立访问链接
- **布局选择**: 九宫格 / 按钮两种布局，上方KV图
- **富文本编辑**: wangEditor图文混排，图片上传OSS
- **外部链接**: 模块支持跳转到外部URL
- **时间控制**: 微站整体和各模块独立的开启/关闭时间
- **登录控制**: 可设置微站是否需要登录，后台批量导入账号；移动端登录页复用站点 KV 图与模板背景，玻璃拟态卡片 + 渐变按钮，视觉与微站主页一致
- **模块权限**: 按账号分配可访问的模块
- **容量限制**: 单个微站的需登录账号数、报名总人数均有上限（系统配置中可调整，默认各 2000）；超限时后台无法继续创建/导入账号，H5 端无法继续提交报名
- **数据统计**: PV/UV、模块点击量、访问趋势
- **模板系统**: 经典/暗黑/节日三套模板
- **后台账号分级**: 超级管理员 / 管理员 / 子账号三级权限

## 后台账号分级与权限

系统后台管理员（区别于微站前端登录账号）分为三个角色：

| 角色 | 说明 | 微站可见范围 | 账号管理权限 |
|------|------|-------------|-------------|
| `super_admin`（超级管理员） | 最高权限 | 查看**所有**微站（整体） | 可创建/编辑/禁用/删除任意角色账号（含管理员、子账号） |
| `admin`（管理员） | 中间层级 | 仅查看**自己创建**的微站 | 可创建/编辑/禁用/删除**子账号**（不能管理超级管理员和其他管理员） |
| `sub_admin`（子账号） | 受限账号 | 仅查看**自己创建**的微站 | 无账号管理权限 |

权限要点：
- 微站创建后，`created_by` 记录创建者；子账号/管理员只能看到自己创建的微站，超级管理员看全部。
- 所有微站维度的接口（微站、模块、账号、统计、报名数据）都会做归属校验，越权访问返回 403。
- 工作台首页统计对超级管理员展示全局数据，对管理员/子账号仅统计自己创建的微站。
- 被禁用的账号（is_active=false）无法登录。

> 后台账号管理页面（侧边栏"账号管理"）仅对超级管理员和管理员可见。
> 注意：此处的"账号管理"是**后台管理员账号**；微站下的"账号管理"（`sites/:id/accounts`）是微站前端登录账号（H5 用户），二者不同。
