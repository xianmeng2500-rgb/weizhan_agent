# 微站系统商业化方案 PRD

> 版本：v1.2  
> 日期：2026-08-18  
> 状态：已开发完成  
> v1.2 变更：**额度扣减时机从「创建签到场次」改为「微站上线」**——每上线一次扣 1 个额度（299元/次），无额度无法上线；下线不退额度，再次上线重新扣减；创建签到场次不再收费。

---

## 一、背景与目标

### 1.1 背景

微站系统当前为纯工具产品，已具备多微站管理、九宫格布局、富文本编辑、签到系统等完整功能。为推进商业化，需要引入预充值钱包 + 会员制收费体系，实现可持续盈利。

### 1.2 商业模式

采用**预充值钱包模式**：超管为用户账户充值余额，用户用余额自助购买会员和场次额度。

| 收费项 | 价格 | 权益说明 | 计费维度 |
|--------|------|---------|---------|
| 微站会员 | 499元/年 | 可创建和管理微站（含内容编辑、模块管理、账号管理、数据统计） | 按年订阅 |
| 上线额度 | 299元/次 | 微站每上线一次消耗1个额度；下线不退，再次上线重新消耗 | 按次付费 |

### 1.3 核心规则

- **预充值钱包**：超管为用户账户充值余额，用户使用余额自助购买会员/场次额度
- **499年费 = 建微站使用权**：不含签到功能，签到每场单独收费
- **499不限微站数量**：年费会员可创建任意数量的微站，不限量
- **299/次 = 微站上线额度**：购买后获得1个额度，微站上线时扣减
- **额度有效期1年**：购买后1年内必须使用，过期作废
- **上线计费规则（v1.2）**：每次上线扣1个额度；无额度无法上线；上线后可下线但已扣额度不退；再次上线重新扣1个
- **到期处理**：会员到期后，所有微站全部变为只读（H5仍可访问，后台不可编辑），续费后恢复
- **价格可配置**：499和299的价格由超管在后台自定义配置，支持调价促销
- **sub_admin继承**：子账号完全继承父账号的会员状态和场次额度，不单独扣费
- **退款**：超管可手动退回钱包余额，撤销对应权益
- **无需外部支付**：所有充值由超管在后台操作，不接入第三方支付

### 1.4 核心流程

```
超管充值 → 用户钱包有余额 → 用户自助购买会员(扣499) / 购买上线额度(扣299)
                                    ↓                        ↓
                             获得会员有效期              获得上线额度
                                    ↓                        ↓
                          可创建/编辑微站            微站上线时扣减额度
```

### 1.5 目标

- 建立预充值钱包体系，超管可充值、用户可自助消费
- 建立会员体系，控制微站创建权限
- 建立场次额度体系，控制签到场次创建权限
- 所有交易有流水记录，可追溯

---

## 二、角色定义

| 角色 | 说明 | 权限 |
|------|------|------|
| super_admin | 超级管理员 | 全部功能 + 钱包充值 + 套餐配置 + 流水查看 + 退款 |
| admin (付费会员) | 钱包有余额的已购会员客户 | 可创建微站、管理自己的微站；签到需另购场次额度 |
| admin (未付费) | 未购买会员的客户 | 不可创建新微站，已有微站变为只读 |
| sub_admin | 子账号 | 由 admin 分配，继承父账号的会员状态和额度 |

---

## 三、功能清单

### 3.1 钱包体系

**EARS 需求描述：**

- **Ubiquitous**: The system shall maintain a wallet balance for each admin user, recording all recharge and consumption transactions.
- **Event-driven**: When the super admin recharges a user's wallet, the system shall increase the user's balance and create a transaction record.
- **Event-driven**: When a user purchases a membership or session credit, the system shall deduct the corresponding amount from the wallet balance and create a transaction record.
- **Unwanted**: If a user attempts to purchase an item with insufficient wallet balance, the system shall reject the request with a clear error message.
- **Event-driven**: When the super admin performs a refund, the system shall restore the wallet balance and revoke the corresponding benefit.

**功能点：**

| 编号 | 功能 | 说明 |
|------|------|------|
| W-01 | 钱包余额查询 | 用户可在会员中心查看自己的钱包余额 |
| W-02 | 超管充值 | 超管为指定用户充值余额（金额可配，备注必填） |
| W-03 | 自助购买会员 | 用户用余额购买会员套餐（扣对应金额） |
| W-04 | 自助购买场次额度 | 用户用余额购买场次额度（299元/场，可批量） |
| W-05 | 余额不足拦截 | 购买时余额不足，返回提示"余额不足，请联系管理员充值" |
| W-06 | 流水记录 | 所有充值/消费/退款操作生成流水记录 |
| W-07 | 流水查询 | 超管可查看所有用户流水，普通用户可查看自己的流水 |
| W-08 | 超管退款 | 超管可退回用户余额，撤销对应权益 |

