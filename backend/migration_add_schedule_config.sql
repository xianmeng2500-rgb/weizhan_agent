-- 添加日程安排配置字段
-- 执行方式: mysql -h <host> -u <user> -p <db> < backend/migration_add_schedule_config.sql

ALTER TABLE modules
ADD COLUMN schedule_config JSON NULL COMMENT '日程安排配置(JSON)'
AFTER form_config;
