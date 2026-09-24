"""案例微站种子脚本：创建 6 个覆盖不同行业的演示微站（幂等）

用法（在 backend 目录下）:
    .venv/bin/python seed_demo_cases.py                # 上传资产 + 创建案例
    .venv/bin/python seed_demo_cases.py --dry-run      # 只打印将要执行的操作
    .venv/bin/python seed_demo_cases.py --skip-upload  # 资产已在 OSS 时跳过上传
    .venv/bin/python seed_demo_cases.py --reset        # 删除 6 个案例微站后重建

说明:
- KV 主视觉 / 内容配图 / 演示附件位于 seed_assets/demo/，由 tools/gen_demo_kv.py 生成（已随仓库提供）
- 资产上传到 OSS 的 weizhan/demo/ 目录
- 案例归属 demo_admin 账号（须先执行 seed_demo.py 创建演示账号）
- 含签到的案例（summit/annual/chamber）开启 need_login + need_checkin，并预置登录账号演示模块级权限
"""
import argparse
import json
import os
import sys
import uuid
from datetime import timedelta

from app.database import SessionLocal
from app.models import (
    User, Site, Module, SiteAccount, AccountModulePermission,
    CheckinConfig, CheckinSession,
)
from app.utils.security import hash_password

BASE = os.path.dirname(os.path.abspath(__file__))
ASSET_DIR = os.path.join(BASE, "seed_assets", "demo")
OSS_PREFIX = "weizhan/demo"
ICON_BASE = "https://simon-node-test.oss-cn-hangzhou.aliyuncs.com/weizhan/icon/"
DEMO_PASSWORD = "Demo@123456"

CASE_CODES = ("demo-wedding", "demo-course", "demo-summit",
              "demo-annual", "demo-store", "demo-chamber")

ASSETS = [
    "kv_wedding.png", "kv_course.png", "kv_summit.png",
    "kv_annual.png", "bg_store.png", "kv_chamber.png",
    "img_wedding_layout.png", "img_course_path.png", "img_summit_venue.png",
    "img_annual_awards.png", "img_store_perks.png", "img_chamber_org.png",
    "img_wedding_venue.png", "img_wedding_detail.png",
    "img_course_room.png", "img_summit_past.png", "img_annual_stage.png",
    "img_store_products.png", "img_chamber_hall.png",
    "doc_charter.pdf",
]


def load_env():
    env = {}
    path = os.path.join(BASE, ".env")
    for line in open(path, encoding="utf-8"):
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, v = line.split("=", 1)
            env[k.strip()] = v.strip()
    return env


def utcnow():
    from datetime import datetime, timezone
    return datetime.now(timezone.utc).replace(tzinfo=None)


# ---------------------------------------------------------------- 富文本片段

def note(text, bg="#EEF2FF", bar="#4F46E5", color="#3730A3"):
    return (f"<div style=\"background:{bg};border-left:4px solid {bar};padding:10px 14px;"
            f"border-radius:8px;margin:12px 0;font-size:14px;color:{color};\">{text}</div>")


def table(headers, rows):
    th = "".join(f"<th style=\"padding:8px 10px;background:#F1F5F9;text-align:left;\">{x}</th>"
                 for x in headers)
    trs = "".join("<tr>" + "".join(
        f"<td style=\"padding:8px 10px;border-bottom:1px solid #EEF1F6;\">{c}</td>" for c in r) + "</tr>"
        for r in rows)
    return (f"<table style=\"border-collapse:collapse;width:100%;font-size:14px;margin:10px 0;\">"
            f"<thead><tr>{th}</tr></thead><tbody>{trs}</tbody></table>")


def pic(url, alt=""):
    return f"<p><img src=\"{url}\" alt=\"{alt}\" style=\"border-radius:10px;\"></p>"


# ---------------------------------------------------------------- 种子工具

def ensure_site(db, owner: User, name: str, code: str, template: str, **kw) -> Site:
    site = db.query(Site).filter(Site.code == code).first()
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
    # title_config 为 Text 列，dict 必须序列化为 JSON 字符串
    if isinstance(defaults.get("title_config"), dict):
        defaults["title_config"] = json.dumps(defaults["title_config"], ensure_ascii=False)

    if site:
        # 已存在：同步外观/配置字段（演示站点以脚本为准），模块内容不动
        changed = []
        for f in _APPEARANCE_FIELDS:
            if f in defaults and getattr(site, f) != defaults[f]:
                setattr(site, f, defaults[f])
                changed.append(f)
        print(f"  [更新] {name}（/s/{code}）：{', '.join(changed) if changed else '无变化'}")
        db.flush()
        return site

    site = Site(name=name, code=code, template=template, **defaults)
    db.add(site)
    db.flush()
    print(f"  [创建] 案例 {name}（/s/{code}，{template}/{defaults['layout']}）")
    return site


# 已存在站点需要随脚本同步的字段（演示外观以脚本为准）
_APPEARANCE_FIELDS = (
    "template", "layout", "kv_image", "background_image", "background_color",
    "share_title", "share_subtitle", "title_config",
    "need_login", "login_require_password", "need_checkin",
    "start_time", "end_time", "status",
)


def mod(db, site: Site, title: str, content_type: str, sort_order: int, icon: str = "img-bule-2.png", **kw):
    """按标题 upsert 模块：已存在则同步内容字段（保持 id 稳定），不存在则创建"""
    data = dict(content_type=content_type, sort_order=sort_order,
                icon=ICON_BASE + icon if icon else None, is_active=True, **kw)
    m = next((m for m in site.modules if m.title == title), None)
    created = m is None
    if created:
        m = Module(site_id=site.id, title=title)
        db.add(m)
    changed = [f for f in data if getattr(m, f) != data[f]]
    for f in changed:
        setattr(m, f, data[f])
    db.flush()
    _SYNCED_TITLES.setdefault(site.id, set()).add(title)
    tag = "创建" if created else ("更新" if changed else "无变化")
    print(f"  [模块] {site.code} · {title}（{tag}）")
    return m


# 记录本次脚本为每个站点写入过的模块标题，供 prune_extra 判断多余模块
_SYNCED_TITLES: dict[int, set] = {}


def prune_extra(db, site: Site):
    """停用脚本中已不存在的模块（改名/删除遗留），仅置 is_active=False，不删数据"""
    keep = _SYNCED_TITLES.get(site.id, set())
    stale = [m for m in site.modules if m.title not in keep and m.is_active]
    for m in stale:
        m.is_active = False
    if stale:
        db.flush()
        print(f"  [停用] {site.code} 脚本外模块：{'、'.join(m.title for m in stale)}")


def add_accounts(db, site: Site, accounts):
    """accounts: [(username, nickname, 可见模块标题列表(None=全部))]，按用户名幂等"""
    mods = {m.title: m for m in site.modules}
    for uname, nick, visible in accounts:
        acc = db.query(SiteAccount).filter(
            SiteAccount.site_id == site.id, SiteAccount.username == uname).first()
        if acc:
            print(f"  [账号] {site.code} · {uname} 已存在，跳过")
            continue
        acc = SiteAccount(
            site_id=site.id, username=uname,
            password_hash=hash_password(DEMO_PASSWORD),
            nickname=nick, phone="13800000000", is_active=True,
        )
        db.add(acc)
        db.flush()
        for title in (list(mods.keys()) if visible is None else visible):
            if title in mods:
                db.add(AccountModulePermission(account_id=acc.id, module_id=mods[title].id))
        print(f"  [账号] {site.code} + {uname}（{nick}，密码 {DEMO_PASSWORD}）")


def add_checkin(db, site: Site, sessions):
    """签到配置与场次，按名称幂等"""
    if not db.query(CheckinConfig).filter(CheckinConfig.site_id == site.id).first():
        db.add(CheckinConfig(site_id=site.id))
    existing = {s.name for s in db.query(CheckinSession).filter(CheckinSession.site_id == site.id)}
    added = [n for n in sessions if n not in existing]
    for i, name in enumerate(sessions, 1):
        if name in existing:
            continue
        db.add(CheckinSession(site_id=site.id, name=name, sort_order=i))
    print(f"  [签到] {site.code} 场次：{'、'.join(sessions)}" + ("" if added else "（已存在，跳过）"))


# ---------------------------------------------------------------- 六个案例

