-- 微站可视化编辑器 - 数据库迁移脚本
-- 执行方式: mysql -u root -p weizhan < backend/migration_add_visual_editor.sql

-- Site 表新增背景图字段
ALTER TABLE sites ADD COLUMN background_image VARCHAR(500) NULL COMMENT '背景图URL' AFTER background_color;

-- Module 表新增自由布局坐标字段
ALTER TABLE modules ADD COLUMN position_x FLOAT NULL COMMENT '自由布局X坐标(百分比0-100)' AFTER is_active;
ALTER TABLE modules ADD COLUMN position_y FLOAT NULL COMMENT '自由布局Y坐标(百分比0-100)' AFTER position_x;