### 3.2 会员体系

#### 3.2.1 会员状态管理

**EARS 需求描述：**

- **Ubiquitous**: The system shall maintain a membership record for each admin user, tracking their membership start date, end date, and status.
- **State-driven**: While a user's membership is active, the system shall allow full access to site creation and editing features.
- **State-driven**: While a user's membership is expired, the system shall restrict site creation and editing, rendering existing sites read-only (H5 remains accessible).
- **Event-driven**: When a membership is activated or renewed, the system shall set the end date to max(current_end_date, today) + plan_duration_days.

**功能点：**

| 编号 | 功能 | 说明 |
|------|------|------|
| M-01 | 会员状态查询 | 用户可查看自己的会员状态（到期时间、剩余天数） |
| M-02 | 自助购买会员 | 用户用钱包余额购买会员套餐 |
| M-03 | 会员到期处理 | 到期后微站全部变只读，H5仍可访问 |
| M-04 | 会员状态展示 | 后台导航栏/工作台显示会员状态徽标 |
| M-05 | 到期提醒 | 到期前7天/3天/1天，后台展示提醒横幅 |

#### 3.2.2 会员套餐配置

**功能点：**

| 编号 | 功能 | 说明 |
|------|------|------|
| P-01 | 套餐列表 | 超管可查看/编辑套餐（名称、价格、时长、描述） |
| P-02 | 套餐启用/停用 | 超管可停用某个套餐（停用后用户不可购买） |

**默认套餐：**

| 套餐名 | 价格 | 时长 | 说明 |
|--------|------|------|------|
| 年费会员 | 499元 | 365天 | 可创建和管理微站 |
| 签到场次 | 299元 | — | 单场签到额度（有效期1年） |

### 3.3 上线额度体系

**EARS 需求描述：**

- **Ubiquitous**: The system shall maintain a session credit balance for each admin user, tracking unused and used credits, with each credit having an expiry date of 1 year from purchase.
- **Event-driven**: When a user puts a site online, the system shall consume one session credit (earliest expiring first) and link it to the site.
- **Unwanted**: If a user attempts to put a site online without sufficient valid (non-expired) credits, the system shall reject the request with a clear error message guiding them to purchase credits.
- **Unwanted**: If a session credit has expired (purchase date + 365 days < current date), the system shall mark it as expired and exclude it from the available balance.
- **State-driven**: While a site is offline, the system shall NOT refund the consumed credit; putting it online again shall consume another credit.
- **Optional**: Where a checkin session is created, the system shall NOT consume any credit (v1.2: 扣减时机仅在上线).

**功能点：**

| 编号 | 功能 | 说明 |
|------|------|------|
| C-01 | 上线额度查询 | 用户可查看自己的剩余上线额度（含即将过期提醒） |
| C-02 | 自助购买额度 | 用户用钱包余额购买上线额度（可批量购买） |
| C-03 | 上线扣减 | 微站上线时自动扣减1个额度（优先扣减即将过期的），状态改为 online 前扣减 |
| C-04 | 额度不足拦截 | 可用额度为0时，上线接口返回403，微站保持原状态 |
| C-05 | 额度使用记录 | 记录每个额度的购买时间、到期时间、使用时间、关联微站 |
| C-06 | 额度过期处理 | 购买后1年未使用的额度自动标记为过期，不计入可用余额 |
| C-07 | 额度即将过期提醒 | 到期前30天/7天，后台展示提醒 |

### 3.4 超管管理后台

**功能点：**

| 编号 | 功能 | 说明 |
|------|------|------|
| A-01 | 会员管理列表 | 查看所有用户的会员状态、钱包余额、额度余额 |
| A-02 | 钱包充值 | 超管为用户充值（金额、备注） |
| A-03 | 套餐管理 | 管理会员套餐和场次额度价格配置 |
| A-04 | 流水查询 | 查看所有用户的充值/消费/退款流水 |
| A-05 | 退款操作 | 超管可退回用户余额，撤销对应权益 |
| A-06 | 收入统计 | 超管工作台展示总充值、总消费、活跃会员数、场次数等 |

---

## 四、数据模型设计

### 4.1 新增表

#### membership_plans（会员套餐表）

```sql
CREATE TABLE membership_plans (
    id INT PRIMARY KEY AUTO_INCREMENT,
    name VARCHAR(50) NOT NULL COMMENT '套餐名称',
    plan_type ENUM('membership', 'session_credit') NOT NULL COMMENT '套餐类型',
    price INT NOT NULL DEFAULT 0 COMMENT '价格（分）',
    duration_days INT DEFAULT NULL COMMENT '时长（天），membership类型使用',
    credit_quantity INT DEFAULT NULL COMMENT '额度数量，session_credit类型使用',
    description VARCHAR(500) DEFAULT NULL COMMENT '描述',
    is_active BOOLEAN DEFAULT TRUE COMMENT '是否启用',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);
```