def case_wedding(db, owner, urls):
    """婚礼邀请函：公开访问 + 宾客回执（分组表单）+ 席位图 + 流程"""
    site = ensure_site(
        db, owner, "张伟 & 李娜 婚礼邀请", "demo-wedding", "classic",
        layout="button", kv_image=urls["kv_wedding.png"],
        share_title="张伟 & 李娜 婚礼邀请",
        share_subtitle="2026.10.18 云栖厅，诚邀您见证我们的幸福时刻",
        title_config={"enabled": False, "text": "张伟 & 李娜", "font": "sans",
                      "color": "#ffffff", "size": 22, "bold": True, "position": "center"},
    )
    mod(db, site, "邀请函", "rich_text", 1, "img-bule-2.png", rich_content=(
        "<p style=\"text-align:center;\">诚挚邀请您出席我们的婚礼</p>"
        "<p style=\"text-align:center;font-size:17px;\"><b>张伟 &amp; 李娜</b></p>"
        "<p style=\"text-align:center;\">新郎 张伟 · 新娘 李娜<br>"
        "谨定于 2026 年 10 月 18 日（星期日），在云栖酒店三层云栖厅举行婚礼</p>"
        + table(["项目", "信息"], [
            ["恭候签到", "10:30 起（三层电梯口签到台）"],
            ["婚礼仪式", "11:08（午宴 12:00 - 14:00）"],
            ["地点", "云栖厅 · 三层宴会厅（杭州市西湖区云栖路 88 号）"],
            ["着装建议", "正装 / 商务休闲（香槟色、莫兰迪色系为佳）"],
            ["回执截止", "10 月 8 日（便于我们安排席位与餐食）"],
        ])
        + "<p style=\"text-align:center;\">张建国 · 王秀兰 携子 张伟<br>"
          "李国强 · 赵雅琴 携女 李娜　敬邀</p>"
        + "<p>一路走来，感谢您的陪伴与支持。人生最重要的一天，盼望与您共同见证。</p>"
        + note("温馨提示：酒店地下停车场 B2 层可免费停车 4 小时，凭回执在签到台领取停车券。")
    ))
    mod(db, site, "我们的故事", "rich_text", 2, "img-bule-7.png", rich_content=(
        "<h3>2019 · 相遇</h3>"
        "<p>在大学同学的生日聚会上第一次见面，因为同一支乐队的歌聊到了散场。</p>"
        "<h3>2022 · 同行</h3>"
        "<p>一起搬进第一个家，养了一只叫「元宵」的猫，学会了在争吵后先递一杯热水。</p>"
        "<h3>2024 · 求婚</h3>"
        "<p>西湖初雪的那个傍晚，他在断桥边单膝跪地。她说「你头发上都白了」，然后哭了。</p>"
        "<h3>2026 · 见证</h3>"
        "<p>我们决定把往后的日子正式交给彼此。10 月 18 日，希望你也在场。</p>"
        + note("「往后余生，风雪是你，平淡是你。」—— 婚礼请柬内页")
    ))
    mod(db, site, "婚礼流程", "schedule", 3, "img-bule-1.png", schedule_config={"items": [
        {"date": "2026-10-18", "time": "09:30-10:00", "topic": "接驳车首班发车（云栖地铁站 C 口）", "personnel": "接驳组"},
        {"date": "2026-10-18", "time": "10:00-10:30", "topic": "宾客签到 · 迎宾茶点", "personnel": "迎宾组"},
        {"date": "2026-10-18", "time": "10:30-11:00", "topic": "入席就座", "personnel": "引位组"},
        {"date": "2026-10-18", "time": "11:08-11:58", "topic": "婚礼仪式（交换戒指 / 证婚 / 交换誓言）", "personnel": "司仪 · 新人"},
        {"date": "2026-10-18", "time": "11:58-12:10", "topic": "双方家人合影", "personnel": "摄影组"},
        {"date": "2026-10-18", "time": "12:10-13:40", "topic": "婚宴午宴", "personnel": "全体宾客"},
        {"date": "2026-10-18", "time": "13:40-14:30", "topic": "敬酒环节", "personnel": "新人"},
        {"date": "2026-10-18", "time": "14:30-15:00", "topic": "互动游戏 · 抛手捧花 · 礼成送客（领伴手礼）", "personnel": "司仪 · 会务组"},
    ]})
    mod(db, site, "婚宴菜单", "rich_text", 4, "img-bule-5.png", rich_content=(
        "<p>婚宴午宴为<b>十二道式</b>，由云栖酒店行政总厨团队主理，菜品如下：</p>"
        + table(["类别", "菜品", "寓意"], [
            ["冷碟", "鸿运当头 · 锦绣冷盘", "红红火火"],
            ["热菜", "金牌乳猪拼盘", "金玉满堂"],
            ["热菜", "清蒸东星斑", "年年有余"],
            ["热菜", "波士顿龙虾二吃", "龙凤呈祥"],
            ["热菜", "白灼基围虾", "笑声连连"],
            ["热菜", "香菇扒菜心", "安居乐业"],
            ["汤羹", "花胶炖土鸡汤", "团圆美满"],
            ["点心", "红枣莲子羹 · 喜饼双拼", "早生贵子"],
            ["果盘", "时令水果拼盘", "甜甜蜜蜜"],
        ])
        + note("为儿童宾客备有儿童餐（需在回执中注明）；素食宾客请提前告知，将单独安排素宴席。")
    ))
    mod(db, site, "宾客回执", "registration_form", 5, "img-bule-6.png", form_config={
        "title": "宾客回执", "description": "请填写回执，便于我们安排席位与餐食",
        "buttonText": "提交回执", "allowEditAfterSubmit": True,
        "fields": [
            {"id": "g1", "type": "divider", "props": {"text": "基本信息"}},
            {"id": "name", "type": "text", "title": "姓名", "required": True, "placeholder": "请输入您的姓名"},
            {"id": "phone", "type": "phone", "title": "手机号", "required": True, "placeholder": "方便与您联系"},
            {"id": "attend", "type": "select", "title": "出席人数", "required": True,
             "options": ["1 位", "2 位", "携家人出席"]},
            {"id": "g2", "type": "divider", "props": {"text": "用餐与行程"}},
            {"id": "child", "type": "radio", "title": "是否携带儿童", "required": False,
             "options": ["不携带", "携带 1 名", "携带 2 名及以上"]},
            {"id": "diet", "type": "text", "title": "饮食禁忌", "required": False,
             "placeholder": "如忌口、过敏等，可不填"},
            {"id": "arrive", "type": "radio", "title": "到达方式", "required": True,
             "options": ["自驾", "地铁", "乘坐接驳车"]},
            {"id": "g3", "type": "divider", "props": {"text": "其他"}},
            {"id": "wish", "type": "textarea", "title": "祝福留言", "required": False,
             "placeholder": "写下您的祝福，婚礼当天会展示在大屏"},
            {"id": "agree", "type": "agreement", "title": "隐私同意", "required": True,
             "placeholder": "宾客信息使用说明",
             "props": {"agreementContent": "您填写的信息仅用于本次婚礼席位与餐食安排，婚礼结束后 30 天内删除。"}},
        ],
    })
    mod(db, site, "席位分布", "rich_text", 6, "img-bule-6.png", rich_content=(
        pic(urls["img_wedding_layout.png"], "婚宴场地座位分布")
        + table(["区域", "宾客", "桌位"], [
            ["A 区", "亲友（含主家席）", "1 - 8 桌"],
            ["B 区", "新郎同事", "9 - 14 桌"],
            ["C 区", "同学与朋友", "15 - 18 桌"],
        ])
        + "<p>提交回执后可在签到台查询具体桌位，引位员全程引导。</p>"
        + note("如需调整席位或有特殊需求，请联系婚宴管家：138-0000-0000（小周）。")
    ))
    mod(db, site, "交通与停车", "rich_text", 7, "img-bule-3.png", rich_content=(
        table(["方式", "说明"], [
            ["地铁", "6 号线「云栖站」C 口出，步行约 300 米"],
            ["自驾", "酒店地下停车场 B2 层，凭回执免费停车 4 小时"],
            ["出租车 / 网约车", "导航至「云栖酒店 · 宴会部」，宴会厅有独立落客区"],
        ])
        + "<h3>免费接驳车</h3>"
        + table(["班次", "时间"], [
            ["首班", "09:30（云栖地铁站 C 口）"],
            ["中间班次", "每 15 分钟一班（09:45 / 10:00 / 10:15 / 10:30）"],
            ["末班", "10:45"],
        ])
        + "<p>乘车点有「张伟 &amp; 李娜 婚礼接驳」指示牌；返程送客 14:30 起，坐满即走。</p>"
    ))
    mod(db, site, "住宿安排", "rich_text", 8, "img-bule-2.png", rich_content=(
        "<p>为外地宾客协调了两家协议酒店，预订时报「<b>张伟 &amp; 李娜 婚礼</b>」即享协议价：</p>"
        + table(["酒店", "距离", "协议价", "房型"], [
            ["云栖酒店（婚礼同址）", "宴会厅同址", "¥580 / 晚（双早）", "大床 / 双床"],
            ["全季酒店 · 云栖路店", "步行 12 分钟", "¥350 / 晚（双早）", "大床"],
        ])
        + note("协议价保留至 10 月 8 日，房间有限建议尽早预订；住宿疑问联系 小林 137-0000-0000。")
    ))
    mod(db, site, "着装建议", "rich_text", 9, "img-bule-4.png", rich_content=(
        "<h3>Dress Code</h3>"
        "<p>本次婚礼色调为<b>香槟金 + 莫兰迪绿</b>，欢迎您的穿搭与之呼应（不作强制要求）。</p>"
        + table(["宾客类型", "建议"], [
            ["女士", "连衣裙 / 套装，避免全白（留给新娘）与全黑"],
            ["男士", "西装或衬衫长裤，休闲得体即可"],
            ["小朋友", "舒适为主，现场有儿童座椅与亲子座位区"],
        ])
    ))
    mod(db, site, "婚礼工作组", "rich_text", 10, "img-trip-1.png", rich_content=(
        "<p>婚礼当天有任何问题，请随时联系工作组：</p>"
        + table(["分工", "负责人", "联系电话"], [
            ["总协调（席位 / 菜单 / 特殊需求）", "小周（婚宴管家）", "138-0000-0000"],
            ["接驳车与交通", "小陈", "139-0000-0000"],
            ["住宿与外地宾客接待", "小林", "137-0000-0000"],
        ])
        + note("婚礼当天上午 9 点后请优先拨打总协调电话；司仪台设在宴会厅正门左侧。")
    ))
    mod(db, site, "伴手礼", "rich_text", 11, "img-bule-8.png", rich_content=(
        "<p>我们为每位宾客准备了伴手礼一份，离场时在<b>签到台</b>凭回执领取：</p>"
        "<ul>"
        "<li>定制喜糖礼盒（含手工喜饼 6 枚）</li>"
        "<li>新人手写感谢卡一张</li>"
        "<li>迷你香薰蜡烛（自驾宾客建议放后备箱哦）</li>"
        "</ul>"
        + note("外地宾客如不便携带，可登记邮寄地址，我们礼成后统一寄出。")
    ))
    mod(db, site, "婚礼相册", "rich_text", 12, "img-bule-9.png", rich_content=(
        "<p>场地布置抢先看，婚礼当天的照片会持续更新到这里：</p>"
        + pic(urls["img_wedding_venue.png"], "宴会厅布置")
        + pic(urls["img_wedding_detail.png"], "桌花与喜糖伴手礼")
        + note("婚礼结束 3 天内更新全部精修照片；也可在签到台扫码加入宾客群，第一时间获取。")
    ))
    prune_extra(db, site)


