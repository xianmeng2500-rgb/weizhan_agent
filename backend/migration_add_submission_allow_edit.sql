-- 报名数据支持"单条数据级"的提交后修改控制
-- 该字段表示每条报名数据是否允许提交者修改，最终可修改需满足:
--   模块级 form_config.allowEditAfterSubmit = true AND 数据级 allow_edit = true
-- 默认允许修改（模块默认关闭时整体仍不可修改，保持现状行为）。

ALTER TABLE form_submissions
  ADD COLUMN allow_edit TINYINT(1) NOT NULL DEFAULT 1 COMMENT '是否允许提交后修改(单条数据级)';
