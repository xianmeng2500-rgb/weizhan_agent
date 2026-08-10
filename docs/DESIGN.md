# 微站系统设计文档

## 1. 系统概述

微站系统是一个面向移动端的轻量级内容展示平台，支持通过后台创建多个微站项目，配置九宫格/按钮布局，管理富文本内容和外部链接，控制开启/关闭时间，并支持账号登录与模块级权限分配。

### 核心功能

| 功能模块 | 说明 |
|---------|------|
| 微站管理 | 创建/编辑/删除微站项目，配置模板、KV图、布局、时间控制 |
| 模块管理 | 九宫格/按钮的各个格子，配置图标、标题、内容类型（富文本/外链）、时间控制 |
| 内容管理 | 富文本编辑器（wangEditor），支持图文混排，图片上传至阿里云OSS |
| 账号管理 | 后台导入登录账号，按账号分配可访问的模块 |
| 访问统计 | PV/UV统计、模块点击量统计 |
| 移动端展示 | H5页面，适配移动端，支持九宫格/按钮布局，KV展示 |

## 2. 技术栈

| 层级 | 技术选型 | 版本 |
|------|---------|------|
| 后端框架 | FastAPI (Python) | 0.110+ |
| ORM | SQLAlchemy | 2.0+ |
| 数据库 | MySQL | 8.0+ |
| 后台前端 | Vue3 + Element Plus + Vite | 3.4+ |
| 移动端前端 | Vue3 + Vant + Vite | 3.4+ |
| 富文本编辑器 | wangEditor | 5+ |
| 对象存储 | 阿里云OSS | - |
| 部署 | Nginx + Uvicorn | - |

## 3. 系统架构

```
                        ┌─────────────────────────────────┐
                        │           Nginx (80/443)         │
                        │  静态文件代理 + API反向代理       │
                        └──────┬──────────────┬──────────┘
                               │              │
                ┌──────────────┴──┐    ┌──────┴──────────┐
                │  后台管理前端     │    │  移动端H5前端    │
                │  (admin前端静态)  │    │  (h5前端静态)    │
                │  Vue3+Element    │    │  Vue3+Vant      │
                └─────────────────┘    └─────────────────┘
                               │              │
                               └──────┬───────┘
                                      │ /api/v1
                            ┌─────────┴─────────┐
                            │   FastAPI 后端      │
                            │   (Uvicorn)         │
                            ├─────────────────────┤
                            │ - 微站管理API        │
                            │ - 模块管理API        │
                            │ - 账号管理API        │
                            │ - 内容管理API        │
                            │ - 统计API            │
                            │ - 文件上传API        │
                            └──────┬──────┬──────┘
                                   │      │
                            ┌──────┴──┐ ┌┴──────────┐
                            │  MySQL  │ │ 阿里云OSS  │
                            │  8.0+   │ │ (图片存储)  │
                            └─────────┘ └───────────┘
```

## 4. 项目目录结构