def case_course(db, owner, urls):
    """少儿编程招生：公开访问 + 进阶路径图 + 分组试听预约表单"""
    site = ensure_site(
        db, owner, "少儿编程秋季班招生", "demo-course", "classic",
        layout="grid", kv_image=urls["kv_course.png"],
        share_title="少儿编程秋季班 · 火热报名中",
        share_subtitle="10 月 12 日开课，限额 20 人，免费试听预约",
        title_config={"enabled": False, "text": "少儿编程秋季班", "font": "sans",
                      "color": "#ffffff", "size": 22, "bold": True, "position": "center"},
    )
    mod(db, site, "课程介绍", "rich_text", 1, "img-bule-2.png", rich_content=(
        "<p>面向 6-15 岁少儿的编程课程体系，<b>小班教学，每班不超过 8 人</b>。</p>"
        + table(["办学数据", "—"], [
            ["办学年限", "7 年（2019 年创立）"],
            ["累计学员", "2600+ 人"],
            ["年度续费率", "87%"],
            ["授课老师", "均具有一线互联网公司研发经验"],
        ])
        + "<p>课程融合数学、逻辑与创意表达，让孩子在完成作品的过程中学会拆解问题、独立思考。</p>"
    ))
    mod(db, site, "课程进阶路径", "rich_text", 2, "img-bule-7.png", rich_content=(
        pic(urls["img_course_path.png"], "课程进阶路径")
        + "<p>三个阶段层层递进：先在图形化编程中建立兴趣与逻辑，再过渡到代码语言，"
        "最终走向算法竞赛。每个阶段结束都有作品展示日，家长可以现场看到孩子的产出。</p>"
    ))
    mod(db, site, "课程体系", "rich_text", 3, "img-bule-6.png", rich_content=(
        table(["班型", "适合年龄", "课时", "学习目标"], [
            ["Scratch 启蒙班", "6-8 岁", "16 课时", "图形化编程启蒙，完成 3 个动画小作品"],
            ["Python 进阶班", "9-11 岁", "20 课时", "掌握基础语法，独立完成一个小游戏"],
            ["C++ 竞赛班", "12-15 岁", "24 课时", "备战信息学奥赛（CSP-J/S），冲刺奖项"],
        ])
    ))
    mod(db, site, "教学环境", "rich_text", 4, "img-bule-2.png", rich_content=(
        pic(urls["img_course_room.png"], "文三路校区教室实拍")
        + table(["环境配置", "说明"], [
            ["班级教室", "4 间，每间限 8 个工位，单人单机"],
            ["设备", "全新联想笔记本 + 乐高 SPIKE 教具箱"],
            ["家长休息区", "独立休息区，直播屏可实时观看课堂"],
            ["安全", "全程录像，出入刷家长卡接送"],
        ])
        + note("欢迎随时到校区参观，报「微站预约」可优先安排顾问一对一讲解。")
    ))
    mod(db, site, "师资团队", "rich_text", 5, "img-bule-4.png", rich_content=(
        "<h3>王老师 · 教学主管</h3>"
        "<p>前电商平台资深研发，8 年少儿编程教学经验，Scratch 启蒙班主讲。</p>"
        "<h3>李老师 · Python 主讲</h3>"
        "<p>浙江大学计算机硕士，擅长把抽象概念讲成孩子听得懂的故事。</p>"
        "<h3>陈老师 · 竞赛教练</h3>"
        "<p>信息学奥赛金牌教练，近三年带出 CSP-J 一等奖 11 人。</p>"
    ))
    mod(db, site, "开班时间", "schedule", 6, "img-bule-1.png", schedule_config={"items": [
        {"date": "2026-10-12", "time": "周六 09:30-11:30", "topic": "Scratch 启蒙班（余 3 席）", "personnel": "王老师"},
        {"date": "2026-10-12", "time": "周六 14:00-16:00", "topic": "Python 进阶班（余 5 席）", "personnel": "李老师"},
        {"date": "2026-10-13", "time": "周日 09:30-11:30", "topic": "C++ 竞赛班（余 2 席）", "personnel": "陈老师"},
        {"date": "2026-10-13", "time": "周日 14:00-16:00", "topic": "Scratch 启蒙班 · 加开班（余 6 席）", "personnel": "王老师"},
    ]})
    mod(db, site, "免费试听预约", "registration_form", 7, "img-bule-5.png", form_config={
        "title": "免费试听预约", "description": "提交后顾问老师将在 1 个工作日内与您联系",
        "buttonText": "预约试听", "allowEditAfterSubmit": False,
        "fields": [
            {"id": "tip1", "type": "tip_text",
             "props": {"content": "试听课全程免费，每班每次仅开放 2 个名额，请提前预约", "tone": "info"}},
            {"id": "child", "type": "text", "title": "孩子姓名", "required": True, "placeholder": "孩子姓名或小名"},
            {"id": "age", "type": "select", "title": "孩子年龄", "required": True,
             "options": ["6-8 岁", "9-11 岁", "12 岁及以上"]},
            {"id": "phone", "type": "phone", "title": "家长手机", "required": True, "placeholder": "用于接收上课提醒"},
            {"id": "klass", "type": "select", "title": "意向班型", "required": True,
             "options": ["Scratch 启蒙班", "Python 进阶班", "C++ 竞赛班", "还没想好，请老师推荐"]},
            {"id": "slot", "type": "select", "title": "期望试听时间", "required": True,
             "options": ["周六上午", "周六下午", "周日上午", "周日下午"]},
            {"id": "base", "type": "radio", "title": "孩子编程基础", "required": False,
             "options": ["零基础", "学过图形化编程", "有代码基础"]},
            {"id": "remark", "type": "textarea", "title": "备注", "required": False,
             "placeholder": "孩子的兴趣、性格，或希望老师关注的地方"},
        ],
    })
    mod(db, site, "学费与优惠", "rich_text", 8, "img-bule-6.png", rich_content=(
        table(["班型", "课时", "原价", "秋季优惠价"], [
            ["Scratch 启蒙班", "16 课时", "¥3,200", "¥2,680"],
            ["Python 进阶班", "20 课时", "¥4,400", "¥3,680"],
            ["C++ 竞赛班", "24 课时", "¥6,000", "¥4,980"],
        ])
        + "<ul>"
        "<li><b>早鸟优惠：</b>10 月 1 日前报名立减 ¥300</li>"
        "<li><b>老带新：</b>推荐新学员双方各得 2 课时</li>"
        "<li><b>团报：</b>3 人成团每人再减 ¥200</li>"
        "</ul>"
        + note("以上优惠可与试听当天专属礼遇叠加；费用含全部教具与教材，无隐形消费。")
    ))
    mod(db, site, "报名须知", "rich_text", 9, "img-bule-8.png", rich_content=(
        "<ol>"
        "<li>每班限额 8 人，报满即止；试听名额每次课仅开放 2 个。</li>"
        "<li>秋季班共 16 次课，每周 1 次，每次 2 小时，逢法定节假日顺延。</li>"
        "<li>开课 7 天前可无理由全额退费；开课后按剩余课时退费。</li>"
        "<li>提供免费电脑，也可自带笔记本（推荐 2019 年后机型）。</li>"
        "<li>每 4 次课向家长同步一次学习报告（含课堂作品）。</li>"
        "</ol>"
    ))
    mod(db, site, "常见问题", "rich_text", 12, "img-bule-3.png", rich_content=(
        "<h3>孩子零基础能跟上吗？</h3>"
        "<p>可以。启蒙班专为零基础设计，前 4 次课不写任何代码，用积木式拖拽建立逻辑。</p>"
        "<h3>家长可以旁听吗？</h3>"
        "<p>第一次课欢迎旁听，之后建议让孩子独立上课，家长可在休息区通过直播屏观看。</p>"
        "<h3>错过一次课怎么办？</h3>"
        "<p>可预约平行班补课，或领取当次课的录像与练习包。</p>"
        "<h3>学完能达到什么水平？</h3>"
        "<p>启蒙班结业能独立完成动画与小游戏；进阶班结业能写出 200 行左右的完整程序；竞赛班以赛事奖项为目标。</p>"
        "<h3>可以只试听不报名吗？</h3>"
        "<p>可以，试听完全免费且无任何购课义务。</p>"
    ))
    mod(db, site, "校区地址", "external_link", 13, "img-bule-3.png",
        external_url="https://uri.amap.com/marker?position=120.12,30.28&name=文三路校区")
    prune_extra(db, site)
    mod(db, site, "学员成果", "rich_text", 10, "img-bule-7.png", rich_content=(
        "<p>上个学年学员的成果一览：</p>"
        + table(["成果", "数量", "说明"], [
            ["CSP-J/S 获奖学员", "23 人", "一等奖 11 人（陈老师竞赛班）"],
            ["完成完整作品", "180+ 件", "游戏、动画、小工具，结业日现场演示"],
            ["校内科技节获奖", "15 人次", "学员作品入选区级科技节展演"],
            ["续费 / 转介绍", "87% / 41%", "家长口碑是我们最大的获客来源"],
        ])
        + note("作品视频合集可在试听时现场演示，也可预约到校区体验学员作品。")
    ))
    mod(db, site, "家长口碑", "rich_text", 11, "img-bule-9.png", rich_content=(
        "<div style=\"background:#FFF7ED;border-left:4px solid #F59E0B;padding:10px 14px;border-radius:8px;margin:10px 0;font-size:14px;color:#9A3412;\">"
        "「孩子从坐不住到主动写代码，一学期变化太大了。」—— 三年级 · 乐乐妈妈</div>"
        "<div style=\"background:#FFF7ED;border-left:4px solid #F59E0B;padding:10px 14px;border-radius:8px;margin:10px 0;font-size:14px;color:#9A3412;\">"
        "「最喜欢每 4 次课的学习报告，能看到孩子每一步的成长。」—— 五年级 · 淘淘爸爸</div>"
        "<div style=\"background:#FFF7ED;border-left:4px solid #F59E0B;padding:10px 14px;border-radius:8px;margin:10px 0;font-size:14px;color:#9A3412;\">"
        "「竞赛班两年拿了一等奖，比我们预期高太多。」—— 初一 · 悦悦家长</div>"
        + note("更多评价可在大众点评「XX 少儿编程（文三路校区）」查看，4.9 分 / 326 条评价。")
    ))


