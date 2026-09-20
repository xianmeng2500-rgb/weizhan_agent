#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""生成案例集页面 docs/case-gallery.html（含每个案例的体验二维码，单文件可直接外发）

用法: /Users/simon/.workbuddy/binaries/python/envs/default/bin/python backend/tools/gen_case_gallery.py
依赖: qrcode（managed env 已安装）；域名在 DOMAIN 常量处修改
"""
import base64
import io
import os

import qrcode

BASE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
OUT = os.path.join(BASE, "docs", "case-gallery.html")
DOMAIN = "https://wm.meetotour.com"
LOGIN_PWD = "Demo@123456"

CASES = [
    dict(code="demo-wedding", industry="婚庆宴会", title="张伟 & 李娜 婚礼邀请", modules=9,
         desc="电子请柬 + 宾客回执 + 婚礼流程 + 席位指引，一份请柬搞定宾客沟通",
         tags=["公开访问", "宾客回执", "自定义表单"], access="public"),
    dict(code="demo-course", industry="培训教育", title="少儿编程秋季班招生", modules=10,
         desc="课程体系 + 开班时间表 + 免费试听预约，招生线索自动汇总成表",
         tags=["公开访问", "试听预约", "开班日程"], access="public"),
    dict(code="demo-summit", industry="峰会论坛", title="2026 数字零售行业峰会", modules=11,
         desc="主论坛 + 双分论坛议程、嘉宾阵容、分场次签到，800 人大会全流程管理",
         tags=["需登录", "分场次签到", "账号权限"], access="login",
         accounts="vip001（全部可见）/ guest001（仅部分模块）"),
    dict(code="demo-annual", industry="企业年会", title="同心同行 · 2026 公司年会", modules=10,
         desc="年会通知、出席回执、抽奖入口、入场扫码核销，行政省一半心",
         tags=["需登录", "出席回执", "扫码核销"], access="login",
         accounts="vip001（全部可见）/ staff001（不含神秘节目单）"),
    dict(code="demo-store", industry="门店品牌", title="星空咖啡 · 会员日", modules=9,
         desc="活动日历 + 会员招募 + 门店导航，活动窗口到期自动开放 / 关闭",
         tags=["公开访问", "定时开关", "会员招募"], access="public"),
    dict(code="demo-chamber", industry="商协会", title="青年企业家协会换届大会", modules=10,
         desc="会议通知 + 参会回执 + 章程资料下载 + 会员扫码签到，秘书处一页搞定",
         tags=["需登录", "资料附件", "会员签到"], access="login",
         accounts="member001（全部可见）/ observer001（观察员视角）"),
    dict(code="demo-launch", industry="发布会", title="2026 新品发布会", modules=5,
         desc="报名提交后可修改、大会议程、现场多场次签到，标准发布会全流程",
         tags=["需登录", "提交后可改", "模块权限"], access="login",
         accounts="zhangsan（全部可见）/ lisi（仅部分模块）"),
    dict(code="demo-festival", industry="庆典活动", title="中秋品牌盛典", modules=4,
         desc="公开访问、预约报名、三日活动日程，到访客户扫码即看",
         tags=["公开访问", "预约报名", "多日日程"], access="public"),
]


def qr_b64(url: str) -> str:
    q = qrcode.QRCode(border=2, box_size=8)
    q.add_data(url)
    q.make()
    img = q.make_image(fill_color="#0F172A", back_color="white")
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return base64.b64encode(buf.getvalue()).decode()


def build_card(c: dict) -> str:
    url = f"{DOMAIN}/s/{c['code']}"
    qr = qr_b64(url)
    if c["access"] == "public":
        access_html = '<span class="pill g">公开访问 · 扫码即看</span>'
        login_html = ""
    else:
        access_html = '<span class="pill a">需登录 · 演示账号见下</span>'
        login_html = (f'<div class="login">演示账号：<code>{c["accounts"]}</code>'
                      f'<br>密码：<code>{LOGIN_PWD}</code></div>')
    tags = "".join(f'<span class="pill p">{t}</span>' for t in c["tags"])
    cnt = f'<span class="pill n">共 {c["modules"]} 个模块</span>' if c.get("modules") else ""
    return f"""
    <div class="case">
      <div class="case-main">
        <div class="case-head">
          <span class="industry">{c['industry']}</span>
          <h3>{c['title']}</h3>
        </div>
        <p class="desc">{c['desc']}</p>
        <div class="tags">{cnt}{tags}</div>
        <div class="access">{access_html}{login_html}</div>
        <a class="link" href="{url}" target="_blank">{url.replace('https://', '')} →</a>
      </div>
      <div class="case-qr">
        <img src="data:image/png;base64,{qr}" alt="{c['title']} 二维码">
        <span>扫码体验</span>
      </div>
    </div>"""


HTML = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>微站系统 · 案例集</title>
<style>
:root{
  --primary:#4F46E5; --primary-dark:#3730A3; --primary-light:#EEF2FF;
  --bg:#F8FAFC; --card:#FFFFFF; --border:#E2E8F0;
  --text:#0F172A; --text-2:#475569; --text-3:#94A3B8;
}
*{margin:0;padding:0;box-sizing:border-box;}
body{font-family:-apple-system,BlinkMacSystemFont,"PingFang SC","Microsoft YaHei","Helvetica Neue",Arial,sans-serif;background:var(--bg);color:var(--text);line-height:1.75;font-size:15px;}
.wrap{max-width:1060px;margin:0 auto;padding:0 24px;}
header.hero{background:linear-gradient(135deg,#312E81 0%,#4F46E5 52%,#0EA5E9 100%);color:#fff;padding:56px 0 64px;position:relative;overflow:hidden;}
header.hero::after{content:"";position:absolute;right:-140px;top:-140px;width:440px;height:440px;border-radius:50%;background:rgba(255,255,255,.08);}
header.hero .wrap{position:relative;z-index:1;}
.tagline{display:inline-block;background:rgba(255,255,255,.18);border:1px solid rgba(255,255,255,.35);border-radius:999px;padding:5px 16px;font-size:13px;margin-bottom:18px;}
header.hero h1{font-size:38px;font-weight:600;margin-bottom:12px;}
header.hero p.sub{font-size:16.5px;color:rgba(255,255,255,.88);max-width:720px;}
main{padding:48px 0 64px;}
.tip{background:var(--primary-light);border-left:4px solid var(--primary);border-radius:10px;padding:13px 18px;font-size:14px;color:var(--primary-dark);margin-bottom:28px;}
.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(480px,1fr));gap:18px;}
.case{background:var(--card);border:1px solid var(--border);border-radius:16px;padding:22px 24px;display:flex;gap:20px;transition:.18s;}
.case:hover{border-color:var(--primary);box-shadow:0 10px 30px rgba(79,70,229,.10);}
.case-main{flex:1;min-width:0;}
.case-head{display:flex;align-items:center;gap:10px;margin-bottom:8px;flex-wrap:wrap;}
.industry{flex-shrink:0;background:var(--primary);color:#fff;font-size:12px;padding:3px 10px;border-radius:999px;letter-spacing:.5px;}
.case h3{font-size:18px;font-weight:600;}
.desc{font-size:14px;color:var(--text-2);margin-bottom:12px;}
.tags{display:flex;gap:6px;flex-wrap:wrap;margin-bottom:12px;}
.pill{display:inline-block;padding:2px 10px;border-radius:999px;font-size:12px;font-weight:500;}
.pill.p{background:var(--primary-light);color:var(--primary-dark);}
.pill.n{background:#F1F5F9;color:#475569;}
.pill.g{background:#F0FDF4;color:#15803D;}
.pill.a{background:#FFFBEB;color:#B45309;}
.access{margin-bottom:10px;}
.login{margin-top:8px;font-size:13px;color:var(--text-2);}
code{background:#F1F5F9;padding:1px 7px;border-radius:5px;font-size:12.5px;color:#334155;}
.link{display:inline-block;font-size:13.5px;color:var(--primary);text-decoration:none;font-weight:500;}
.link:hover{text-decoration:underline;}
.case-qr{flex-shrink:0;width:118px;text-align:center;}
.case-qr img{width:118px;height:118px;border:1px solid var(--border);border-radius:10px;display:block;}
.case-qr span{display:block;font-size:12px;color:var(--text-3);margin-top:6px;}
.cta{margin-top:36px;background:linear-gradient(135deg,#312E81,#4F46E5);border-radius:16px;padding:30px 34px;color:#fff;display:flex;justify-content:space-between;align-items:center;gap:20px;flex-wrap:wrap;}
.cta h3{font-size:21px;margin-bottom:6px;}
.cta p{font-size:14px;color:rgba(255,255,255,.85);margin:0;}
footer{border-top:1px solid var(--border);padding:24px 0 44px;color:var(--text-3);font-size:13px;text-align:center;}
@media(max-width:1080px){.grid{grid-template-columns:1fr;}}
@media(max-width:640px){.case{flex-direction:column;}.case-qr{width:100%;}.case-qr img{margin:0 auto;}}
@media print{header.hero,.cta{-webkit-print-color-adjust:exact;print-color-adjust:exact;}.case{page-break-inside:avoid;}}
</style>
</head>
<body>
<header class="hero">
  <div class="wrap">
    <span class="tagline">微站系统 · 案例集</span>
    <h1>一场活动一个微站</h1>
    <p class="sub">以下均为真实可访问的演示站点，覆盖婚庆、培训、峰会、年会、门店、商协会等场景。扫描二维码或点击链接即可体验，公开站点无需登录。</p>
  </div>
</header>
<main class="wrap">
  <div class="tip"><b>体验说明：</b>标注「公开访问」的案例，扫码即可直接查看；标注「需登录」的案例使用页面下方给出的演示账号登录（用于演示签到与模块权限功能）。</div>
  <div class="grid">__CARDS__</div>
  <div class="cta">
    <div>
      <h3>下一个活动，就用微站系统</h3>
      <p>3 分钟搭好 · 报名 · 签到 · 数据看板一站式。联系我们，最快当天上线。</p>
      <p style="margin-top:6px;"><b>微信 / 电话：</b>请替换为你的联系方式</p>
    </div>
  </div>
</main>
<footer>微站系统 · 案例集 · __DATE__ 生成</footer>
</body>
</html>
"""

if __name__ == "__main__":
    from datetime import date
    html = HTML.replace("__CARDS__", "".join(build_card(c) for c in CASES))
    html = html.replace("__DATE__", date.today().isoformat())
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    open(OUT, "w", encoding="utf-8").write(html)
    print("生成:", OUT, f"({len(html)} chars, {len(CASES)} 案例)")
