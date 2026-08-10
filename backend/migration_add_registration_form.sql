-- 微站报名表单功能 - 数据库迁移脚本
-- 执行方式: mysql -u root -p weizhan < backend/migration_add_registration_form.sql

-- Module 表新增表单配置字段
ALTER TABLE modules ADD COLUMN form_config JSON NULL COMMENT '报名表单设计配置(JSON)' AFTER rich_content;

-- 表单提交记录表
CREATE TABLE IF NOT EXISTS form_submissions (
    id INT AUTO_INCREMENT PRIMARY KEY,
    site_id INT NOT NULL COMMENT '所属微站',
    module_id INT NOT NULL COMMENT '所属模块',
    account_id INT NULL COMMENT '提交账号(登录用户)',
    submitter_name VARCHAR(128) NULL COMMENT '提交者姓名',
    submitter_phone VARCHAR(20) NULL COMMENT '提交者手机号',
    data JSON NOT NULL COMMENT '提交数据(JSON)',
    note TEXT NULL COMMENT '备注/管理员备注',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '提交时间',
    INDEX idx_site_id (site_id),
    INDEX idx_module_id (module_id),
    INDEX idx_account_id (account_id),
    FOREIGN KEY (site_id) REFERENCES sites(id) ON DELETE CASCADE,
    FOREIGN KEY (module_id) REFERENCES modules(id) ON DELETE CASCADE,
    FOREIGN KEY (account_id) REFERENCES site_accounts(id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='模块报名表单提交记录';
