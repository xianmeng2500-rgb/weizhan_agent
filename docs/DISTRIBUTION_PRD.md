# 微站平台渠道分销功能 PRD

> 版本：v1.0
> 日期：2026-08-23
> 状态：待评审
> 前置依赖：预充值钱包 + 会员/额度体系（COMMERCIALIZATION_PRD v1.2）已上线

---

## 一、背景与目标

### 1.1 背景

微站系统当前已具备完整的商业化能力（预充值钱包、会员 499/年、上线额度 299/次），但获客完全依赖平台主动拓展，缺乏「老带新 / 渠道分销」的传播与激励机制，销售增长受限。

### 1.2 目标

- 建立「推广码 → 绑定 → 消费 → 返佣」的一级分销闭环，让老客户 / 渠道伙伴成为平台推广员
- 返佣以**钱包余额**结算（复用现有预充值体系），不引入外部支付
- 仅对**真实成交**返佣，规避多级分销 / 拉人头的合规风险

### 1.3 商业模式与核心规则

| 规则项 | 规则 |
|--------|------|
| 分销层级 | **一级**（只返直接推荐人），不设团队计酬、不设晋级奖励 |
| 返佣比例 | **10%**（超管可在分销设置中调整，范围 0%–20%） |
| 返佣对象 | 被推荐账号**首次**购买会员 / 上线额度（真实成交） |
| 结算方式 | 支付成功后，返佣金额自动入账推荐人**钱包余额**，流水类型 `rebate_in` |
| 绑定方式 | 超管 / 管理员**开号时填写「推荐人推广码」**，绑定关系建立后不可自行修改 |
| 防刷约束 | 被推荐账号须为**无历史消费**的新账号；禁止自我推广；超管可撤销异常返佣 |
| 退款处理 | 被推荐账号消费退款时，系统**自动扣回**对应返佣（`rebate_refund`）；余额不足则挂起待扣回 |

### 1.4 核心流程

```
超管开启分销、配置返佣比例 10%
        ↓
分销商（admin/sub_admin）在「推广中心」查看自己的推广码
        ↓
新客户咨询 → 超管/管理员开号时填写推荐人推广码 → 绑定关系建立
        ↓
新客户购买会员/上线额度（用余额支付）
        ↓
系统自动返佣 10% 入账推荐人钱包余额，生成返佣记录
        ↓
推荐人在「推广中心」查看拉新数据与返佣流水
```

---

## 二、角色定义

| 角色 | 说明 | 权限 |
|------|------|------|
| super_admin | 平台方 | 分销总开关、返佣比例配置、返佣记录查询/撤销、分销商排行；开号时填写推广码 |
| admin / sub_admin | 分销商（推广员） | 查看自己的推广码与推广数据、返佣流水；开号时填写推广码 |
| 被推荐客户 | 新开户 admin | 正常消费，对分销无感知 |

---

## 三、功能清单

### 3.1 分销设置（超管）

**EARS 需求描述：**

- **Ubiquitous**: The system shall provide a global switch for the distribution feature and a configurable rebate rate (0%–20%, default 10%), which takes effect immediately after saving.
- **Event-driven**: When the distribution feature is disabled, the system shall stop generating new rebate records, while existing settled rebates remain unaffected.
- **Event-driven**: When the distribution feature is enabled, only consumption orders created afterwards shall be eligible for rebate calculation.

**功能点：**

| 编号 | 功能 | 说明 |
|------|------|------|
| D-01 | 分销总开关 | 启用 / 停用分销功能，停用后不再产生新返佣 |
| D-02 | 返佣比例配置 | 超管可调整比例（0%–20%，默认 10%），保存立即生效 |
| D-03 | 规则说明文案 | 设置页展示当前生效规则（比例、结算方式、退款处理） |

### 3.2 推广码（分销商身份）

**EARS 需求描述：**

- **Ubiquitous**: The system shall automatically generate a globally unique promotion code for every admin and sub_admin account, and backfill codes for existing accounts.
- **Event-driven**: When a super admin resets an account's promotion code, the system shall invalidate the old code and generate a new one; accounts already bound to the old code shall keep their binding.

**功能点：**

