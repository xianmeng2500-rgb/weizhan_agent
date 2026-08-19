-- 商业化计费系统迁移脚本
-- 说明：新表（membership_plans/memberships/session_credits/wallet_transactions）
--       由后端 Base.metadata.create_all 自动创建，本脚本仅处理已有表的 ALTER
--       和默认套餐数据。全新部署无需执行本脚本。

-- 1. users 表新增计费字段
ALTER TABLE users ADD COLUMN wallet_balance INT NOT NULL DEFAULT 0 COMMENT '钱包余额(分)';
ALTER TABLE users ADD COLUMN membership_status VARCHAR(20) NOT NULL DEFAULT 'none' COMMENT '会员状态缓存: active/expired/none';
ALTER TABLE users ADD COLUMN membership_end_at DATETIME DEFAULT NULL COMMENT '会员到期时间缓存';
ALTER TABLE users ADD COLUMN session_credit_balance INT NOT NULL DEFAULT 0 COMMENT '场次额度余额缓存';

-- 2. session_credits 表新增 site_id 字段（v1.2: 扣减时机从创建签到场次改为微站上线）
ALTER TABLE session_credits ADD COLUMN site_id INT NULL COMMENT '使用后关联的微站ID(上线扣减)';
ALTER TABLE session_credits ADD CONSTRAINT fk_session_credits_site FOREIGN KEY (site_id) REFERENCES sites(id);

-- 3. 套餐名称更新（v1.2: 签到场次 → 上线场次；已初始化的库执行后可跳过）
UPDATE membership_plans SET name='上线场次', description='单次上线额度，微站每上线一次消耗1个，购买后1年内有效' WHERE plan_type='session_credit';

-- 4. 默认套餐（若后端启动时未自动初始化，可手动执行）
-- INSERT INTO membership_plans (name, plan_type, price, duration_days, credit_quantity, description, is_active)
-- VALUES
--   ('年费会员', 'membership', 49900, 365, NULL, '可创建和管理微站，有效期365天', 1),
--   ('上线场次', 'session_credit', 29900, NULL, 1, '单次上线额度，微站每上线一次消耗1个，购买后1年内有效', 1);