#### memberships（会员记录表）

```sql
CREATE TABLE memberships (
    id INT PRIMARY KEY AUTO_INCREMENT,
    user_id INT NOT NULL COMMENT '用户ID（关联users表）',
    plan_id INT NOT NULL COMMENT '套餐ID',
    transaction_id INT DEFAULT NULL COMMENT '关联流水ID',
    start_at DATETIME NOT NULL COMMENT '会员开始时间',
    end_at DATETIME NOT NULL COMMENT '会员到期时间',
    status ENUM('active', 'expired', 'refunded') DEFAULT 'active' COMMENT '状态',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_user (user_id),
    INDEX idx_status (status)
);
```

#### session_credits（场次额度表）

```sql
CREATE TABLE session_credits (
    id INT PRIMARY KEY AUTO_INCREMENT,
    user_id INT NOT NULL COMMENT '用户ID',
    transaction_id INT DEFAULT NULL COMMENT '关联流水ID',
    session_id INT DEFAULT NULL COMMENT '使用后关联的签到场次ID',
    status ENUM('unused', 'used', 'expired', 'refunded') DEFAULT 'unused' COMMENT '状态',
    expire_at DATETIME NOT NULL COMMENT '到期时间（购买后+365天）',
    used_at DATETIME DEFAULT NULL COMMENT '使用时间',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_user_status (user_id, status),
    INDEX idx_expire (expire_at)
);
```

#### wallet_transactions（钱包流水表）

```sql
CREATE TABLE wallet_transactions (
    id INT PRIMARY KEY AUTO_INCREMENT,
    user_id INT NOT NULL COMMENT '用户ID',
    tx_type ENUM('recharge', 'purchase_membership', 'purchase_credit', 'refund') NOT NULL COMMENT '交易类型',
    amount INT NOT NULL COMMENT '金额（分），正数=入账，负数=扣款',
    balance_after INT NOT NULL COMMENT '交易后余额（分）',
    plan_id INT DEFAULT NULL COMMENT '关联套餐ID（购买时）',
    membership_id INT DEFAULT NULL COMMENT '关联会员记录ID（购买会员时）',
    session_credit_ids VARCHAR(500) DEFAULT NULL COMMENT '关联额度ID列表（购买场次时，逗号分隔）',
    operator_id INT DEFAULT NULL COMMENT '操作人（充值/退款时为超管ID）',
    remark VARCHAR(500) DEFAULT NULL COMMENT '备注',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_user (user_id),
    INDEX idx_type (tx_type),
    INDEX idx_created (created_at)
);
```

### 4.2 现有表变更

#### users 表新增字段

```sql
ALTER TABLE users ADD COLUMN wallet_balance INT NOT NULL DEFAULT 0 COMMENT '钱包余额（分）';
ALTER TABLE users ADD COLUMN membership_status ENUM('active', 'expired', 'none') DEFAULT 'none' COMMENT '会员状态缓存';
ALTER TABLE users ADD COLUMN membership_end_at DATETIME DEFAULT NULL COMMENT '会员到期时间缓存';
ALTER TABLE users ADD COLUMN session_credit_balance INT DEFAULT 0 COMMENT '场次额度余额缓存';
```

> 说明：在 users 表冗余缓存字段，避免每次查询都 JOIN。由后端在充值/购买/到期/扣减时同步更新。

### 4.3 ER 关系

```
users ──1:N──> wallet_transactions (充值/消费/退款流水)
  │
  ├──1:N──> memberships ──N:1──> membership_plans
  │                │
  │                └──N:1──> wallet_transactions (购买时关联)
  │
  ├──1:N──> session_credits
  │                │
  │                ├──N:1──> wallet_transactions (购买时关联)
  │                │
  │                └──N:1──> checkin_sessions (使用时关联)
  │
  └──1:N──> membership_plans (作为可选套餐)
```

---

## 五、接口设计

### 5.1 钱包相关接口

#### 查询我的钱包

```
GET /api/v1/wallet/me
```

**响应：**
```json
{
    "balance": 100000,
    "balance_yuan": "1000.00",
    "membership": {
        "status": "active",
        "plan_name": "年费会员",
        "end_at": "2027-08-18T00:00:00",
        "days_remaining": 365
    },
    "session_credits": 3
}
```

#### 超管：充值

```
POST /api/v1/wallet/recharge
```

**请求：**
```json
{
    "user_id": 5,
    "amount": 100000,
    "remark": "客户微信转账1000元"
}
```

**逻辑：**
- amount > 0
- 更新 users.wallet_balance += amount
- 创建 wallet_transaction（type=recharge, amount=+amount, balance_after=新余额, operator_id=超管ID）

#### 查询流水