| 编号 | 功能 | 说明 |
|------|------|------|
| D-10 | 自动生成推广码 | 全量后台账号自动分配唯一推广码（字母+数字，长度 8） |
| D-11 | 推广码展示 | 「推广中心」展示我的推广码，支持一键复制 |
| D-12 | 推广码重置（超管） | 后台账号管理可重置某账号推广码（重置后旧码作废） |
| D-13 | 绑定查询（超管） | 按推广码 / 推荐人查询绑定关系与历史记录 |

### 3.3 绑定关系（开号时填写）

**EARS 需求描述：**

- **Event-driven**: When an admin or super admin fills in a promoter code when creating a new account, the system shall validate the code, set the new account's recommender, and reject the request if the code is invalid or belongs to the operator themselves.
- **Unwanted**: If the promoter code does not exist or corresponds to a disabled account, the system shall reject saving the account with a clear error message.
- **Unwanted**: If the promoter code belongs to the account currently being created or to the operator themselves, the system shall reject it as self-promotion.
- **Unwanted**: If an account already has a recommender, the system shall not allow the recommender to be changed through the normal account edit flow (super admin may adjust it manually).

**功能点：**

| 编号 | 功能 | 说明 |
|------|------|------|
| D-20 | 新建账号填推广码 | 「后台账号管理-新建账号」新增可选字段「推荐人推广码」，带存在性 / 自推校验 |
| D-21 | 绑定关系建立 | 保存成功后，被推荐账号记录推荐人；绑定关系不可自行修改 |
| D-22 | 自推拦截 | 推广码为操作者本人或新建账号本人时，拒绝并提示 |
| D-23 | 超管手动调整 | 超管可在后台账号管理中修改某账号的推荐人（保留变更留痕） |

### 3.4 返佣结算

**EARS 需求描述：**

- **Event-driven**: When a referred account successfully purchases a membership plan, the system shall calculate the rebate as (actual payment × rebate rate), credit it to the recommender's wallet balance, and create a rebate record with type `rebate_in`.
- **Event-driven**: When a referred account successfully purchases session credits (上线额度), the system shall calculate and credit the rebate in the same way.
- **Event-driven**: When the referred account has any historical consumption before binding, the system shall NOT generate a rebate for this order (first-purchase-only rule).
- **Event-driven**: When a referred account's order is refunded, the system shall automatically deduct the corresponding rebate from the recommender's wallet balance (type `rebate_refund`); if the balance is insufficient, the rebate shall be marked as `pending_clawback` and deducted first from future credits.
- **Unwanted**: If the recommender is a system-internal account (e.g., super admin), the system shall not generate a rebate.

**功能点：**

| 编号 | 功能 | 说明 |
|------|------|------|
| D-30 | 会员购买返佣 | 被推荐账号购买会员，支付成功后自动返佣 |
| D-31 | 额度购买返佣 | 被推荐账号购买上线额度，支付成功后自动返佣 |
| D-32 | 首次消费校验 | 有历史消费记录的账号不产生返佣 |
| D-33 | 返佣入账 | 返佣金额入账推荐人钱包，流水类型 `rebate_in` |
| D-34 | 退款自动扣回 | 订单退款时自动扣回返佣（`rebate_refund`） |
| D-35 | 余额不足挂起 | 扣回时余额不足，记录标记 `pending_clawback`，后续入账优先扣回 |
| D-36 | 免返佣账号 | 系统内置账号 / 超管账号消费不返佣 |

### 3.5 返佣记录与风控（超管）

**EARS 需求描述：**

- **Ubiquitous**: The system shall record every rebate with its distributor, customer, order type/amount, rate, amount, status, and time.
- **Event-driven**: When a super admin revokes a rebate record, the system shall deduct the amount from the recommender's wallet (marking `revoked`), regardless of whether the original order was refunded.
- **State-driven**: While a rebate record is in `pending_clawback` status, the system shall attempt to deduct it first whenever the recommender's wallet receives any credit.

**功能点：**