def case_summit(db, owner, urls):
    """行业峰会：登录 + 多分论坛议程 + 多场次签到 + 实名报名 + 权限"""
    site = ensure_site(
        db, owner, "2026 数字零售行业峰会", "demo-summit", "dark",
        layout="button", kv_image=urls["kv_summit.png"],
        need_login=True, need_checkin=True,
        share_title="2026 数字零售行业峰会",
        share_subtitle="10.24-10.25 上海 · 议程 / 嘉宾 / 报名",
        title_config={"enabled": False, "text": "2026 数字零售行业峰会", "font": "sans",
                      "color": "#ffffff", "size": 20, "bold": True, "position": "center"},
    )
    mod(db, site, "峰会介绍", "rich_text", 1, "img-bule-2.png", rich_content=(
        "<p>由市零售行业协会主办的年度行业峰会，聚焦<b>数字零售、私域运营与 AI 应用</b>三大议题。</p>"
        + table(["基本信息", "—"], [
            ["时间", "2026 年 10 月 24 日 - 25 日"],
            ["地点", "上海国际会议中心 · 3F"],
            ["规模", "主论坛 600 人 + 双分论坛各 100 人"],
            ["参会对象", "品牌方、零售企业、平台与服务商"],
        ])
        + note("往届峰会到场率 92%，本届实行实名制入场，报名后需审核。")
    ))
    mod(db, site, "主论坛议程", "schedule", 2, "img-bule-1.png", schedule_config={"items": [
        {"date": "2026-10-24", "time": "09:00-09:30", "topic": "签到入场", "personnel": "会务组"},
        {"date": "2026-10-24", "time": "09:30-10:10", "topic": "开幕致辞：零售数字化的下一个五年", "personnel": "协会理事长"},
        {"date": "2026-10-24", "time": "10:10-11:40", "topic": "主旨演讲：AI 重构人货场", "personnel": "头部平台副总裁"},
        {"date": "2026-10-24", "time": "11:40-12:00", "topic": "《2026 数字零售白皮书》发布", "personnel": "研究院"},
        {"date": "2026-10-24", "time": "14:00-15:30", "topic": "圆桌对话：全域经营的增长拐点", "personnel": "4 位品牌嘉宾"},
        {"date": "2026-10-24", "time": "15:30-16:30", "topic": "年度案例颁奖 · 自由交流", "personnel": "全体"},
    ]})
    mod(db, site, "分论坛议程", "schedule", 3, "img-bule-6.png", schedule_config={"items": [
        {"date": "2026-10-25", "time": "09:30-11:30", "topic": "A 厅：零售数字化落地路径（案例专场）", "personnel": "A 厅"},
        {"date": "2026-10-25", "time": "09:30-11:30", "topic": "B 厅：私域增长实战工坊（演练）", "personnel": "B 厅"},
        {"date": "2026-10-25", "time": "13:30-15:00", "topic": "A 厅：门店数字化 100 个细节", "personnel": "A 厅"},
        {"date": "2026-10-25", "time": "13:30-15:00", "topic": "B 厅：会员运营方法论专场", "personnel": "B 厅"},
    ]})
    mod(db, site, "嘉宾阵容", "rich_text", 4, "img-bule-7.png", rich_content=(
        "<h3>主论坛嘉宾（部分）</h3>"
        "<p><b>某头部电商平台 副总裁</b> ——《AI 重构人货场》</p>"
        "<p><b>某连锁超市 CIO</b> ——《门店数字化的 100 个细节》</p>"
        "<p><b>某新消费品牌 增长负责人</b> ——《私域 2.0：从流量到留量》</p>"
        "<p><b>某产业研究院 院长</b> ——《2026 数字零售白皮书》解读</p>"
        + note("更多嘉宾持续更新中，最终议程以现场为准。")
    ))
    mod(db, site, "会场导览", "rich_text", 5, "img-bule-3.png", rich_content=(
        pic(urls["img_summit_venue.png"], "3F 会场导览")
        + "<p>签到区设在扶梯口，凭「我的二维码」核销入场；分论坛 A / B 厅需分别核销，请留意场次时间。</p>"
    ))
    mod(db, site, "参会报名", "registration_form", 6, "img-bule-5.png", form_config={
        "title": "参会报名", "description": "实名制报名，审核通过后将收到短信通知",
        "buttonText": "提交报名", "allowEditAfterSubmit": True,
        "fields": [
            {"id": "g1", "type": "divider", "props": {"text": "参会人信息"}},
            {"id": "name", "type": "text", "title": "姓名", "required": True, "placeholder": "与身份证一致"},
            {"id": "phone", "type": "phone", "title": "手机号", "required": True, "placeholder": "接收审核与参会短信"},
            {"id": "idcard", "type": "idcard", "title": "身份证号", "required": True,
             "placeholder": "用于会场实名核验，仅入场使用"},
            {"id": "company", "type": "text", "title": "公司", "required": True, "placeholder": "公司全称"},
            {"id": "job", "type": "text", "title": "职务", "required": False, "placeholder": "如：运营总监"},
            {"id": "g2", "type": "divider", "props": {"text": "参会安排"}},
            {"id": "forum", "type": "checkbox", "title": "拟参加分论坛（可多选）", "required": True,
             "options": ["A：零售数字化", "B：私域增长"]},
            {"id": "dinner", "type": "radio", "title": "是否参加交流晚宴", "required": True,
             "options": ["参加", "不参加"]},
            {"id": "arrive", "type": "date", "title": "预计到达日期", "required": False},
            {"id": "tip1", "type": "tip_text",
             "props": {"content": "提交后 3 个工作日内完成审核，审核结果将以短信通知", "tone": "warning"}},
        ],
    })
    mod(db, site, "交通指引", "rich_text", 7, "img-bule-3.png", rich_content=(
        table(["方式", "说明"], [
            ["地铁", "2 号线「陆家嘴站」1 号口，步行约 5 分钟"],
            ["自驾", "会议中心地下停车场，参会凭证件免费"],
            ["机场", "浦东机场乘 2 号线直达，约 50 分钟；虹桥机场乘 2 号线，约 40 分钟"],
            ["高铁", "上海虹桥站乘 2 号线至陆家嘴站"],
        ])
    ))
    mod(db, site, "周边住宿", "rich_text", 8, "img-bule-8.png", rich_content=(
        "<p>以下酒店报「数字零售峰会」享协议价（数量有限，建议提前预订）：</p>"
        + table(["酒店", "协议价", "距会场"], [
            ["江景大酒店（五星）", "¥680 / 晚", "500 米"],
            ["商务酒店（四星）", "¥420 / 晚", "1.2 公里"],
            ["青年公寓", "¥220 / 晚", "800 米"],
        ])
    ))
    mod(db, site, "餐饮安排", "rich_text", 9, "img-bule-6.png", rich_content=(
        "<p><b>午餐：</b>10 月 24 日为全体参会嘉宾提供自助午餐（凭胸卡就餐）；25 日午餐自理，会场周边餐饮地图见「会场导览」。</p>"
        "<p><b>茶歇：</b>上午 / 下午各一场，设于茶歇区，提供咖啡、茶与点心。</p>"
        "<p><b>交流晚宴：</b>10 月 24 日 18:30，江景厅（报名时选择参加，凭胸卡入场）。</p>"
    ))
    mod(db, site, "参展与赞助", "rich_text", 10, "img-bule-6.png", rich_content=(
        "<p>本届峰会开放<b>展位与赞助</b>合作，面向零售品牌、SaaS 服务商与解决方案商：</p>"
        + table(["合作档位", "名额", "权益概要", "价格"], [
            ["钻石合作", "1 家", "开幕致辞前品牌展示 + 主论坛演讲 15 分钟 + 双人晚宴", "¥88,000"],
            ["金牌合作", "3 家", "分论坛演讲 10 分钟 + 展位 1 个 + 双人晚宴", "¥38,000"],
            ["展位合作", "8 家", "会场展位 1 个（3m×2m）+ 单人晚宴", "¥12,800"],
        ])
        + note("合作详案与权益明细请联系会务组：021-6000-0000（王女士），额满即止。")
    ))
    mod(db, site, "会议须知", "rich_text", 11, "img-bule-4.png", rich_content=(
        "<ol>"
        "<li>请携带名片办理签到；电子凭证在「我的二维码」中查看。</li>"
        "<li>主论坛与分论坛需分别核销签到，请留意场次时间。</li>"
        "<li>实名制入场，身份证信息仅用于会场核验，会后 7 天内删除。</li>"
        "<li>会议全程禁止直播录播，允许个人拍照记录。</li>"
        "<li>如无法出席，请至少提前 3 天告知会务组，以便释放名额。</li>"
        "</ol>"
    ))
    mod(db, site, "往届回顾", "rich_text", 12, "img-bule-2.png", rich_content=(
        "<p>2025 峰会现场：</p>"
        + pic(urls["img_summit_past.png"], "2025 峰会主论坛现场")
        + table(["往届数据", "2025 峰会"], [
            ["参会人数", "480 人（到场率 92%）"],
            ["参会企业", "260 家（品牌方 / 零售商 / 服务商）"],
            ["演讲嘉宾", "28 位"],
            ["满意度", "4.7 / 5（会后问卷回收 312 份）"],
        ])
        + note("2025 峰会全部演讲视频已整理成合集，报名本届可免费获取回放权限。")
    ))
    mod(db, site, "我的二维码", "qrcode", 13, "img-bule-9.png", qrcode_config={
        "hint": "现场出示此二维码，由工作人员扫码完成签到入场",
        "display_fields": ["username", "nickname"],
    })
    prune_extra(db, site)
    add_checkin(db, site, ["主论坛签到（10.24）", "分论坛签到（10.25）"])
    add_accounts(db, site, [
        ("vip001", "王总（VIP）", None),
        ("guest001", "李参会", ["峰会介绍", "主论坛议程", "会议须知", "我的二维码"]),
    ])


