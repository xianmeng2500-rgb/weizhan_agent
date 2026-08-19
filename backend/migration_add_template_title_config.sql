-- 微站模板表增加标题装饰配置（与 sites.title_config 同构）
-- 执行方式: mysql -u<user> -p <db> < migration_add_template_title_config.sql
ALTER TABLE site_templates
  ADD COLUMN title_config TEXT NULL COMMENT '微站标题装饰配置JSON(enabled/text/font/color/size/bold/position_x/position_y/max_width)' AFTER kv_image;
