"""预置演示账号与演示数据（幂等：账号/微站已存在则跳过）

用法：
    cd backend && .venv/bin/python seed_demo.py
    cd backend && .venv/bin/python seed_demo.py --reset   # 删除演示数据后重建

演示账号（密码均为 Demo@123456）：
    demo_admin  演示商家·发布会运营（会员+余额+额度，含完整发布会微站与签到）
    demo_shop   演示商家·品牌推广（会员+余额+额度，含品牌盛典微站）
"""
import argparse
import json
import sys
from datetime import datetime, timedelta, timezone

from sqlalchemy import inspect

from app.database import SessionLocal
from app.models import (
    User, Site, Module, SiteAccount, AccountModulePermission,
    CheckinConfig, CheckinSession,
    Membership, MembershipPlan, SessionCredit,
)
from app.utils.security import hash_password

DEMO_PASSWORD = "Demo@123456"

DEMO_USERNAMES = ("demo_admin", "demo_shop")
DEMO_SITE_CODES = ("demo-launch", "demo-festival")


def utcnow() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


def _column_exists(db, table: str, column: str) -> bool:
    try:
        cols = {c["name"] for c in inspect(db.bind).get_columns(table)}
        return column in cols
    except Exception:
        return False


def get_plan(db, plan_type: str) -> MembershipPlan | None:
    return db.query(MembershipPlan).filter(
        MembershipPlan.plan_type == plan_type,
        MembershipPlan.is_active == True,  # noqa: E712
    ).first()


def ensure_user(db, username: str, nickname: str, balance_cents: int, credits: int) -> User:
    """创建演示账号（会员+余额+额度），已存在则跳过"""
    user = db.query(User).filter(User.username == username).first()
    if user:
        print(f"  [跳过] 演示账号 {username} 已存在")
        return user
    user = User(
        username=username,
        password_hash=hash_password(DEMO_PASSWORD),
        nickname=nickname,
        role="admin",
        is_active=True,
        wallet_balance=balance_cents,
    )
    db.add(user)
    db.flush()

    plan = get_plan(db, "membership")
    if plan:
        end = utcnow() + timedelta(days=plan.duration_days or 365)
        db.add(Membership(
            user_id=user.id, plan_id=plan.id,
            start_at=utcnow(), end_at=end, status="active",
        ))
        user.membership_status = "active"
        user.membership_end_at = end
    else:
        print("  [警告] 未找到会员套餐，跳过开通会员（请确认已初始化默认套餐）")

    for _ in range(credits):
        db.add(SessionCredit(
            user_id=user.id, transaction_id=None,
            status="unused", expire_at=utcnow() + timedelta(days=365),
        ))
    user.session_credit_balance = credits

    db.flush()
    print(f"  [创建] 演示账号 {username}（{nickname}），余额 ¥{balance_cents / 100}，额度 {credits} 个，会员已开通")
    return user


def ensure_site(db, owner: User, name: str, code: str, template: str, **kw) -> Site:
    """创建演示微站，已存在则跳过"""
    site = db.query(Site).filter(Site.code == code).first()
    if site:
        print(f"  [跳过] 演示微站 {name}（{code}）已存在")
        return site
    defaults = dict(
        layout="grid",
        background_color="",
        share_title=name,
        share_subtitle="微站系统演示站点",
        need_login=False,
        login_require_password=True,
        need_checkin=False,
        status="online",
        created_by=owner.id,
    )
    defaults.update(kw)
    # Text 列需要 JSON 字符串序列化（dict 无法直接绑定 MySQL 参数）
    if isinstance(defaults.get("title_config"), dict):
        defaults["title_config"] = json.dumps(defaults["title_config"], ensure_ascii=False)
    site = Site(name=name, code=code, template=template, **defaults)
    db.add(site)
    db.flush()
    print(f"  [创建] 演示微站 {name}（/s/{code}）")
    return site