def case_annual(db, owner, urls):
    """企业年会：登录 + 奖项图 + 多选节目报名 + 权限悬念"""
    site = ensure_site(
        db, owner, "同心同行 · 2026 公司年会", "demo-annual", "festive",
        layout="button", kv_image=urls["kv_annual.png"],
        need_login=True, need_checkin=True,
        share_title="同心同行 · 2026 公司年会",
        share_subtitle="2027.01.16 星河宴会厅，不见不散",
        title_config={"enabled": False, "text": "同心同行 · 2026 公司年会", "font": "sans",
                      "color": "#ffffff", "size": 20, "bold": True, "position": "center"},
    )
    mod(db, site, "年会通知", "rich_text", 1, "img-bule-2.png", rich_content=(
        "<p>2026 年度总结表彰暨 2027 迎新年会，定于 <b>2027 年 1 月 16 日（周六）</b>举行。</p>"
        + table(["项目", "信息"], [
            ["时间", "17:30 入场 / 18:00 正式开始"],
            ["地点", "星河宴会厅 · 2 层"],
            ["班车", "17:00 园区南门发车，21:45 返程"],
            ["着装", "无强制要求，红金色系更应景"],
        ])
        + note("今年特设「年度之星」颁奖与三轮抽奖，请务必在 1 月 10 日前提交出席回执。")
    ))
    mod(db, site, "年会议程", "schedule", 2, "img-bule-1.png", schedule_config={"items": [
        {"date": "2027-01-16", "time": "17:30-18:00", "topic": "签到入场 · 合影打卡", "personnel": "行政组"},
        {"date": "2027-01-16", "time": "18:00-18:20", "topic": "开场表演 + CEO 致辞", "personnel": "管理层"},
        {"date": "2027-01-16", "time": "18:20-19:00", "topic": "年度颁奖（年度之星 / 最佳团队）", "personnel": "HR"},
        {"date": "2027-01-16", "time": "19:00-20:00", "topic": "晚宴", "personnel": "全体"},
        {"date": "2027-01-16", "time": "20:00-21:30", "topic": "三轮抽奖 + 员工节目", "personnel": "主持人"},
        {"date": "2027-01-16", "time": "21:30", "topic": "大合影 · 礼成", "personnel": "全体"},
    ]})
    mod(db, site, "奖项与奖品", "rich_text", 3, "img-bule-6.png", rich_content=(
        pic(urls["img_annual_awards.png"], "年度奖项与奖品")
        + "<p>奖项由各部门推荐 + 管理层评审产生，获奖名单将在颁奖环节现场揭晓。</p>"
    ))
    mod(db, site, "出席回执", "registration_form", 4, "img-bule-5.png", form_config={
        "title": "年会出席回执", "description": "请于 1 月 10 日前提交，便于安排桌位与餐食",
        "buttonText": "提交回执", "allowEditAfterSubmit": True,
        "fields": [
            {"id": "name", "type": "text", "title": "姓名", "required": True, "placeholder": "请输入姓名"},
            {"id": "dept", "type": "select", "title": "部门", "required": True,
             "options": ["研发", "产品", "市场", "销售", "职能"]},
            {"id": "phone", "type": "phone", "title": "手机号", "required": True, "placeholder": "接收年会提醒"},
            {"id": "guests", "type": "radio", "title": "是否携带家属", "required": True,
             "options": ["不携带", "携带 1 位", "携带 2 位"]},
            {"id": "shows", "type": "checkbox", "title": "想看的节目类型（可多选，供主持人串场参考）",
             "required": False, "options": ["唱歌", "舞蹈", "小品 / 相声", "乐器", "游戏互动"]},
            {"id": "diet", "type": "text", "title": "饮食备注", "required": False, "placeholder": "忌口 / 素食等"},
        ],
    })
    mod(db, site, "交通与班车", "rich_text", 5, "img-bule-3.png", rich_content=(
        table(["方式", "说明"], [
            ["园区班车", "17:00 南门发车，21:45 返程（回执中登记过才有座位）"],
            ["自驾", "星河宴会厅地下停车场，凭年会电子凭证免费"],
            ["地铁", "5 号线「星河站」B 口，步行 600 米"],
        ])
    ))
    mod(db, site, "桌位安排", "rich_text", 6, "img-bule-2.png", rich_content=(
        "<p>晚宴共 <b>32 桌</b>，按部门大区入座，跨部门交流可现场找行政组调换：</p>"
        + table(["区域", "部门", "桌位"], [
            ["主桌区", "管理层 + 年度之星", "1 - 3 桌"],
            ["东区", "研发 / 产品", "4 - 15 桌"],
            ["西区", "市场 / 销售", "16 - 27 桌"],
            ["家庭区", "携家属同事专属", "28 - 32 桌（近舞台与儿童角）"],
        ])
        + note("具体桌号以签到台桌位图为准；家属席位已在回执中预留，无需额外申请。")
    ))
    mod(db, site, "节目征集", "rich_text", 7, "img-bule-7.png", rich_content=(
        "<p>年会舞台虚位以待！欢迎个人 / 组合 / 部门报名节目：</p>"
        "<ul>"
        "<li>形式不限：唱歌、舞蹈、小品、乐器、魔术、脱口秀……</li>"
        "<li>入选节目组全员额外获得「神秘道具」一份</li>"
        "<li>报名截止：1 月 5 日，联系行政组 小林（分机 8021）</li>"
        "</ul>"
        + note("彩排时间：1 月 14 日 14:00-18:00，地点为公司一层多功能厅。")
    ))
    mod(db, site, "抽奖规则", "rich_text", 8, "img-bule-6.png", rich_content=(
        "<p>今年共 <b>三轮抽奖</b>，凭工牌号自动参与，需本人在场（缺席视为放弃）：</p>"
        + table(["轮次", "开奖时间", "奖项", "名额"], [
            ["第一轮 · 幸运奖", "19:40", "小米充电宝 + 咖啡月卡", "30 名"],
            ["第二轮 · 优享奖", "20:30", "戴森吹风机 / Switch 游戏机（二选一）", "8 名"],
            ["第三轮 · 终极大奖", "21:10", "iPhone 17（1 名）+ 额外 3 天年假", "4 名"],
        ])
        + "<ul>"
        "<li>连续中奖自动顺延至下一轮重新抽取，让更多人带奖回家</li>"
        "<li>「年度之星」获奖者额外拥有终极大奖双倍中奖权重</li>"
        "<li>奖品现场领取，异地同事由行政统一邮寄</li>"
        "</ul>"
        + note("去年锦鲤是研发部老王——今年他主动申请当了抽奖嘉宾（合规起见）。")
    ))
    mod(db, site, "往年年会回顾", "rich_text", 9, "img-baier-7.jpg", rich_content=(
        "<p>2025 年会现场：</p>"
        + pic(urls["img_annual_stage.png"], "2025 年会舞台")
        + table(["2025 年会数据", "—"], [
            ["现场人数", "286 人（含家属 41 位）"],
            ["员工节目", "14 个（投票冠军：销售部《销售风云》小品）"],
            ["抽奖奖品总值", "¥42,000"],
        ])
        + note("2025 年会完整相册已同步到公司网盘「文化活动」目录，可自行下载。")
    ))
    mod(db, site, "年会工作组", "rich_text", 11, "img-trip-1.png", rich_content=(
        "<p>年会当天有任何问题（桌位 / 设备 / 特殊需求），找对人不绕弯：</p>"
        + table(["分工", "负责人", "联系方式"], [
            ["总协调（流程 / 桌位）", "行政组 小林", "分机 8021 / 138-0000-0000"],
            ["节目与彩排", "文化专员 阿哲", "分机 8033"],
            ["抽奖与奖品", "HR 小雨", "分机 8012"],
            ["摄影与直播", "品牌部 大鹏", "分机 8055"],
        ])
        + note("1 月 14 日 14:00-18:00 全要素彩排，当晚 20:00 后禁止占用舞台试音。")
    ))
    mod(db, site, "我的二维码", "qrcode", 12, "img-bule-9.png", qrcode_config={
        "hint": "入场时出示此二维码，工作人员扫码核销",
        "display_fields": ["username", "nickname"],
    })
    mod(db, site, "节目单（神秘）", "rich_text", 10, "img-bule-4.png", rich_content=(
        "<p>节目单保密中！仅对管理团队可见，年会当天对全员开放。</p>"
        "<p>小提示：今年有部门重量级节目回归，还有一个大家都想不到的开场。</p>"
    ))
    prune_extra(db, site)
    add_checkin(db, site, ["入场签到", "晚宴签到"])
    add_accounts(db, site, [
        ("vip001", "张总监", None),
        ("staff001", "陈员工", ["年会通知", "年会议程", "奖项与奖品", "出席回执", "桌位安排",
                            "交通与班车", "节目征集", "抽奖规则", "往年年会回顾",
                            "年会工作组", "我的二维码"]),
    ])