```
weizhan_agent/
├── docs/                    # 设计文档
│   └── DESIGN.md
├── backend/                 # 后端 (FastAPI)
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py          # FastAPI 入口
│   │   ├── config.py        # 配置管理
│   │   ├── database.py      # 数据库连接
│   │   ├── models/          # 数据模型 (SQLAlchemy)
│   │   │   ├── __init__.py
│   │   │   ├── user.py          # 后台管理员
│   │   │   ├── site.py          # 微站
│   │   │   ├── module.py        # 模块
│   │   │   ├── content.py       # 内容
│   │   │   ├── account.py       # 登录账号
│   │   │   └── stats.py         # 统计日志
│   │   ├── schemas/         # Pydantic 模型
│   │   │   ├── __init__.py
│   │   │   ├── site.py
│   │   │   ├── module.py
│   │   │   ├── account.py
│   │   │   └── stats.py
│   │   ├── routers/         # API路由
│   │   │   ├── __init__.py
│   │   │   ├── auth.py          # 认证
│   │   │   ├── sites.py         # 微站管理
│   │   │   ├── modules.py       # 模块管理
│   │   │   ├── accounts.py      # 账号管理
│   │   │   ├── upload.py        # 文件上传
│   │   │   ├── stats.py         # 统计
│   │   │   └── public.py        # 公开接口(H5访问)
│   │   ├── services/        # 业务逻辑
│   │   │   ├── __init__.py
│   │   │   ├── site_service.py
│   │   │   ├── module_service.py
│   │   │   ├── account_service.py
│   │   │   ├── oss_service.py
│   │   │   └── stats_service.py
│   │   └── utils/           # 工具
│   │       ├── __init__.py
│   │       ├── security.py      # JWT/密码哈希
│   │       └── deps.py         # 依赖注入
│   ├── requirements.txt
│   ├── .env.example
│   └── alembic/             # 数据库迁移
├── admin-frontend/          # 后台管理前端 (Vue3 + Element Plus)
│   ├── src/
│   │   ├── views/
│   │   │   ├── Login.vue
│   │   │   ├── Dashboard.vue
│   │   │   ├── SiteList.vue
│   │   │   ├── SiteEdit.vue
│   │   │   ├── ModuleEdit.vue
│   │   │   ├── ContentEdit.vue
│   │   │   ├── AccountImport.vue
│   │   │   └── Stats.vue
│   │   ├── components/
│   │   ├── router/
│   │   ├── store/
│   │   ├── api/
│   │   └── App.vue
│   ├── package.json
│   └── vite.config.ts
├── h5-frontend/             # 移动端H5前端 (Vue3 + Vant)
│   ├── src/
│   │   ├── views/
│   │   │   ├── SiteView.vue      # 微站展示页
│   │   │   ├── ContentView.vue   # 内容页
│   │   │   └── Login.vue         # 登录页
│   │   ├── router/
│   │   ├── api/
│   │   └── App.vue
│   ├── package.json
│   └── vite.config.ts
└── nginx.conf               # Nginx配置示例
```

## 5. 数据库设计

### 5.1 ER关系

```
users (后台管理员)  ── 自引用 created_by ──> users (上级管理员)
  └─ 管理 ──> sites (微站项目)        (sites.created_by = users.id)
                ├─ 1:N ──> modules (模块)
                │            ├─ 1:1 ──> module_contents (富文本内容)
                │            └─ N:M ──> account_module_permissions (权限)
                ├─ 1:N ──> site_accounts (登录账号)
                │            └─ N:M ──> account_module_permissions (权限)
                └─ 1:N ──> access_logs (访问日志)
                             module_click_logs (模块点击日志)
```

### 5.2 表结构

#### users — 后台管理员
| 字段 | 类型 | 说明 |
|------|------|------|
| id | INT, PK, AUTO_INCREMENT | 主键 |
| username | VARCHAR(64), UNIQUE | 用户名 |
| password_hash | VARCHAR(255) | 密码哈希 |
| nickname | VARCHAR(64) | 昵称 |
| role | VARCHAR(20) | 角色: super_admin/admin/sub_admin |
| is_active | TINYINT(1) | 是否启用(禁用后无法登录) |
| created_by | INT, FK→users.id | 创建者(上级管理员，自引用) |
| created_at | DATETIME | 创建时间 |
| updated_at | DATETIME | 更新时间 |

#### sites — 微站项目
| 字段 | 类型 | 说明 |
|------|------|------|
| id | INT, PK, AUTO_INCREMENT | 主键 |
| name | VARCHAR(128) | 微站名称 |
| code | VARCHAR(64), UNIQUE | 微站唯一码(用于URL) |
| template | VARCHAR(20) | 模板: classic/dark/festive |
| layout | VARCHAR(20) | 布局: grid/button |
| kv_image | VARCHAR(500) | KV图URL |
| background_color | VARCHAR(20) | 背景色 |
| need_login | BOOLEAN | 是否需要登录 |
| start_time | DATETIME | 开启时间 |
| end_time | DATETIME | 关闭时间 |
| status | VARCHAR(20) | 状态: draft/online/offline |
| close_message | TEXT | 关闭后提示文案 |
| created_by | INT, FK→users.id | 创建者 |
| created_at | DATETIME | 创建时间 |
| updated_at | DATETIME | 更新时间 |

