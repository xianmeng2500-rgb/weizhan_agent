-- 登录微站报名表单单次提交约束
-- 执行前请确认同一站点、同一表单、同一登录账号不存在重复历史记录。
-- MySQL 的 UNIQUE 索引允许 account_id 为 NULL 的多条记录，因此未登录微站仍可重复提交。

ALTER TABLE form_submissions
  ADD UNIQUE INDEX uq_form_submission_logged_account (site_id, module_id, account_id);
