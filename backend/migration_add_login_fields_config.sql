-- ============================================
-- 迁移: 添加可配置登录字段支持
-- 日期: 2026-08-06
-- 说明: 微站支持配置多种登录方式（账号/手机号/自定义字段）
-- ============================================

-- 1. 为 sites 表添加 login_fields_config 字段（JSON 配置）
ALTER TABLE sites
  ADD COLUMN login_fields_config TEXT NULL COMMENT '登录字段配置JSON'
  AFTER customer_service_config;

-- 2. 为 site_accounts 表添加 custom_fields 字段（自定义字段值）
ALTER TABLE site_accounts
  ADD COLUMN custom_fields TEXT NULL COMMENT '自定义字段JSON'
  AFTER phone;
