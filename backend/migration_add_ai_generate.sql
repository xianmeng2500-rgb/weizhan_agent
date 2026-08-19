-- AI 生图模块迁移脚本
-- 说明：新表 ai_generations 由后端 Base.metadata.create_all 自动创建，
--       本脚本仅处理已有表 system_configs 的 ALTER。全新部署无需执行本脚本。

-- 1. system_configs 表新增 AI 生图配置字段
ALTER TABLE system_configs ADD COLUMN ai_provider VARCHAR(50) NOT NULL DEFAULT 'dashscope' COMMENT 'AI 服务商';
ALTER TABLE system_configs ADD COLUMN ai_api_key VARCHAR(255) DEFAULT NULL COMMENT 'AI API Key（通义万相/DashScope）';
ALTER TABLE system_configs ADD COLUMN ai_image_model VARCHAR(100) NOT NULL DEFAULT 'wan2.2-t2i-flash' COMMENT 'AI 生图模型';

-- 2. ai_generations 表（如后端尚未启动，可手动创建）
-- CREATE TABLE ai_generations (
--   id INT AUTO_INCREMENT PRIMARY KEY,
--   user_id INT NOT NULL COMMENT '生成者(后台用户ID)',
--   prompt TEXT NOT NULL COMMENT '提示词',
--   negative_prompt TEXT NULL COMMENT '负面提示词',
--   reference_image VARCHAR(1000) NULL COMMENT '参考图URL(图生图)',
--   result_url VARCHAR(1000) NOT NULL COMMENT '生成结果图URL',
--   provider VARCHAR(50) NOT NULL DEFAULT 'dashscope' COMMENT 'AI服务商',
--   model_name VARCHAR(100) NOT NULL DEFAULT 'wan2.2-t2i-flash' COMMENT '模型名称',
--   size VARCHAR(30) NOT NULL DEFAULT '1024*1024' COMMENT '生成尺寸',
--   created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '生成时间',
--   KEY idx_ai_generations_user_id (user_id),
--   CONSTRAINT fk_ai_generations_user FOREIGN KEY (user_id) REFERENCES users(id)
-- ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='AI 生成记录表';
