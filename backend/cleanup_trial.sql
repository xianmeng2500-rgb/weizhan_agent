-- 免登录游客试用功能下线：数据库残留清理
--
-- 【重要】这是不可逆操作，执行前请务必先备份数据库。
-- 代码侧已完全移除（后端模型/路由/服务、前端页面/store/路由/菜单均已删除），
-- 本脚本只处理数据库里遗留的表、列与试用草稿站点。
--
-- 执行顺序不能乱：先删数据，再删列，最后删表。

-- 0) 先看一眼有多少残留（建议先跑这段，确认影响面）
SELECT COUNT(*) AS 试用会话数 FROM site_trials;
SELECT COUNT(*) AS 试用草稿站点数 FROM sites WHERE is_trial = 1;

-- 1) 清理试用产生的草稿站点及其关联数据
--    级联删除 modules / accesses / form_submissions 等子表，
--    避免留下指向已删站点 id 的孤儿行。
DELETE FROM sites WHERE is_trial = 1;

-- 2) 清理试用会话 / 线索表（内含手机号等留资信息，删除即不可恢复）
DROP TABLE IF EXISTS site_trials;

-- 3) 移除 sites.is_trial 列（ORM 模型已无该字段，留着不影响运行）
ALTER TABLE sites DROP COLUMN is_trial;

-- 4) 移除 system_configs 的试用配置项
ALTER TABLE system_configs
  DROP COLUMN trial_enabled,
  DROP COLUMN trial_duration_minutes,
  DROP COLUMN trial_template_id,
  DROP COLUMN trial_contact,
  DROP COLUMN trial_convert_url;

-- 5) 复查
SHOW COLUMNS FROM sites LIKE 'is_trial';
SHOW COLUMNS FROM system_configs LIKE 'trial%';
SHOW TABLES LIKE 'site_trials';
