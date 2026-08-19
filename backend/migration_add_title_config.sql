-- 微站标题配置：KV图下方的标题文字样式
ALTER TABLE sites ADD COLUMN title_config TEXT NULL COMMENT '微站标题配置JSON(文本/字体/颜色/大小/粗细/位置)' AFTER kv_image;