def case_store(db, owner, urls):
    """门店会员日：背景图风格 + 福利图 + 常住区域字段 + 定时开关"""
    now = utcnow()
    site = ensure_site(
        db, owner, "星空咖啡 · 会员日", "demo-store", "default",
        layout="button", kv_image="", background_image=urls["bg_store.png"],
        start_time=now - timedelta(days=7), end_time=now + timedelta(days=30),
        share_title="星空咖啡 · 会员日",
        share_subtitle="10.01-10.07 全场第二杯半价",
        title_config={"enabled": False, "text": "星空咖啡 · 会员日", "font": "sans",
                      "color": "#ffffff", "size": 22, "bold": True, "position": "center"},
    )
    mod(db, site, "活动介绍", "rich_text", 1, "img-trip-5.png", rich_content=(
        "<p>星空咖啡一年一度的<b>会员日</b>来了！10 月 1 日 - 7 日，全国 12 家门店同步进行。</p>"
        "<p>会员到店出示会员码，即可享受本次活动全部福利；还不是会员？在下方「加入会员」30 秒完成注册。</p>"
        + note("本活动页将在活动结束后自动关闭——由系统按时间自动控制，无需人工操作。")
    ))
    mod(db, site, "会员日福利", "rich_text", 2, "img-trip-1.png", rich_content=(
        pic(urls["img_store_perks.png"], "会员日福利一览")
        + "<p>福利可与会员积分折扣叠加使用，单笔订单最多叠加两重福利。</p>"
    ))
    mod(db, site, "活动日历", "schedule", 3, "img-trip-4.png", schedule_config={"items": [
        {"date": "2026-10-01", "time": "10:00-22:00", "topic": "会员日开幕 · 手冲品鉴会", "personnel": "A 店"},
        {"date": "2026-10-03", "time": "14:00-16:00", "topic": "拉花体验课（需预约，限 12 人）", "personnel": "B 店"},
        {"date": "2026-10-05", "time": "15:00-17:00", "topic": "亲子咖啡渣盆栽 DIY", "personnel": "C 店"},
        {"date": "2026-10-07", "time": "19:00-21:00", "topic": "会员日晚会 · 年度锦鲤抽奖", "personnel": "旗舰店"},
    ]})
    mod(db, site, "明星产品", "rich_text", 4, "img-trip-8.png", rich_content=(
        pic(urls["img_store_products.png"], "会员日明星产品")
        + table(["产品", "会员日价", "推荐理由"], [
            ["桂花拿铁（秋日限定）", "¥22（原 ¥32）", "桂花蜜现熬，每天限量 60 杯"],
            ["经典燕麦拿铁", "¥19（原 ¥28）", "连续 3 年销量第一"],
            ["冷萃耶加雪菲", "¥25（原 ¥36）", "会员日限定冰滴版本"],
            ["海盐芝士厚乳", "¥20（原 ¥30）", "第二杯半价首选"],
        ])
    ))
    mod(db, site, "会员等级", "rich_text", 5, "img-trip-1.png", rich_content=(
        "<p>会员分三级，按近 12 个月累计消费自动升级，权益自动生效：</p>"
        + table(["等级", "升级条件", "专属权益"], [
            ["银卡", "注册即享", "积分抵现 + 生日礼"],
            ["金卡", "年消费 ≥ ¥1,500", "全场 95 折 + 每月 1 张升杯券 + 新品品鉴优先"],
            ["黑金卡", "年消费 ≥ ¥4,000", "金卡权益 + 免费手冲课 2 次 + 专属客服"],
        ])
        + note("会员日期间消费按 1.5 倍累计等级成长值，升级更快。")
    ))
    mod(db, site, "会员权益", "rich_text", 6, "img-trip-1.png", rich_content=(
        "<ul>"
        "<li><b>积分体系：</b>消费 1 元 = 1 积分，积分可抵现（100 积分 = 5 元）</li>"
        "<li><b>生日礼：</b>生日当月免费饮品一杯 + 8 折券一张</li>"
        "<li><b>升杯券：</b>每消费满 10 次自动发放</li>"
        "<li><b>专属活动：</b>会员日、新品品鉴会优先报名</li>"
        "</ul>"
    ))
    mod(db, site, "加入会员", "registration_form", 7, "img-trip-9.png", form_config={
        "title": "加入会员", "description": "填写信息即视为注册会员，福利立即生效",
        "buttonText": "立即加入", "allowEditAfterSubmit": True,
        "fields": [
            {"id": "name", "type": "text", "title": "姓名", "required": True, "placeholder": "请输入姓名"},
            {"id": "phone", "type": "phone", "title": "手机号", "required": True, "placeholder": "会员号与手机号一致"},
            {"id": "birth", "type": "select", "title": "出生月份", "required": True,
             "options": [f"{m} 月" for m in range(1, 13)]},
            {"id": "store", "type": "select", "title": "常去门店", "required": True,
             "options": ["星空咖啡 · A 店", "星空咖啡 · B 店", "星空咖啡 · C 店", "旗舰店"]},
            {"id": "area", "type": "region", "title": "常住区域", "required": False},
            {"id": "hobby", "type": "checkbox", "title": "偏好（可多选，用于新品推荐）", "required": False,
             "options": ["拿铁系列", "手冲单品", "甜品", "轻食", "周边产品"]},
        ],
    })
    mod(db, site, "门店列表", "rich_text", 8, "img-trip-4.png", rich_content=(
        "<p>全国 12 家直营门店（部分展示），会员日福利全门店通用：</p>"
        + table(["门店", "地址", "营业时间", "活动专场"], [
            ["旗舰店", "文三路 88 号星空广场 1F", "07:30-22:30", "年度锦鲤抽奖（10.7）"],
            ["A 店 · 西溪店", "西溪印象城 2F", "08:00-22:00", "手冲品鉴会（10.1）"],
            ["B 店 · 滨江店", "滨盛路 1870 号", "08:00-21:30", "拉花体验课（10.3）"],
            ["C 店 · 城西银泰店", "城西银泰城 1F", "09:00-22:00", "亲子 DIY（10.5）"],
        ])
        + note("其余 8 家门店信息可在小程序「门店」页查看；各店活动名额以门店公告为准。")
    ))
    mod(db, site, "门店导航", "external_link", 9, "img-trip-7.png",
        external_url="https://uri.amap.com/marker?position=120.15,30.27&name=星空咖啡旗舰店")
    mod(db, site, "常见问题", "rich_text", 10, "img-trip-5.png", rich_content=(
        "<h3>会员日福利所有门店都能用吗？</h3>"
        "<p>是，全国 12 家门店通用；拉花课等专场活动以对应门店为准。</p>"
        "<h3>第二杯半价可以和积分折扣叠加吗？</h3>"
        "<p>可以，单笔订单最多叠加两重福利，收银台会自动计算最优组合。</p>"
        "<h3>会员码在哪里看？</h3>"
        "<p>注册成功后短信会发专属链接，到店出示即可；也可以收藏本微站随时打开。</p>"
        "<h3>会员收费吗？</h3>"
        "<p>注册免费，充值返利活动期间额外赠送。</p>"
    ))
    mod(db, site, "品牌介绍", "rich_text", 11, "img-trip-8.png", rich_content=(
        "<p><b>星空咖啡</b>创立于 2019 年，专注「好咖啡，日常价」。目前在全国拥有 12 家直营门店，"
        "自有烘焙工厂，豆子从产区直采。</p>"
        "<p>我们相信一杯好咖啡不该有门槛——这也是会员日存在的意义。</p>"
    ))
    mod(db, site, "咖啡课堂", "rich_text", 12, "img-trip-9.png", rich_content=(
        "<h3>在家也能冲出一杯好咖啡</h3>"
        + table(["步骤", "要点", "常见失误"], [
            ["称豆", "15g 豆 / 225g 水（1:15）", "凭手感估量，浓度忽高忽低"],
            ["研磨", "中细研磨（白砂糖颗粒感）", "磨太细导致过萃发苦"],
            ["注水", "分三段注入，总时长 2 分 30 秒", "一次性倒满水，萃取不均"],
            ["水温", "92℃（浅烘 94℃ / 深烘 90℃）", "刚烧开就冲，烫出焦苦味"],
        ])
        + note("想系统学习？会员日「拉花体验课」10 月 3 日 B 店开课，金卡以上会员免费，限 12 人。")
    ))
    prune_extra(db, site)


