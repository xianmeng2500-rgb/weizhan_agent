-- 微站自由拖拽按钮 - 尺寸/形状样式字段迁移脚本
-- 执行方式: mysql -u root -p weizhan < backend/migration_add_button_style.sql

-- Module 表新增自由拖拽按钮样式字段（null 表示使用默认样式，兼容旧数据）
ALTER TABLE modules ADD COLUMN width FLOAT NULL COMMENT '自由布局按钮宽度(百分比0-100, null=自适应)' AFTER position_y;
ALTER TABLE modules ADD COLUMN height FLOAT NULL COMMENT '自由布局按钮高度(百分比0-100, null=自适应内容)' AFTER width;
ALTER TABLE modules ADD COLUMN border_radius INT NULL COMMENT '按钮圆角(px, null=默认)' AFTER height;
ALTER TABLE modules ADD COLUMN bg_color VARCHAR(50) NULL COMMENT '按钮背景色(hex, null=模板默认)' AFTER border_radius;
ALTER TABLE modules ADD COLUMN font_color VARCHAR(50) NULL COMMENT '按钮文字颜色(hex, null=模板默认)' AFTER bg_color;
ALTER TABLE modules ADD COLUMN icon_position VARCHAR(10) NULL COMMENT '图标相对标题位置(left/right/top/bottom, null=left)' AFTER font_color;
ALTER TABLE modules ADD COLUMN content_align VARCHAR(10) NULL COMMENT '内容水平对齐(left/center/right, null=center)' AFTER icon_position;
ALTER TABLE modules ADD COLUMN show_arrow TINYINT(1) NULL COMMENT '是否显示右侧箭头(null=默认显示)' AFTER content_align;