```
GET /api/v1/wallet/transactions          # 查看自己的流水
GET /api/v1/admin/wallet/transactions    # 超管查看所有流水（支持筛选）
```

**参数：** user_id, tx_type, start_date, end_date, page, page_size

#### 超管：退款

```
POST /api/v1/wallet/refund
```

**请求：**
```json
{
    "transaction_id": 123,
    "remark": "客户要求退款"
}
```

**逻辑：**
- 查询原交易流水，校验 tx_type 为 purchase_membership 或 purchase_credit
- 如果是 purchase_membership：撤销会员（回退到期时间），退回余额
- 如果是 purchase_credit：撤销未使用的额度，退回余额；已使用的场次不退
- 创建 wallet_transaction（type=refund, amount=+原金额）
- 更新 users.wallet_balance

### 5.2 会员相关接口

#### 自助购买会员

```
POST /api/v1/membership/purchase
```

**请求：**
```json
{
    "plan_id": 1
}
```

**逻辑：**
1. 查询 plan，校验 plan_type='membership' 且 is_active=true
2. 校验余额：users.wallet_balance >= plan.price
3. 如果用户已有 active 会员：end_at = max(当前end_at, now) + plan.duration_days
4. 如果用户无会员或已过期：start_at = now, end_at = now + plan.duration_days
5. 创建 membership 记录
6. 扣减余额：users.wallet_balance -= plan.price
7. 创建 wallet_transaction（type=purchase_membership, amount=-plan.price, balance_after=新余额, plan_id, membership_id）
8. 更新 users 缓存：membership_status='active', membership_end_at=new_end_at

### 5.3 场次额度相关接口

#### 自助购买场次额度

```
POST /api/v1/session-credits/purchase
```

**请求：**
```json
{
    "plan_id": 2,
    "quantity": 3
}
```

**逻辑：**
1. 查询 plan，校验 plan_type='session_credit' 且 is_active=true
2. 计算总价：total = plan.price * quantity
3. 校验余额：users.wallet_balance >= total
4. 创建 quantity 条 session_credits（status=unused, expire_at=now+365天）
5. 扣减余额：users.wallet_balance -= total
6. 创建 wallet_transaction（type=purchase_credit, amount=-total, balance_after=新余额, session_credit_ids=逗号分隔ID列表）
7. 更新 users.session_credit_balance += quantity

### 5.4 套餐管理接口

```
GET    /api/v1/membership/plans              # 查询套餐列表（所有用户可查，用于购买页展示）
POST   /api/v1/admin/plans                   # 新增套餐（仅超管）
PUT    /api/v1/admin/plans/{id}              # 编辑套餐（仅超管）
```

### 5.5 超管管理接口

```
GET    /api/v1/admin/members                 # 会员管理列表（含搜索/筛选）
GET    /api/v1/admin/members/{user_id}       # 用户详情（会员+钱包+额度）
GET    /api/v1/admin/revenue/stats           # 收入统计
```

### 5.6 现有接口改造

#### 创建微站 - 增加会员校验

`POST /api/v1/sites` 增加前置校验：

```python
# 在 sites.py 路由中增加
async def create_site(..., current_admin: User = Depends(get_current_admin)):
    # 新增：校验会员状态
    if current_admin.role != 'super_admin':
        # sub_admin 继承父账号
        owner = get_membership_owner(current_admin)
        if owner.membership_status != 'active':
            raise HTTPException(403, detail="您的会员已过期，请在会员中心续费后创建微站")
    # ... 原有逻辑
```

#### 更新微站状态（上线/下线）- 增加额度扣减（v1.2）

`PUT /api/v1/sites/{site_id}/status` 当目标状态为 online 且当前状态非 online 时：

```python
# 在 sites.py update_status 路由中
if req.status == "online" and site.status != "online" and current.role != ROLE_SUPER_ADMIN:
    try:
        consume_credit_for_site_online(db, current, site.id)  # 优先扣减即将过期的
    except ValueError:
        raise HTTPException(403, detail="CREDIT_INSUFFICIENT:场次额度不足，无法上线...")
# 扣减成功后才置 site.status = online；下线(offline)不退额度
```

> 创建签到场次接口 `POST /api/v1/checkin/projects/{site_id}/sessions` 不再扣减额度（v1.2 移除）。

#### 编辑微站 - 增加会员校验

`PUT /api/v1/sites/{id}` 和所有模块编辑接口增加会员状态校验，非 active 状态返回 403。

---

## 六、前端页面设计

### 6.1 admin-frontend 新增页面

#### 会员中心页 `/billing`