def case_chamber(db, owner, urls):
    """协会换届大会：登录 + 组织架构图 + 资料附件 + 住宿安排"""
    site = ensure_site(
        db, owner, "青年企业家协会换届大会", "demo-chamber", "default",
        layout="grid", kv_image=urls["kv_chamber.png"],
        need_login=True, need_checkin=True,
        share_title="青年企业家协会换届大会",
        share_subtitle="2026.11.08 市会议中心 A 厅",
        title_config={"enabled": False, "text": "青年企业家协会换届大会", "font": "sans",
                      "color": "#ffffff", "size": 20, "bold": True, "position": "center"},
    )
    now_iso = utcnow().isoformat(timespec="seconds") + "Z"

    def att(fname, title, url, ext, category, size):
        return {"id": str(uuid.uuid4()), "name": fname, "title": title, "url": url,
                "size": size, "ext": ext, "category": category, "uploaded_at": now_iso}

    mod(db, site, "会议通知", "rich_text", 1, "img-baier-4.jpg", rich_content=(
        "<p>青年企业家协会第四届会员大会（换届大会）定于 <b>2026 年 11 月 8 日</b>召开。</p>"
        + table(["项目", "信息"], [
            ["时间", "13:30 签到 / 14:00 正式开始"],
            ["地点", "市会议中心 A 厅（二层）"],
            ["议程", "审议工作报告 · 换届选举 · 新任会长讲话"],
            ["参会对象", "全体会员（含单位会员代表 1-2 名）"],
        ])
        + note("请全体会员于 11 月 5 日前提交参会回执，便于秘书处安排席位与选票。")
    ))
    mod(db, site, "大会议程", "schedule", 2, "img-bule-1.png", schedule_config={"items": [
        {"date": "2026-11-08", "time": "13:30-14:00", "topic": "会员签到 · 领取会议材料", "personnel": "秘书处"},
        {"date": "2026-11-08", "time": "14:00-14:20", "topic": "开幕 · 特邀嘉宾致辞", "personnel": "市工商联"},
        {"date": "2026-11-08", "time": "14:20-15:20", "topic": "第二届理事会工作报告 · 财务报告", "personnel": "理事会"},
        {"date": "2026-11-08", "time": "15:30-16:40", "topic": "换届选举（无记名投票）", "personnel": "全体会员"},
        {"date": "2026-11-08", "time": "16:40-17:00", "topic": "新任会长就职讲话 · 大合影", "personnel": "全体"},
        {"date": "2026-11-08", "time": "17:30-20:00", "topic": "答谢晚宴（需回执确认）", "personnel": "全体"},
    ]})
    mod(db, site, "组织架构", "rich_text", 3, "img-baier-3.jpg", rich_content=(
        pic(urls["img_chamber_org.png"], "协会组织架构")
        + "<p>协会实行会员大会制度，理事会为执行机构，秘书处负责日常运营，下设三个专门委员会。</p>"
    ))
    mod(db, site, "选举办法", "rich_text", 4, "img-baier-1.jpg", rich_content=(
        "<p>本次换届选举依据《协会章程（第三届）》执行，要点如下：</p>"
        + table(["事项", "办法"], [
            ["选举方式", "无记名投票，等额选举（15 名候选人）"],
            ["有效票", "实到会员 2/3 以上出席方可开票"],
            ["当选条件", "同意票超过到会会员半数即当选"],
            ["监票 / 计票", "监事会 3 人监票，秘书处 2 人计票，现场唱票"],
            ["异议处理", "对候选人或程序有异议，11 月 3 日前书面提交秘书处"],
        ])
        + note("因故不能到会的会员可办理委托投票（1 人最多代 1 票），11 月 6 日前向秘书处备案。")
    ))
    mod(db, site, "候选人名单", "rich_text", 5, "img-bule-7.png", rich_content=(
        "<p><b>第三届理事会候选人（15 名，等额选举）</b>（按姓氏笔画排序）</p>"
        + table(["姓名", "单位", "拟任职务"], [
            ["王某某", "某某科技有限公司", "会长（候选人）"],
            ["冯某某", "某某控股集团", "副会长（候选人）"],
            ["刘某某", "某某智能制造", "副会长（候选人）"],
            ["许某某", "某某律所", "理事（候选人）"],
            ["……", "……", "……"],
        ])
        + note("候选人详细简介见「会议资料」附件；对候选人有异议可在 11 月 3 日前书面反馈秘书处。")
    ))
    mod(db, site, "参会回执", "registration_form", 6, "img-bule-5.png", form_config={
        "title": "参会回执", "description": "请全体会员于 11 月 5 日前提交",
        "buttonText": "提交回执", "allowEditAfterSubmit": True,
        "fields": [
            {"id": "g1", "type": "divider", "props": {"text": "会员信息"}},
            {"id": "name", "type": "text", "title": "姓名", "required": True, "placeholder": "请输入姓名"},
            {"id": "phone", "type": "phone", "title": "手机号", "required": True, "placeholder": "接收会议通知"},
            {"id": "company", "type": "text", "title": "单位", "required": True, "placeholder": "单位全称"},
            {"id": "job", "type": "text", "title": "职务", "required": True, "placeholder": "如：总经理"},
            {"id": "g2", "type": "divider", "props": {"text": "参会安排"}},
            {"id": "dinner", "type": "radio", "title": "是否出席答谢晚宴", "required": True,
             "options": ["出席", "不出席"]},
            {"id": "hotel", "type": "radio", "title": "是否需要协助预订住宿", "required": False,
             "options": ["需要", "不需要"]},
            {"id": "arrive", "type": "time", "title": "预计到达时间", "required": False},
            {"id": "remark", "type": "textarea", "title": "备注", "required": False,
             "placeholder": "特殊需求、随行人员等"},
        ],
    })
    mod(db, site, "会议资料", "file_attachment", 7, "img-baier-2.jpg", form_config={
        "files": [
            att("协会章程（第三届）.pdf", "协会章程（第三届）", urls["doc_charter.pdf"],
                "pdf", "document", os.path.getsize(os.path.join(ASSET_DIR, "doc_charter.pdf"))),
            att("大会主视觉.png", "大会主视觉（可直接转发）", urls["kv_chamber.png"],
                "png", "image", os.path.getsize(os.path.join(ASSET_DIR, "kv_chamber.png"))),
            att("协会组织架构.png", "协会组织架构图", urls["img_chamber_org.png"],
                "png", "image", os.path.getsize(os.path.join(ASSET_DIR, "img_chamber_org.png"))),
        ],
    })
    mod(db, site, "住宿安排", "rich_text", 8, "img-bule-8.png", rich_content=(
        "<p>为外地会员协调了两家协议酒店，预订时报「<b>青企协换届大会</b>」即享协议价：</p>"
        + table(["酒店", "距离", "协议价", "房型"], [
            ["会议中心大酒店", "会场同址", "¥520 / 晚（双早）", "大床 / 双床"],
            ["格林豪泰 · 会展路店", "车程 8 分钟", "¥280 / 晚（双早）", "大床"],
        ])
        + note("11 月 5 日前预订可确保留房；如需秘书处代订，请在参会回执中勾选「需要协助预订住宿」。")
    ))
    mod(db, site, "会议纪律", "rich_text", 9, "img-baier-1.jpg", rich_content=(
        "<ol>"
        "<li>请凭「我的二维码」签到，领取会议材料与选票。</li>"
        "<li>选举环节采用无记名投票，请服从监票人安排。</li>"
        "<li>会议期间请将手机调至静音，摄影请关闭闪光灯。</li>"
        "<li>如需请假，请提前向秘书处报备（视为弃权，不影响会员资格）。</li>"
        "</ol>"
    ))
    mod(db, site, "交通指引", "rich_text", 10, "img-bule-3.png", rich_content=(
        table(["方式", "说明"], [
            ["地铁", "1 号线「会议中心站」D 口，直达负一层"],
            ["自驾", "会议中心 P1 / P2 停车场，凭回执码 3 小时免费"],
            ["接驳车", "14:00 前「协会办事处」有专车接送，需在回执备注中登记"],
        ])
    ))
    mod(db, site, "往届回顾", "rich_text", 11, "img-baier-7.jpg", external_url=None, rich_content=(
        "<p>第二届理事会五年工作剪影：</p>"
        + pic(urls["img_chamber_hall.png"], "市会议中心（本届大会举办地）")
        + table(["五年工作成果", "数据"], [
            ["会员规模", "从 86 家增长至 214 家"],
            ["政企对接活动", "46 场（累计促成合作意向 ¥3.2 亿）"],
            ["公益投入", "助学 / 抗疫捐赠累计 ¥580 万"],
            ["获得荣誉", "市「5A 级社会组织」"],
        ])
        + note("五年工作完整报告见「会议资料」附件《第二届理事会工作报告》。")
    ))
    mod(db, site, "会费与会员权益", "rich_text", 12, "img-bule-6.png", rich_content=(
        "<p>第四届理事会任期 5 年，会费标准维持不变（经理事会审议通过）：</p>"
        + table(["会员类别", "年费", "核心权益"], [
            ["单位会员", "¥5,000 / 年", "全活动免费参加 2 人 + 政企对接优先 + 会刊宣传"],
            ["个人会员", "¥1,200 / 年", "活动会员价 + 行业社群 + 资源对接服务"],
            ["青年理事（新增）", "¥3,000 / 年", "单位会员权益 + 理事会列席 + 专项委员会任职资格"],
        ])
        + note("换届后 30 天内完成会费缴纳；新会员入会可在大会现场办理，享首年 9 折。")
    ))
    mod(db, site, "我的二维码", "qrcode", 13, "img-bule-9.png", qrcode_config={
        "hint": "会议当天出示此二维码，工作人员扫码完成签到",
        "display_fields": ["username", "nickname"],
    })
    prune_extra(db, site)
    add_checkin(db, site, ["会员签到"])
    add_accounts(db, site, [
        ("member001", "刘会员", None),
        ("observer001", "观察员", ["会议通知", "大会议程", "组织架构", "会议资料",
                               "会议纪律", "交通指引", "我的二维码"]),
    ])


