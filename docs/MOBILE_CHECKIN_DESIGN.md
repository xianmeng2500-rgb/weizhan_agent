# 手机端签到方案（H5 管理员核销端）

- 日期：2026-08-18
- 状态：已实现
- 范围：手机端扫码签到 + 补签（其他配置功能仍在后台管理端）

## 一、需求背景

签到管理此前仅支持 PC 后台操作（扫码盒子 / 摄像头核销）。现场工作人员需要用手机完成扫码签到，要求：

1. 使用后台管理账号登录
2. 登录后选择对应的微站
3. 进入签到页选择签到场次，下方展示该场次签到情况
4. 手机端只提供**签到**与**补签**功能，场次配置、撤销、导出等仍在后台管理端

## 二、方案选型：放在 H5 端而非后台管理端

| 维度 | admin-frontend（Element Plus） | h5-frontend（Vant 4）✅ |
|------|------------------------------|------------------------|
| UI 库 | 桌面端组件，手机上体验差 | 移动端组件库，天然适配 |
| 包体积 | 含富文本、ECharts，首屏重 | 轻量按需加载 |
| 扫码兼容 | BarcodeDetector，iOS Safari 不支持 | jsQR 纯 JS 解码，全端兼容 |

结论：在 h5-frontend 中新增独立的管理员路由组 `/m`，复用现有后端 API，后端零改动。

## 三、整体设计

### 3.1 路由结构（h5-frontend）

```
/m/login              管理员登录页
/m/checkin            微站列表（仅开启签到的微站）
/m/checkin/:siteId    签到页（场次选择 + 扫码 + 补签 + 签到情况）
```

### 3.2 认证隔离

- 管理员 token 存 `m_admin_token`（JWT type=admin），与 H5 用户端 `h5_token`（type=frontend）完全隔离
- 独立 axios 实例（baseURL `/api/v1`），401 自动清除 token 跳 `/m/login`
- 路由守卫：`meta.requiresAdmin` 检查 token，未登录跳 `/m/login`

### 3.3 复用的后端 API（零改动）

| 用途 | 接口 |
|------|------|
| 管理员登录 | `POST /api/v1/auth/login` |
| 微站列表 | `GET /api/v1/checkin/projects` |
| 场次列表（含已签数） | `GET /api/v1/checkin/projects/{site_id}/sessions` |
| 签到记录 | `GET /api/v1/checkin/projects/{site_id}/records?session_id=` |
| 扫码核销 | `POST /api/v1/checkin/projects/{site_id}/scan` |
| 人工补签 | `POST /api/v1/checkin/projects/{site_id}/manual` |
| 补签搜索账号 | `GET /api/v1/sites/{site_id}/accounts?keyword=` |

## 四、功能说明（签到页）

- **场次选择**：底部弹层列出所有场次（名称、时间窗、停用标记、已签人数），默认选中第一个启用场次；顶部展示当前场次已签统计
- **扫码签到**：jsQR + `getUserMedia`（后置摄像头）实时解码；取景框遮罩、震动反馈、全屏结果面板（成功 / 已签到 / 失败及原因）；同码 3 秒防重复
- **输入签到码**：扫码枪或手动输入 `ck1` 码兜底（摄像头不可用时降级方案）
- **补签**：按姓名/手机号/账号远程搜索微站账号 → 确认弹窗（选填补签原因）→ MANUAL 补签，记录操作人
- **签到情况**：当前场次签到记录列表（姓名、脱敏手机号、时间、扫码/补签、撤销标记），下拉刷新 + 触底分页

## 五、代码位置

| 文件 | 说明 |
|------|------|
| `h5-frontend/src/api/admin.ts` | 管理员 API 封装（独立 axios + token 管理） |
| `h5-frontend/src/views/admin/AdminLogin.vue` | 登录页 |
| `h5-frontend/src/views/admin/AdminCheckinSites.vue` | 微站选择页 |
| `h5-frontend/src/views/admin/AdminCheckinScan.vue` | 签到页（核心） |
| `h5-frontend/src/router/index.ts` | `/m` 路由组 + requiresAdmin 守卫 |
| 依赖 | `jsqr@1.4.0`（新增） |

## 六、注意事项与风险

1. **HTTPS 要求**：`getUserMedia` 仅在 HTTPS（或 localhost）可用，生产环境需确认域名证书；微信内打开同样受限
2. **权限兼容性**：不使用 BarcodeDetector（iOS Safari 不支持），统一 jsQR 软解
3. **权限边界**：扫码接口任何管理员角色可用；补签要求 admin 及以上角色（后端 `_can_manage` 控制）
4. **幂等保证**：同一场次重复扫码返回 `ALREADY_CHECKED_IN`，数据库唯一约束 `(site_id, account_id, session_id)` 兜底

## 七、测试路径

1. `npm run dev`（h5-frontend，5174 端口）
2. 手机访问 `/m/login`，用后台管理账号登录
3. 选择微站 → 选择场次
4. 扫用户 H5 签到页（`/s/:code/qrcode/:moduleId`）展示的静态二维码
5. 验证：签到成功 / 重复扫码提示已签到 / 补签流程 / 记录列表刷新