```
┌──────────────────────────────────────────────┐
│  会员中心                                      │
├──────────────────────────────────────────────┤
│  ┌──────────────────────────────────────────┐│
│  │  钱包余额：¥1,000.00          [充值记录]   ││
│  │  （余额不足时联系管理员充值）               ││
│  └──────────────────────────────────────────┘│
│                                              │
│  ┌──────────────────────────────────────────┐│
│  │  会员状态：● 有效                          ││
│  │  套餐：年费会员                            ││
│  │  到期时间：2027-08-18  剩余：365天         ││
│  │                              [续费 499元]  ││
│  └──────────────────────────────────────────┘│
│                                              │
│  ┌──────────────────────────────────────────┐│
│  │  签到场次额度：3 场                        ││
│  │  （其中1场将于30天后过期）                  ││
│  │                          [购买 299元/场]  ││
│  └──────────────────────────────────────────┘│
│                                              │
│  交易流水                                     │
│  ┌──────────────────────────────────────────┐│
│  │  时间       类型        金额      余额     ││
│  │  08-18 10:00 充值        +1000.00  1000.00││
│  │  08-18 10:05 购买会员     -499.00   501.00││
│  │  08-18 10:06 购买场次     -299.00   202.00││
│  └──────────────────────────────────────────┘│
└──────────────────────────────────────────────┘
```

#### 超管：会员管理页 `/admin/members`

```
┌──────────────────────────────────────────────────────────┐
│  会员管理                                                  │
│  [搜索用户名]  [筛选会员状态]                                │
├──────────────────────────────────────────────────────────┤
│  用户名   会员状态  到期时间   钱包余额  场次余额  操作       │
│  ────────────────────────────────────────────────────── │
│  userA    ●有效    2027-08-18  ¥202.00  3      [充值] [详情]│
│  userB    ○过期    2026-08-01  ¥0.00    0      [充值]      │
│  userC    —未开通  —          ¥0.00    0      [充值]      │
│                                                          │
│  [充值]                                                   │
└──────────────────────────────────────────────────────────┘
```

#### 超管：充值弹窗

```
┌──────────────────────────────┐
│  钱包充值                      │
├──────────────────────────────┤
│  用户：userA                  │
│  当前余额：¥202.00             │
│  充值金额：[    ] 元           │
│  备注：[____________________] │
│                              │
│  ⓘ 请确认已收到客户转账后再充值 │
│                              │
│  [取消]       [确认充值]       │
└──────────────────────────────┘
```

#### 超管：用户详情页 `/admin/members/:userId`

```
┌──────────────────────────────────────────────┐
│  用户详情 - userA                              │
├──────────────────────────────────────────────┤
│  账户信息                                      │
│  钱包余额：¥202.00    [充值]                    │
│  会员状态：●有效  到期：2027-08-18              │
│  场次额度：3场（1场即将过期）                    │
│                                              │
│  交易流水                                      │
│  ┌──────────────────────────────────────────┐│
│  │  时间       类型        金额      操作     ││
│  │  08-18 10:00 充值        +1000.00  —      ││
│  │  08-18 10:05 购买会员     -499.00  [退款]  ││
│  │  08-18 10:06 购买场次     -299.00  [退款]  ││
│  └──────────────────────────────────────────┘│
└──────────────────────────────────────────────┘
```

#### 购买会员弹窗

```
┌──────────────────────────────┐
│  购买会员                      │
├──────────────────────────────┤
│  套餐：年费会员                │
│  价格：¥499.00                │
│  时长：365天                   │
│  当前余额：¥1000.00            │
│  支付后余额：¥501.00           │
│                              │
│  [取消]      [确认购买]        │
└──────────────────────────────┘
```

#### 购买场次额度弹窗

```
┌──────────────────────────────┐
│  购买场次额度                   │
├──────────────────────────────┤
│  单价：¥299.00/场              │
│  数量：[- 1 +] 场              │
│  合计：¥299.00                │
│  当前余额：¥501.00            │
│  支付后余额：¥202.00           │
│                              │
│  ⓘ 购买后1年内有效，过期作废    │
│                              │
│  [取消]      [确认购买]        │
└──────────────────────────────┘
```

### 6.2 导航栏改造

在后台 Layout.vue 的侧边栏增加菜单项：

```
工作台
签到管理
微站管理
账号管理
会员中心 ← 新增（所有管理员可见）
管理员配置
  └── 会员管理 ← 新增（仅超管可见）
  └── 系统配置
```

### 6.3 到期提醒横幅

在 Layout.vue 顶部增加提醒横幅组件：

```
┌──────────────────────────────────────────────────────┐
│ ⚠ 您的会员将于3天后到期，请及时在会员中心续费  [去续费] [×] │
└──────────────────────────────────────────────────────┘
```

### 6.4 创建场次时的额度提示

在 CheckinDetail.vue 的"添加场次"按钮处：

- 有额度：正常点击创建
- 无额度：点击后弹出提示「场次额度不足，请前往会员中心购买（299元/场）」，并提供跳转按钮

### 6.5 创建微站时的会员提示

