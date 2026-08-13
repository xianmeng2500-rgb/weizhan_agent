-- 添加登录表单配置字段（存储位置对齐等配置）
ALTER TABLE sites ADD COLUMN login_form_config TEXT NULL COMMENT '登录表单配置JSON(位置等)' AFTER login_fields_config;