| 编号 | 功能 | 说明 |
|------|------|------|
| D-40 | 返佣记录查询 | 超管可按推荐人 / 被推荐人 / 时间 / 状态筛选 |
| D-41 | 返佣撤销 | 超管可撤销异常返佣，自动从推荐人钱包扣回 |
| D-42 | 分销商排行 | 按累计返佣金额 / 累计拉新数排行 |
| D-43 | 状态机 | `settled`（已入账）/ `refunded`（已随退款扣回）/ `revoked`（已撤销）/ `pending_clawback`（待扣回） |

### 3.6 推广中心（分销商自助查看）

**EARS 需求描述：**

- **Ubiquitous**: The system shall provide a promotion center for distributors showing their promotion code, referral statistics (new accounts, total order amount, total rebate), and rebate transaction history.
- **State-driven**: While the distribution feature is disabled, the promotion center shall still display historical data but note that no new rebates will be generated.

**功能点：**

| 编号 | 功能 | 说明 |
|------|------|------|
| D-50 | 推广中心入口 | 侧边栏「推广中心」菜单（admin / sub_admin 可见） |
| D-51 | 推广码卡片 | 展示我的推广码 + 一键复制 + 文案说明 |
| D-52 | 数据统计 | 累计拉新账号数、累计成交金额、累计返佣金额 |
| D-53 | 返佣流水 | 明细列表（时间、客户、订单类型、金额），与钱包流水打通 |
| D-54 | 分销规则说明 | 页内展示当前返佣比例与结算规则 |

---

## 四、数据模型

### 4.1 users 表扩展

| 字段 | 类型 | 说明 |
|------|------|------|
| recommend_code | VARCHAR(32), UNIQUE | 推广码，全量后台账号自动生成 |
| recommend_by | INT, NULL, FK users.id | 推荐人账号 ID |

> 迁移方式：新增两列后，对存量账号批量生成唯一推广码回填；`recommend_by` 默认 NULL（老账号无推荐人）。

### 4.2 新增 rebate_records 表

| 字段 | 类型 | 说明 |
|------|------|------|
| id | INT PK | |
| distributor_id | INT FK users.id | 推荐人 |
| customer_id | INT FK users.id | 被推荐人 |
| order_type | VARCHAR(20) | membership / session_credit |
| order_ref | VARCHAR(64) | 关联订单/流水标识 |
| order_amount | DECIMAL(10,2) | 实付金额 |
| rebate_rate | DECIMAL(5,2) | 返佣比例（如 10.00） |
| rebate_amount | DECIMAL(10,2) | 返佣金额 |
| status | VARCHAR(20) | settled / refunded / revoked / pending_clawback |
| created_at | DATETIME | 返佣产生时间 |

### 4.3 交易流水类型扩展

- 新增 `rebate_in`（返佣入账）、`rebate_refund`（返佣扣回），现有流水查询 / 会员中心流水页自动兼容展示。

---

## 五、接口设计（草案）

| 接口 | 方法 | 权限 | 说明 |
|------|------|------|------|
| `/distribution/config` | GET/PUT | super_admin | 分销开关与比例 |
| `/distribution/my-code` | GET | 登录用户 | 我的推广码 + 统计 |
| `/distribution/rebates` | GET | 登录用户 | 我的返佣流水（分页） |
| `/distribution/rebates/admin` | GET | super_admin | 全量返佣记录（筛选/分页） |
| `/distribution/rebates/{id}/revoke` | POST | super_admin | 撤销返佣 |
| `/distribution/ranking` | GET | super_admin | 分销商排行 |
| `/distribution/rebates/{id}/clawback` | POST | 系统任务 | 挂起返佣的优先扣回（可在入账流程内内联执行） |

---

## 六、交互说明

1. **新建账号表单**：在「后台账号管理 → 新建账号」中新增「推荐人推广码（可选）」输入框，失焦即时校验（不存在 / 自推给出明确错误提示）。
2. **推广中心**：顶部推广码卡片（大号展示 + 复制按钮 + 说明），中部三格统计卡（拉新数 / 成交金额 / 累计返佣），下方返佣流水表格。
3. **分销设置（超管）**：开关 + 比例滑条 / 数字输入 + 规则说明静态文案，保存后 toast 提示生效。
4. **返佣记录（超管）**：筛选区 + 表格（含状态标签：已入账绿色 / 已随退款扣回灰色 / 已撤销红色 / 待扣回黄色）+ 撤销操作需二次确认。