在 SiteList.vue 的"创建微站"按钮处：

- 会员有效：正常点击创建
- 会员过期/未开通：点击后弹出提示「会员未开通或已过期，请前往会员中心购买（499元/年）」，并提供跳转按钮

---

## 七、计费逻辑详解

### 7.1 充值逻辑

```
输入：user_id, amount（分）, operator_id, remark

1. 校验 amount > 0
2. 更新 users.wallet_balance += amount
3. 创建 wallet_transaction：
   tx_type = 'recharge'
   amount = +amount
   balance_after = users.wallet_balance（更新后的值）
   operator_id = 超管ID
   remark = 备注
```

### 7.2 购买会员逻辑

```
输入：user_id, plan_id

1. 查询 plan，校验 plan_type='membership' 且 is_active=true
2. 校验余额：wallet_balance >= plan.price，否则返回 403 "余额不足"
3. 查询用户当前最新的 active membership
4. 如果存在且 active：
   new_end_at = max(existing.end_at, now) + plan.duration_days（续费延长）
5. 如果不存在或已 expired：
   new_end_at = now + plan.duration_days（新开）
6. 创建 membership 记录
7. 扣减余额：wallet_balance -= plan.price
8. 创建 wallet_transaction：
   tx_type = 'purchase_membership'
   amount = -plan.price
   balance_after = wallet_balance（扣减后）
   plan_id = plan.id
   membership_id = new_membership.id
9. 更新 users 缓存：membership_status='active', membership_end_at=new_end_at
```

### 7.3 购买场次额度逻辑

```
输入：user_id, plan_id, quantity

1. 查询 plan，校验 plan_type='session_credit' 且 is_active=true
2. total = plan.price * quantity
3. 校验余额：wallet_balance >= total，否则返回 403 "余额不足"
4. 创建 quantity 条 session_credits：
   status = 'unused'
   expire_at = now + 365天
   transaction_id = 即将创建的 transaction ID
5. 扣减余额：wallet_balance -= total
6. 创建 wallet_transaction：
   tx_type = 'purchase_credit'
   amount = -total
   balance_after = wallet_balance（扣减后）
   plan_id = plan.id
   session_credit_ids = 逗号分隔的credit ID列表
7. 更新 users.session_credit_balance += quantity
```

### 7.4 上线额度扣减逻辑（v1.2）

```
输入：user_id, site_id（待上线的微站ID）
触发：PUT /sites/{site_id}/status 且 req.status == 'online' 且 site.status != 'online'

1. 确定额度归属：sub_admin 取 created_by（父账号ID），否则取自身ID；super_admin 免费跳过
2. 查询 session_credits WHERE user_id=? AND status='unused' AND expire_at > now
   ORDER BY expire_at ASC LIMIT 1（优先扣减即将过期的）
3. 如果无记录 → 403 "CREDIT_INSUFFICIENT"，微站状态不变
4. 更新该 credit 记录：
   status = 'used'
   site_id = ?
   used_at = now
5. 更新 owner.session_credit_balance -= 1
6. 扣减成功后才更新 site.status = 'online'
7. 下线（offline）不退额度；再次上线重复上述流程再扣1个
```

### 7.5 会员过期处理

**定时任务**（建议每小时执行一次）：

```
1. 查询所有 membership_status='active' 且 membership_end_at < now 的用户
2. 更新 membership_status = 'expired'
3. 更新对应 membership 记录 status = 'expired'
4. 这些用户的微站自动变为只读（通过 membership_status 判断，无需改 site 表）
```

### 7.6 场次额度过期处理

**定时任务**（建议每天执行一次）：

```
1. 查询 session_credits WHERE status='unused' AND expire_at < now
2. 批量更新 status = 'expired'
3. 重新计算受影响用户的 session_credit_balance（unused + 未过期 的数量）
```

### 7.7 退款逻辑

```
输入：transaction_id（原购买流水ID）, operator_id, remark

1. 查询原 wallet_transaction，校验 tx_type 为 purchase_membership 或 purchase_credit
2. 如果是 purchase_membership：
   a. 查询关联的 membership 记录
   b. 如果 membership 仍 active：
      - 将 end_at 回退到扣除该套餐时长前的值
      - 如果回退后 end_at < now → status='expired', 同步 users 缓存
   c. 如果 membership 已 expired：仅退余额
   d. 退回余额：wallet_balance += 原金额
3. 如果是 purchase_credit：
   a. 查询关联的所有 session_credits
   b. unused 且未过期的 → status='refunded'，可退
   c. used 的 → 不退（场次已使用）
   d. 计算可退金额 = (可退数量 / 总数量) * 原金额
   e. 退回余额：wallet_balance += 可退金额
   f. 重新计算 session_credit_balance
4. 创建退款 wallet_transaction：
   tx_type = 'refund'
   amount = +退款金额
   balance_after = wallet_balance（退回后）
   operator_id = 超管ID
   remark = 退款备注
```

