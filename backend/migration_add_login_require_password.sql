-- ============================================
-- 迁移: 添加登录是否需要密码配置
-- 日期: 2026-08-07
-- 说明: 微站可配置无密码登录，账号即唯一标识
-- ============================================

-- 为 sites 表添加 login_require_password 字段（默认 True 保持原行为）
ALTER TABLE sites
  ADD COLUMN login_require_password TINYINT(1) NOT NULL DEFAULT 1 COMMENT '登录是否需要密码'
  AFTER need_login;