def ensure_module(db, site: Site, title: str, content_type: str, sort_order: int, **kw) -> Module:
    m = Module(site_id=site.id, title=title, content_type=content_type, sort_order=sort_order, is_active=True, **kw)
    db.add(m)
    db.flush()
    return m


def seed_launch_site(db, owner: User):
    """发布会微站：登录 + 报名(可修改) + 日程 + 签到"""
    site = ensure_site(
        db, owner, "2026 新品发布会", "demo-launch", "dark",
        need_login=True, need_checkin=True,
        title_config={
            "enabled": True, "text": "2026 新品发布会",
            "font": "sans", "color": "#ffffff", "size": 22,
            "bold": True, "position": "center",
        },
    )
    if site.modules:  # 已存在（跳过）
        return

    ensure_module(db, site, "活动介绍", "rich_text", 1, rich_content=(
        "<p>我们诚挚邀请您参加 <b>2026 年度新品发布会</b>。</p>"
        "<p>届时将发布全新一代产品，现场设有体验区与媒体专访，欢迎莅临。</p>"
        "<p>时间：2026-09-18 14:00<br/>地点：深圳国际会展中心 · 1 号馆</p>"
    ))
    ensure_module(db, site, "立即报名", "registration_form", 2, form_config={
        "title": "发布会报名",
        "description": "请填写以下信息完成报名",
        "buttonText": "提交报名",
        "allowEditAfterSubmit": True,
        "fields": [
            {"id": "name", "type": "text", "title": "姓名", "required": True, "placeholder": "请输入姓名"},
            {"id": "phone", "type": "phone", "title": "手机号", "required": True, "placeholder": "请输入手机号"},
            {"id": "company", "type": "text", "title": "公司", "required": False, "placeholder": "请输入公司名称"},
            {"id": "remark", "type": "textarea", "title": "备注", "required": False, "placeholder": "想了解的方面"},
        ],
    })
    ensure_module(db, site, "大会议程", "schedule", 3, schedule_config={"items": [
        {"date": "2026-09-18", "time": "14:00-14:30", "topic": "嘉宾签到入场", "personnel": "会务组"},
        {"date": "2026-09-18", "time": "14:30-15:30", "topic": "新品发布主题演讲", "personnel": "产品副总裁"},
        {"date": "2026-09-18", "time": "15:30-16:00", "topic": "产品体验与交流", "personnel": "产品团队"},
    ]})
    ensure_module(db, site, "签到二维码", "qrcode", 4, qrcode_config={
        "hint": "现场出示此二维码，由工作人员扫码完成签到",
        "display_fields": ["username"],
    })
    ensure_module(db, site, "官方网站", "external_link", 5, external_url="https://example.com")

    # 签到场次
    db.add(CheckinConfig(site_id=site.id))
    db.add(CheckinSession(site_id=site.id, name="上午场", sort_order=1))
    db.add(CheckinSession(site_id=site.id, name="下午场", sort_order=2))

    # 微站登录账号（演示 H5 登录 + 模块权限）
    mods = {m.title: m for m in site.modules}
    for uname, nick in (("zhangsan", "张三"), ("lisi", "李四")):
        acc = SiteAccount(
            site_id=site.id, username=uname,
            password_hash=hash_password(DEMO_PASSWORD),
            nickname=nick, phone="13800000000", is_active=True,
        )
        db.add(acc)
        db.flush()
        # 张三全部可见，李四仅可见活动介绍与签到二维码（演示模块级权限）
        visible = ("活动介绍", "签到二维码") if uname == "lisi" else list(mods.keys())
        for title in visible:
            if title in mods:
                db.add(AccountModulePermission(account_id=acc.id, module_id=mods[title].id))
    print("  [创建] 登录账号 zhangsan / lisi（密码 Demo@123456），已配置模块级权限")