---

## 七、数据指标与埋点

### 7.1 核心指标

| 指标 | 口径 |
|------|------|
| 分销渠道拉新数 | 有推荐人的新增账号数 / 总新增账号数 |
| 分销贡献营收 | 被推荐账号的消费金额合计 |
| 返佣支出占比 | 累计返佣金额 / 累计成交金额（健康线建议 < 20%） |
| 活跃分销商 | 近 30 天有返佣入账的分销商数量 |
| 单分销商业绩 | 累计拉新数 / 累计返佣金额排行 |

### 7.2 埋点

- 推广码查看 / 复制（`distribution.code_view` / `distribution.code_copy`）
- 开户绑定成功（`distribution.bind_success`，携带推广码）
- 返佣入账（`distribution.rebate_in`，携带金额 / 订单类型）
- 返佣撤销 / 扣回挂起（`distribution.revoke` / `distribution.clawback_pending`）

---

## 八、验收标准

| 编号 | 用例 | 预期结果 |
|------|------|---------|
| A-01 | 超管开启分销，配置比例为 10% | 保存成功，推广中心可见最新规则 |
| A-02 | admin A 查看推广码并复制 | 展示唯一推广码，复制成功 |
| A-03 | 开号填写不存在推广码 | 保存被拒，提示「推广码不存在」 |
| A-04 | 开号填写操作者本人推广码 | 保存被拒，提示自推不允许 |
| A-05 | 新客户 B（无历史消费）开号填 A 的推广码，购买 499 会员 | B 绑定 A；支付成功后 A 钱包 +49.9，流水 `rebate_in`，生成 settled 返佣记录 |
| A-06 | 新客户 B 再购买 299 额度 | A 再 +29.9 返佣 |
| A-07 | 有历史消费的账号 C 被填推广码后购买 | 不产生返佣 |
| A-08 | B 的会员订单被超管退款 | A 钱包自动 -49.9，返佣记录变 `refunded` |
| A-09 | 超管撤销某条返佣记录 | A 钱包扣回金额，记录变 `revoked` |
| A-10 | 扣回时 A 余额不足 | 记录变 `pending_clawback`；A 后续任意入账时优先扣回直至补足 |
| A-11 | 分销功能停用后新消费 | 不产生新返佣，历史记录不受影响 |
| A-12 | sub_admin 推广 | 拥有推广码，返佣入其父 admin 钱包（沿用余额继承） |
| A-13 | 分销商排行 / 返佣流水查询 | 数据准确，可按条件筛选 |

---

## 九、风险与合规

| 风险 | 说明 | 应对 |
|------|------|------|
| 多级分销合规 | 三级以上 / 拉人头计酬存在传销定性风险 | 固定一级返佣、仅按真实消费计酬、不设团队计酬，规则文案明确写入设置页 |
| 返佣侵蚀利润 | 比例过高导致毛利受损 | 上限 20%，默认 10%；设置页展示返佣支出占比指标 |
| 刷单 | 分销商自购 / 虚假开户套返佣 | 自推拦截 + 首次消费才返佣 + 开号人工流程 + 超管可撤销 |
| 绑定不可撤销的争议 | 客户投诉被错误绑定 | 超管可手动调整推荐人，操作留痕 |
| 退款倒挂 | 返佣已花、订单又退款 | 自动扣回 + 余额不足挂起优先扣回 |

---

## 十、待确认问题

1. **返佣比例**：默认 10% 起步，是否开放超管调整区间为 0%–20%？（当前设计：开放，区间可配）
2. **返佣上限**：单个分销商累计返佣是否设上限？（当前设计：不设）
3. **老账号补绑定**：存量客户账号是否允许超管事后补填推荐人？（当前设计：允许，通过后台账号管理手动调整）
4. **推广说明文档**：是否需要为分销商提供一页「分销推广指南」（话术 + 操作步骤）？（建议做，成本低）
5. **排期与资源**：功能开发排期、联调环境、上线窗口需研发负责人确认。