### 7.8 权限校验矩阵

| 操作 | super_admin | admin (会员有效) | admin (会员过期) | sub_admin |
|------|-------------|-----------------|-----------------|-----------|
| 创建微站 | ✅ 直接 | ✅ 不限量 | ❌ 403 拦截 | ✅ 继承父账号 |
| 编辑微站 | ✅ 直接 | ✅ 校验通过 | ❌ 403 只读 | ✅ 继承父账号 |
| 微站上线 | ✅ 免费 | ✅ 扣1个额度 | ❌ 403 拦截 | ✅ 继承(扣父额度) |
| 微站下线 | ✅ | ✅ 不退额度 | ✅ 不退额度 | ✅ |
| 创建签到场次 | ✅ 直接 | ✅ 不扣额度(v1.2) | ❌ 403 拦截 | ✅ 不扣额度 |
| H5访问微站 | ✅ | ✅ | ✅ 不受影响 | ✅ |
| 查看统计 | ✅ | ✅ | ❌ 只读 | ✅ |
| 购买会员 | ❌ 不需要 | ✅ 扣余额 | ✅ 扣余额 | ❌ 继承父账号 |
| 购买上线额度 | ❌ 不需要 | ✅ 扣余额 | ✅ 扣余额 | ❌ 继承父账号 |
| 钱包充值 | ✅ 充值 | ❌ | ❌ | ❌ |
| 退款操作 | ✅ 手动退款 | ❌ | ❌ | ❌ |

> sub_admin 的会员状态和额度继承其父账号（created_by 对应的 admin 用户）。sub_admin 上线微站时扣减父账号的额度。sub_admin 不参与购买，由父账号购买后继承。

---

## 八、前端改造点清单

### admin-frontend

| 文件 | 改造内容 |
|------|---------|
| `src/router/index.ts` | 新增 `/billing`、`/admin/members`、`/admin/members/:id` 路由 |
| `src/views/Layout.vue` | 侧边栏增加"会员中心"和"会员管理"菜单；增加到期提醒横幅 |
| `src/views/Dashboard.vue` | 工作台增加钱包余额卡片、会员状态卡片、场次额度卡片 |
| `src/views/SiteList.vue` | 创建微站按钮增加会员校验，过期时弹窗引导去购买 |
| `src/views/SiteWorkspace.vue` | 编辑页增加会员校验，过期时展示只读提示 |
| `src/views/CheckinDetail.vue` | 添加场次按钮增加额度校验，不足时弹窗引导去购买 |
| **新增** `src/views/Billing.vue` | 会员中心页（钱包+会员+额度+流水） |
| **新增** `src/views/admin/MemberList.vue` | 超管会员管理列表页 |
| **新增** `src/views/admin/MemberDetail.vue` | 超管用户详情页（充值+流水+退款） |
| **新增** `src/api/billing.ts` | 钱包/会员/额度/流水 API 封装 |

### h5-frontend

无需改动。H5 端用户不受会员体系影响。

---

## 九、后端改造点清单

### 新增文件

| 文件 | 内容 |
|------|------|
| `backend/app/models/membership.py` | MembershipPlan + Membership 模型 |
| `backend/app/models/session_credit.py` | SessionCredit 模型 |
| `backend/app/models/wallet.py` | WalletTransaction 模型 |
| `backend/app/schemas/membership.py` | 会员相关 Pydantic schema |
| `backend/app/schemas/session_credit.py` | 场次额度相关 schema |
| `backend/app/schemas/wallet.py` | 钱包流水相关 schema |
| `backend/app/routers/wallet.py` | 钱包相关路由（充值/流水/退款） |
| `backend/app/routers/membership.py` | 会员购买+套餐路由 |
| `backend/app/routers/admin_billing.py` | 超管管理路由 |
| `backend/app/services/billing_service.py` | 计费业务逻辑封装 |
| `backend/app/utils/membership_check.py` | 会员校验依赖 |

### 修改文件

| 文件 | 改造内容 |
|------|---------|
| `backend/app/models/user.py` | 新增 wallet_balance / membership_status / membership_end_at / session_credit_balance 字段 |
| `backend/app/routers/sites.py` | 创建微站接口增加会员校验 |
| `backend/app/routers/modules.py` | 编辑模块接口增加会员校验 |
| `backend/app/routers/checkin.py` | 创建场次接口增加额度扣减 |
| `backend/app/utils/deps.py` | 新增 `require_active_membership` 依赖 |
| `backend/app/main.py` | 注册新路由；启动时创建默认套餐；注册定时任务 |
| `backend/app/config.py` | 新增会员相关配置项 |

### 数据库迁移