#### modules — 模块
| 字段 | 类型 | 说明 |
|------|------|------|
| id | INT, PK, AUTO_INCREMENT | 主键 |
| site_id | INT, FK→sites.id | 所属微站 |
| title | VARCHAR(128) | 模块标题 |
| icon | VARCHAR(500) | 图标URL |
| sort_order | INT | 排序 |
| content_type | VARCHAR(20) | 类型: rich_text/external_link |
| external_url | VARCHAR(500) | 外部链接(content_type=external_link时) |
| rich_content | LONGTEXT | 富文本HTML(content_type=rich_text时) |
| start_time | DATETIME | 模块开启时间 |
| end_time | DATETIME | 模块关闭时间 |
| is_active | BOOLEAN | 是否启用 |
| created_at | DATETIME | 创建时间 |
| updated_at | DATETIME | 更新时间 |

#### site_accounts — 登录账号
| 字段 | 类型 | 说明 |
|------|------|------|
| id | INT, PK, AUTO_INCREMENT | 主键 |
| site_id | INT, FK→sites.id | 所属微站 |
| username | VARCHAR(64) | 登录账号 |
| password_hash | VARCHAR(255) | 密码哈希 |
| nickname | VARCHAR(64) | 昵称 |
| phone | VARCHAR(20) | 手机号(可选) |
| is_active | BOOLEAN | 是否启用 |
| created_at | DATETIME | 创建时间 |
| updated_at | DATETIME | 更新时间 |

**唯一约束**: (site_id, username) 联合唯一

#### account_module_permissions — 账号-模块权限
| 字段 | 类型 | 说明 |
|------|------|------|
| id | INT, PK, AUTO_INCREMENT | 主键 |
| account_id | INT, FK→site_accounts.id | 账号ID |
| module_id | INT, FK→modules.id | 模块ID |

#### access_logs — 访问日志
| 字段 | 类型 | 说明 |
|------|------|------|
| id | BIGINT, PK, AUTO_INCREMENT | 主键 |
| site_id | INT, FK→sites.id | 微站ID |
| account_id | INT, NULL | 登录账号ID(未登录为空) |
| ip | VARCHAR(64) | IP地址 |
| user_agent | VARCHAR(500) | User-Agent |
| visit_date | DATE | 访问日期 |
| visit_time | DATETIME | 访问时间 |

#### module_click_logs — 模块点击日志
| 字段 | 类型 | 说明 |
|------|------|------|
| id | BIGINT, PK, AUTO_INCREMENT | 主键 |
| site_id | INT, FK→sites.id | 微站ID |
| module_id | INT, FK→modules.id | 模块ID |
| account_id | INT, NULL | 账号ID |
| click_date | DATE | 点击日期 |
| click_time | DATETIME | 点击时间 |

## 6. 权限模型 (后台管理员)

后台管理员(`users` 表)分三级，通过 `role` 字段区分：

| 角色 | 微站可见范围 | 账号管理 | 说明 |
|------|-------------|---------|------|
| `super_admin` | 所有微站 | 可管理任意角色账号 | 最高权限，默认初始账号 `admin` 即此角色 |
| `admin` | 仅自己创建的微站(`created_by=自己`) | 仅可管理自己创建的 `sub_admin` | 中间层级 |
| `sub_admin` | 仅自己创建的微站 | 无 | 受限账号 |

