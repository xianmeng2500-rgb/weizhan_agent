-- 渠道分销功能迁移
-- 1) users 表新增推广码与推荐人字段
ALTER TABLE users
  ADD COLUMN recommend_code VARCHAR(32) NULL COMMENT '分销推广码' AFTER created_by,
  ADD COLUMN recommend_by INT NULL COMMENT '推荐人(分销上级)' AFTER recommend_code,
  ADD UNIQUE KEY uk_users_recommend_code (recommend_code);

-- 2) 系统配置新增分销开关与返佣比例
ALTER TABLE system_configs
  ADD COLUMN distribution_enabled TINYINT(1) NOT NULL DEFAULT 0 COMMENT '是否启用分销返佣' AFTER ai_image_model,
  ADD COLUMN rebate_rate INT NOT NULL DEFAULT 10 COMMENT '返佣比例(百分比, 默认10%)' AFTER distribution_enabled;

-- 3) 新建返佣记录表（新表由 Base.metadata.create_all 自动创建，此处幂等建表便于手工执行）
CREATE TABLE IF NOT EXISTS rebate_records (
  id INT AUTO_INCREMENT PRIMARY KEY,
  distributor_id INT NOT NULL COMMENT '推荐人(返佣接收者)',
  customer_id INT NOT NULL COMMENT '被推荐人(消费账号)',
  order_type VARCHAR(30) NOT NULL COMMENT '订单类型: membership/session_credit',
  order_ref INT NOT NULL COMMENT '关联购买流水ID(wallet_transactions.id)',
  order_amount INT NOT NULL COMMENT '实付金额(分)',
  rebate_rate INT NOT NULL COMMENT '返佣比例(百分比)',
  rebate_amount INT NOT NULL COMMENT '返佣金额(分)',
  status VARCHAR(20) NOT NULL DEFAULT 'settled' COMMENT 'settled/refunded/revoked/pending_clawback',
  created_at DATETIME NOT NULL COMMENT '返佣产生时间',
  updated_at DATETIME NOT NULL COMMENT '更新时间',
  KEY idx_rebate_distributor (distributor_id),
  KEY idx_rebate_customer (customer_id),
  KEY idx_rebate_status (status),
  KEY idx_rebate_order_ref (order_ref)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='分销返佣记录';