def seed_festival_site(db, owner: User):
    """品牌盛典微站：公开访问 + 报名 + 日程"""
    site = ensure_site(
        db, owner, "中秋品牌盛典", "demo-festival", "festive",
        title_config={
            "enabled": True, "text": "中秋品牌盛典",
            "font": "song", "color": "#b8860b", "size": 24,
            "bold": True, "position": "center",
        },
    )
    if site.modules:
        return
    ensure_module(db, site, "活动亮点", "rich_text", 1, rich_content=(
        "<p>中秋佳节，与家人朋友共赴一场品牌文化盛宴。</p>"
        "<p>现场设有品牌快闪店、传统手作体验、赏月晚会等活动。</p>"
        "<p>时间：2026-09-26 至 2026-09-28<br/>地点：城市之心广场</p>"
    ))
    ensure_module(db, site, "预约报名", "registration_form", 2, form_config={
        "title": "盛典预约",
        "description": "提交预约，到场即可快速入场",
        "buttonText": "提交预约",
        "allowEditAfterSubmit": False,
        "fields": [
            {"id": "name", "type": "text", "title": "姓名", "required": True, "placeholder": "请输入姓名"},
            {"id": "phone", "type": "phone", "title": "手机号", "required": True, "placeholder": "请输入手机号"},
        ],
    })
    ensure_module(db, site, "活动日程", "schedule", 3, schedule_config={"items": [
        {"date": "2026-09-26", "time": "10:00-18:00", "topic": "品牌快闪店开放", "personnel": "各大品牌"},
        {"date": "2026-09-27", "time": "15:00-17:00", "topic": "传统手作体验", "personnel": "非遗老师"},
        {"date": "2026-09-28", "time": "19:00-21:00", "topic": "中秋赏月晚会", "personnel": "演出团队"},
    ]})
    ensure_module(db, site, "联系我们", "external_link", 4, external_url="https://example.com")


def bind_distribution(db):
    """演示分销绑定：demo_shop 由 demo_admin 推荐（依赖分销迁移，列不存在则跳过）"""
    if not _column_exists(db, "users", "recommend_by"):
        print("  [跳过] users 表缺少 recommend_by 列（未执行分销迁移），演示分销绑定已跳过")
        return
    admin = db.query(User).filter(User.username == "demo_admin").first()
    shop = db.query(User).filter(User.username == "demo_shop").first()
    if not admin or not shop:
        return
    if not admin.recommend_code:
        from app.services import distribution_service
        admin.recommend_code = distribution_service.get_or_create_recommend_code(db, admin)
    if not shop.recommend_by:
        shop.recommend_by = admin.id
        print(f"  [创建] 分销演示绑定：demo_shop ← 推荐人 demo_admin（推广码 {admin.recommend_code}）")


def main():
    parser = argparse.ArgumentParser(description="预置演示账号与演示数据")
    parser.add_argument("--reset", action="store_true", help="删除已有演示数据后重建")
    args = parser.parse_args()

    db = SessionLocal()
    try:
        if args.reset:
            for code in DEMO_SITE_CODES:
                site = db.query(Site).filter(Site.code == code).first()
                if site:
                    db.delete(site)
            db.flush()
            for username in DEMO_USERNAMES:
                user = db.query(User).filter(User.username == username).first()
                if user:
                    db.delete(user)
            db.flush()
            print("已删除旧的演示数据")

        print("== 演示账号 ==")
        owner1 = ensure_user(db, "demo_admin", "演示商家·发布会运营", balance_cents=50000, credits=5)
        owner2 = ensure_user(db, "demo_shop", "演示商家·品牌推广", balance_cents=30000, credits=3)

        print("== 演示微站 ==")
        seed_launch_site(db, owner1)
        seed_festival_site(db, owner2)

        bind_distribution(db)

        db.commit()
        print("== 完成 ==")
        print(f"后台登录地址：/admin/   （账号 demo_admin / demo_shop，密码 {DEMO_PASSWORD}）")
        print(f"H5 微站地址：/s/demo-launch（需登录：zhangsan 或 lisi，密码 {DEMO_PASSWORD}）")
        print(f"H5 微站地址：/s/demo-festival（公开访问）")
    except Exception as e:
        db.rollback()
        print(f"执行失败，已回滚：{e}", file=sys.stderr)
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()