新建 `backend/migrations/001_add_membership.sql`，内容为上述 SQL 建表语句 + users 表 ALTER 语句 + 插入默认套餐：

```sql
INSERT INTO membership_plans (name, plan_type, price, duration_days, credit_quantity, description) VALUES
('年费会员', 'membership', 49900, 365, NULL, '可创建和管理微站，有效期365天'),
('签到场次', 'session_credit', 29900, NULL, 1, '单场签到额度，购买后1年有效');
```

---

## 十、定时任务

### 会员过期检查

```
触发频率：每小时
逻辑：
1. SELECT * FROM users WHERE membership_status='active' AND membership_end_at < NOW()
2. 批量更新 membership_status='expired'
3. 更新对应 memberships 记录 status='expired'
```

### 场次额度过期检查

```
触发频率：每天 00:30
逻辑：
1. SELECT * FROM session_credits WHERE status='unused' AND expire_at < NOW()
2. 批量更新 status='expired'
3. 重新计算受影响用户的 session_credit_balance（unused + 未过期 的数量）
```

建议使用 APScheduler 或简单的 cron 脚本。

---

## 十一、后续扩展（v2.0）

### 11.1 在线支付充值

- 接入微信支付 Native（PC扫码）+ JSAPI（H5）
- 用户自助充值：生成支付二维码 → 支付成功 → 自动到账
- 支付回调自动更新 wallet_balance

### 11.2 自动续费

- 微信支付委托代扣
- 到期前3天自动扣款续费

### 11.3 套餐升级

- 支持多种套餐（季度、半年、年）
- 套餐升级补差价

### 11.4 场次额度批量优惠

- 5场套餐 1299（省199）
- 10场套餐 2499（省491）

### 11.5 试用功能

- 新用户免费试用7天
- 试用期内可建1个微站

---

## 十二、验收标准

### 12.1 钱包体系

- [ ] 超管可在后台为用户充值，充值后余额正确增加
- [ ] 充值后生成流水记录，记录金额、操作人、备注
- [ ] 用户可在会员中心查看钱包余额和交易流水
- [ ] 余额不足时购买操作返回403，前端展示"余额不足"提示

### 12.2 会员体系

- [ ] 用户可自助用余额购买会员，购买后到期时间正确计算
- [ ] 续费时到期时间在现有基础上延长（不覆盖）
- [ ] 会员到期后，用户无法创建/编辑微站，已有微站H5仍可访问
- [ ] 会员到期后，后台编辑页展示只读提示
- [ ] 后台导航栏/工作台正确展示会员状态和到期时间
- [ ] 到期前7天/3天/1天展示提醒横幅

### 12.3 上线额度

- [ ] 用户可自助用余额购买上线额度（支持批量），购买后额度余额正确增加
- [ ] 额度购买时自动设置到期时间（购买后+365天）
- [ ] 用户上线微站时，自动扣减1个额度（优先扣减即将过期的）；扣减成功后微站才变为 online
- [ ] 额度不足时，上线接口返回403，微站状态不变，前端展示引导提示
- [ ] 下线不退额度；下线后再次上线重新扣1个额度
- [ ] 创建/编辑/删除签到场次不消耗额度
- [ ] 额度过期后自动标记为expired，不计入可用余额
- [ ] 额度使用记录可追溯（购买时间、到期时间、使用时间、关联微站）

### 12.4 超管管理

- [ ] 超管可查看所有用户会员状态、钱包余额、额度余额
- [ ] 超管可查看所有用户交易流水
- [ ] 超管可对购买流水执行退款，自动撤销对应权益，退回余额
- [ ] 超管可自定义修改套餐价格
- [ ] 所有充值/退款操作有流水记录

### 12.5 权限控制

- [ ] super_admin 不受会员/额度限制，不需要购买
- [ ] sub_admin 继承父账号的会员状态和额度
- [ ] sub_admin 创建场次时扣减父账号的额度
- [ ] 非超管无法访问会员管理页面和充值功能

---

## 十三、已确认决策

| 问题 | 决策 |
|------|------|
| 支付方式 | **预充值钱包模式**，超管手动充值，不接入外部支付 |
| sub_admin 会员继承 | **完全继承父账号**的会员状态和场次额度，不单独扣费 |
| 会员到期后微站处理 | **全部只读**，后台不可编辑，H5仍可正常访问 |
| 价格配置 | **超管可在后台自定义修改**价格，支持调价促销 |
| 微站数量限制 | **不限量**，499年费可创建任意数量的微站 |
| 场次额度有效期 | **1年有效**，购买后365天内必须使用，过期作废 |
| 退款规则 | **超管手动退款**，退回钱包余额，撤销对应权益（已使用的场次不退） |
| 额度扣减时机（v1.2） | **微站上线时扣减**（原为创建签到场次时）；每次上线扣1个，下线不退，再次上线重扣；无额度无法上线 |
