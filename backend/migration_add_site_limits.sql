-- 微站容量限制：单个微站报名人数 / 需登录账号数上限（可在系统配置中调整，默认 2000）

ALTER TABLE system_configs
  ADD COLUMN max_accounts_per_site INT NOT NULL DEFAULT 2000 COMMENT '单个微站登录账号数上限',
  ADD COLUMN max_submissions_per_site INT NOT NULL DEFAULT 2000 COMMENT '单个微站报名人数上限';