控制逻辑：
- **微站隔离**：`sites.created_by` 记录创建者。列表接口对非超级管理员按 `created_by` 过滤；详情/编辑/删除/上下线及所有子资源（模块、账号、统计、报名数据）均调用 `assert_site_access` 校验归属，越权返回 403。
- **账号管理隔离**：超级管理员可见并管理全部账号；管理员仅可见并管理 `created_by=自己` 且 `role=sub_admin` 的账号，且只能创建 `sub_admin`；子账号无入口。
- **状态控制**：`is_active=false` 的账号无法登录（登录与 `get_current_admin` 双重拦截）。
- **防误删**：不能删除/禁用当前登录账号，不能删除超级管理员。

> 注意区分：后台管理员账号(`users`) 与 微站前端登录账号(`site_accounts`) 是两套独立体系。

## 7. API设计

### 基础路径: `/api/v1`

### 7.1 认证与账号管理 (后台)
| 方法 | 路径 | 说明 |
|------|------|------|
| POST | /auth/login | 管理员登录(返回 token + role) |
| GET | /auth/me | 获取当前用户(含角色/状态) |
| POST | /auth/logout | 退出登录 |
| GET | /auth/accounts | 后台账号列表(超级管理员看全部；管理员看自己创建的子账号) |
| POST | /auth/accounts | 创建后台账号(管理员仅能创建子账号) |
| GET | /auth/accounts/{id} | 账号详情 |
| PUT | /auth/accounts/{id} | 编辑账号(改密码/昵称/角色/启用状态) |
| DELETE | /auth/accounts/{id} | 删除账号 |

### 7.2 微站管理 (后台)
| 方法 | 路径 | 说明 |
|------|------|------|
| GET | /sites | 微站列表(分页) |
| POST | /sites | 创建微站 |
| GET | /sites/{id} | 微站详情 |
| PUT | /sites/{id} | 更新微站 |
| DELETE | /sites/{id} | 删除微站 |
| PUT | /sites/{id}/status | 更新微站状态 |

### 7.3 模块管理 (后台)
| 方法 | 路径 | 说明 |
|------|------|------|
| GET | /sites/{site_id}/modules | 模块列表 |
| POST | /sites/{site_id}/modules | 创建模块 |
| GET | /sites/{site_id}/modules/{id} | 模块详情 |
| PUT | /sites/{site_id}/modules/{id} | 更新模块 |
| DELETE | /sites/{site_id}/modules/{id} | 删除模块 |
| PUT | /sites/{site_id}/modules/sort | 批量排序 |

### 7.4 账号管理 (后台, 微站前端登录账号)
| 方法 | 路径 | 说明 |
|------|------|------|
| GET | /sites/{site_id}/accounts | 账号列表(分页) |
| POST | /sites/{site_id}/accounts/import | 批量导入账号 |
| DELETE | /sites/{site_id}/accounts/{id} | 删除账号 |
| PUT | /sites/{site_id}/accounts/{id} | 更新账号 |
| PUT | /sites/{site_id}/accounts/{id}/permissions | 设置模块权限 |

### 7.5 文件上传 (后台)
| 方法 | 路径 | 说明 |
|------|------|------|
| POST | /upload/image | 上传图片到OSS |

### 7.6 统计 (后台)
| 方法 | 路径 | 说明 |
|------|------|------|
| GET | /sites/{id}/stats/overview | 总览(PV/UV) |
| GET | /sites/{id}/stats/modules | 模块点击统计 |
| GET | /sites/{id}/stats/trend | 访问趋势 |

### 7.7 公开接口 (H5前端)
| 方法 | 路径 | 说明 |
|------|------|------|
| GET | /p/sites/{code} | 获取微站展示信息 |
| POST | /p/sites/{code}/login | 前端用户登录 |
| GET | /p/sites/{code}/modules | 获取可见模块列表 |
| GET | /p/modules/{id} | 获取模块内容 |
| POST | /p/sites/{code}/access | 上报访问日志 |
| POST | /p/sites/{code}/click | 上报模块点击 |

## 8. 微站模板设计

### template: classic (经典)
- 背景: 渐变蓝紫色
- 九宫格: 白色圆角卡片，居中图标+标题
- 适合: 企业活动、产品展示

