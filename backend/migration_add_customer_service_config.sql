-- 微站客服配置迁移
-- 执行前请备份数据库；仅适用于已执行 migration_add_system_config_and_share.sql 的数据库。

ALTER TABLE sites ADD COLUMN customer_service_config TEXT NULL COMMENT '客服配置JSON';