# ---------------------------------------------------------------- 资产上传

def upload_assets(dry: bool, skip: bool) -> dict:
    """上传 KV/配图/PDF 到 OSS，返回 文件名 -> URL"""
    env = load_env()
    urls = {}
    if skip or dry:
        base = f"https://{env.get('OSS_BUCKET_NAME', 'bucket')}.{env.get('OSS_ENDPOINT', 'aliyuncs.com')}"
        for f in ASSETS:
            urls[f] = f"{base}/{OSS_PREFIX}/{f}"
        if dry:
            print(f"  [dry] 资产共 {len(ASSETS)} 个（不实际上传）")
        return urls
    import oss2
    auth = oss2.Auth(env["OSS_ACCESS_KEY_ID"], env["OSS_ACCESS_KEY_SECRET"])
    bucket = oss2.Bucket(auth, "https://" + env["OSS_ENDPOINT"], env["OSS_BUCKET_NAME"])
    for f in ASSETS:
        local = os.path.join(ASSET_DIR, f)
        key = f"{OSS_PREFIX}/{f}"
        bucket.put_object_from_file(key, local)
        urls[f] = f"https://{env['OSS_BUCKET_NAME']}.{env['OSS_ENDPOINT']}/{key}"
        print(f"  [oss] {f} -> {key}")
    return urls


def main():
    parser = argparse.ArgumentParser(description="案例微站种子脚本")
    parser.add_argument("--reset", action="store_true", help="删除 6 个案例微站后重建")
    parser.add_argument("--dry-run", action="store_true", help="只打印操作，不写库不上传")
    parser.add_argument("--skip-upload", action="store_true", help="跳过 OSS 上传（资产已存在时）")
    args = parser.parse_args()

    cases = (case_wedding, case_course, case_summit, case_annual, case_store, case_chamber)

    db = SessionLocal()
    try:
        owner = db.query(User).filter(User.username == "demo_admin").first()
        if not owner:
            print("未找到演示账号 demo_admin，请先执行: .venv/bin/python seed_demo.py", file=sys.stderr)
            sys.exit(1)

        if args.reset:
            for code in CASE_CODES:
                site = db.query(Site).filter(Site.code == code).first()
                if site:
                    db.delete(site)
            db.flush()
            print("已删除旧案例微站")

        print("== 上传案例资产 ==")
        urls = upload_assets(args.dry_run, args.skip_upload)

        print("== 创建案例微站 ==")
        if args.dry_run:
            for fn in cases:
                print(f"  [dry] {fn.__doc__.strip().splitlines()[0] if fn.__doc__ else fn.__name__}")
        else:
            for fn in cases:
                fn(db, owner, urls)
            # 统一清理：停用脚本中已不存在的模块（改名/删除遗留）
            for sid, titles in _SYNCED_TITLES.items():
                site = db.get(Site, sid)
                if site:
                    prune_extra(db, site)
            db.commit()
            print("== 完成 ==")
            print("案例微站（均已上线）:")
            print("  公开访问：/s/demo-wedding  /s/demo-course  /s/demo-store")
            print("  需登录  ：/s/demo-summit /s/demo-annual /s/demo-chamber（账号见上方输出，密码 Demo@123456）")
    except Exception as e:
        db.rollback()
        print(f"执行失败，已回滚：{e}", file=sys.stderr)
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()