### template: dark (暗黑)
- 背景: 深色系
- 九宫格: 半透明深色卡片，亮色文字
- 适合: 科技风、夜间活动

### template: festive (节日)
- 背景: 红色系渐变
- 九宫格: 金色边框卡片，喜庆图标
- 适合: 节日活动、促销

## 9. H5 登录页设计

当微站开启「需要登录」(`need_login=true`) 时，移动端访问会先进入登录页 `/s/{code}/login`。登录页视觉与微站主页保持一致，并复用站点的 KV 图与背景配置。

### 数据来源
登录页在 `onMounted` 调用公开接口 `GET /p/sites/{code}`（无需认证）拉取站点展示信息，用于渲染 KV 与背景：
- `kv_image` — 顶部 KV 横幅
- `background_image` / `background_color` — 页面背景
- `template` — 模板主题（classic / dark / festive）
- `name` — 站点名称（作为标题）

> 站点信息加载失败时仅提示文案，不阻断登录（登录接口 `POST /p/sites/{code}/login` 本身不校验 online 状态，仍可正常登录）。

### 视觉规范
- **页面背景**：优先使用 `background_image`（覆盖式 + 顶部 18% 暗化遮罩）；其次 `background_color`；否则回退到与微站主页一致的模板渐变。
- **KV 横幅**：满宽展示，最大高度 42vh，底部左右圆角 + 阴影；存在 KV 时登录卡片上移 38px 与之叠出层次感。
- **登录卡片**：半透明白底（`rgba(255,255,255,0.92)`）+ `backdrop-filter: blur(12px)` 玻璃拟态，圆角 20px，阴影。
  - 无 KV 时：站点首字母 logo（渐变圆角方块）+ 站点名 + 副标题「请登录后继续访问」。
  - 有 KV 时：精简为站点名 + 副标题。
- **表单**：无 label 输入框，带 `user-o` / `lock` 左图标，外裹浅灰（`#f4f5f8`）圆角容器。
- **登录按钮**：渐变填充（`#667eea → #764ba2`）+ 阴影 + 字间距，圆角全宽。

### 登录流程
提交 `username` / `password` 至 `POST /p/sites/{code}/login`，成功后写入 `localStorage` 的 `h5_token` 与 `h5_nickname`，再 `router.replace` 回到微站主页 `/s/{code}`。

## 10. H5访问流程

```
用户扫码/点击链接
  │
  ▼
GET /p/sites/{code}  ──→  检查微站状态
  │                          ├─ 未到开始时间 → 显示"敬请期待"
  │                          ├─ 已关闭       → 显示关闭文案
  │                          └─ 正常运行     ↓
  ▼
判断 need_login
  │
  ├─ 不需要登录 → 直接展示微站
  │
  └─ 需要登录 → 跳转登录页
       │
       ▼
    POST /p/sites/{code}/login
       │
       ├─ 成功 → 记录登录态 → 展示有权限的模块
       │
       └─ 失败 → 提示错误，重新登录
```

## 11. 安全设计

- 后台管理员: JWT Token认证，密码bcrypt哈希，按角色(`super_admin`/`admin`/`sub_admin`)做微站与账号的访问隔离
- 后台账号禁用(`is_active=false`)后无法登录，登录与接口鉴权双重拦截
- 微站及子资源均做归属校验(`assert_site_access`)，越权访问返回 403
- 前端用户: JWT Token认证（按site隔离），密码bcrypt哈希
- 上传文件: 校验文件类型(jpg/png/gif/webp)和大小(最大10MB)
- 接口防刷: 基于IP的简单限流
- SQL注入: SQLAlchemy ORM参数化查询
- XSS防护: 富文本内容存储前进行HTML净化

## 12. 部署方案

### Nginx配置
```
# admin-frontend → /admin/
# h5-frontend    → /
# API            → /api/
```

### 启动命令
```bash
# 后端
cd backend
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4

# 前端构建
cd admin-frontend && npm run build  # → dist/
cd h5-frontend && npm run build     # → dist/
```
