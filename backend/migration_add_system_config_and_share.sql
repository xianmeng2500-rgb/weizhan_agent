-- 系统配置与单站微信分享字段迁移
-- 执行前请备份数据库；适用于已有微站系统数据库。

CREATE TABLE IF NOT EXISTS system_configs (
  id INT NOT NULL PRIMARY KEY,
  h5_domain VARCHAR(500) NULL COMMENT '移动端 H5 对外域名',
  wechat_share_enabled TINYINT(1) NOT NULL DEFAULT 0 COMMENT '是否启用微信分享',
  wechat_app_id VARCHAR(128) NULL COMMENT '微信 AppID',
  wechat_app_secret VARCHAR(255) NULL COMMENT '微信 AppSecret',
  oss_access_key_id VARCHAR(255) NULL COMMENT 'OSS AccessKey ID',
  oss_access_key_secret VARCHAR(255) NULL COMMENT 'OSS AccessKey Secret',
  oss_bucket_name VARCHAR(255) NULL COMMENT 'OSS Bucket',
  oss_endpoint VARCHAR(500) NULL COMMENT 'OSS Endpoint',
  oss_custom_domain VARCHAR(500) NULL COMMENT 'OSS 自定义域名',
  local_icon_library TEXT NULL COMMENT '本地图标库 JSON',
  updated_by INT NULL COMMENT '最后修改人',
  updated_at DATETIME NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

INSERT IGNORE INTO system_configs (id, wechat_share_enabled) VALUES (1, 0);

ALTER TABLE sites ADD COLUMN share_image VARCHAR(500) NULL COMMENT '微信分享图标';
ALTER TABLE sites ADD COLUMN share_title VARCHAR(128) NULL COMMENT '微信分享标题';
ALTER TABLE sites ADD COLUMN share_subtitle VARCHAR(255) NULL COMMENT '微信分享副标题';
