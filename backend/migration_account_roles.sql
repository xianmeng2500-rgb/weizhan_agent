-- 后台账号分级与权限迁移
-- 说明：将用户(users)表扩展为三级角色 + 启用状态 + 创建者字段

-- 1. 新增 is_active 列（是否启用）
ALTER TABLE `users`
  ADD COLUMN `is_active` TINYINT(1) NOT NULL DEFAULT 1
  COMMENT '是否启用' AFTER `role`;

-- 2. 新增 created_by 列（创建者，上级管理员ID，自引用）
ALTER TABLE `users`
  ADD COLUMN `created_by` INT NULL
  COMMENT '创建者(上级管理员)' AFTER `is_active`,
  ADD CONSTRAINT `fk_users_created_by` FOREIGN KEY (`created_by`) REFERENCES `users`(`id`);

-- 3. 角色默认值调整说明：
--    原 role 取值为 admin/editor，现统一为 super_admin / admin / sub_admin
--    默认管理员 admin 升级为超级管理员（确保有首个超级管理员可管理账号）
UPDATE `users` SET `role` = 'super_admin' WHERE `username` = 'admin';

-- 4. 将其余历史账号统一归入子账号（受限：仅看自己创建的微站，无账号管理权）
--    如需保留某账号为管理员，请手动将其 role 改为 'admin'
UPDATE `users` SET `role` = 'sub_admin' WHERE `role` NOT IN ('super_admin', 'admin');
