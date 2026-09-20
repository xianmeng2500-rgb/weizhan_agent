#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""生成案例微站 KV 主视觉（750x340）与演示附件文件。

仅需在资产缺失时运行一次，产物已随仓库提供：
    python tools/gen_demo_kv.py

依赖 Pillow（建议用独立环境运行，不要污染 backend/.venv）：
    /Users/simon/.workbuddy/binaries/python/envs/default/bin/python tools/gen_demo_kv.py
"""
import os
from PIL import Image, ImageDraw, ImageFont

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(BASE, "seed_assets", "demo")
FONT = "/System/Library/Fonts/Hiragino Sans GB.ttc"
W, H = 750, 340

_fc = {}
def F(size, bold=False):
    k = (size, bold)
    if k not in _fc:
        _fc[k] = ImageFont.truetype(FONT, size, index=2 if bold else 0)
    return _fc[k]

def hex2rgb(s):
    s = s.lstrip("#")
    return tuple(int(s[i:i + 2], 16) for i in (0, 2, 4))

def gradient(top, bottom):
    img = Image.new("RGB", (W, H))
    px = img.load()
    t, b = hex2rgb(top), hex2rgb(bottom)
    for y in range(H):
        k = y / (H - 1)
        c = tuple(int(t[i] + (b[i] - t[i]) * k) for i in range(3))
        for x in range(W):
            px[x, y] = c
    return img

THEMES = {
    "wedding": dict(top="#FFFBF2", bottom="#E9D5AC", title="#6B4E23", sub="#8A6E42", accent="#C9A227"),
    "course":  dict(top="#0F2E6E", bottom="#2C6BD8", title="#FFFFFF", sub="#CFE0FF", accent="#7FD3FF"),
    "summit":  dict(top="#0A0F28", bottom="#1D2A5C", title="#FFFFFF", sub="#A9B8E8", accent="#22D3EE"),
    "annual":  dict(top="#7E1414", bottom="#B8271F", title="#FFE9B0", sub="#FFD9A8", accent="#FFD166"),
    "store":   dict(top="#2E1D14", bottom="#6B4425", title="#FFEBD6", sub="#E8C9A8", accent="#F5A524"),
    "chamber": dict(top="#0F2244", bottom="#1E3E72", title="#FFFFFF", sub="#BBD0F0", accent="#D4AF37"),
}

CASES = [
    ("wedding", "婚礼邀请函", "张伟 & 李娜", "2026.10.18 · 云栖厅 · 诚邀您见证"),
    ("course", "招生宣传", "少儿编程秋季班", "10月12日开课 · 限额 20 人"),
    ("summit", "峰会论坛", "2026 数字零售行业峰会", "10.24-10.25 · 上海国际会议中心"),
    ("annual", "企业年会", "同心同行 · 2026 公司年会", "2027.01.16 · 星河宴会厅"),
    ("store", "门店活动", "星空咖啡 · 会员日", "10.01-10.07 · 全场第二杯半价"),
    ("chamber", "协会会议", "青年企业家协会换届大会", "2026.11.08 · 市会议中心 A 厅"),
]

def fit_font(text, max_w, start, bold=True):
    size = start
    while size > 24:
        f = F(size, bold)
        if ImageDraw.Draw(Image.new("RGB", (10, 10))).textlength(text, font=f) <= max_w:
            return f
        size -= 2
    return F(24, bold)

def build_kv(key, tag, title, subtitle):
    th = THEMES[key]
    img = gradient(th["top"], th["bottom"]).convert("RGBA")
    ov = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(ov)
    acc = hex2rgb(th["accent"])
    light = key == "wedding"

    # 右上装饰圆
    d.ellipse([W - 190, -110, W + 90, 170], fill=acc + (30,))
    d.ellipse([W - 110, -50, W + 50, 110], outline=acc + (90,), width=2)
    # 左下装饰点阵
    for i in range(5):
        for j in range(3):
            a = 70 - i * 8 - j * 6
            if a <= 0:
                continue
            d.ellipse([52 + i * 16, H - 46 + j * 16, 56 + i * 16, H - 42 + j * 16], fill=acc + (a,))

    # 分类标签
    tf = F(20, True)
    tw = d.textlength(tag, font=tf)
    d.rounded_rectangle([52, 38, 52 + tw + 32, 78], radius=20,
                        fill=(255, 255, 255, 200) if light else acc + (48,),
                        outline=acc + (150,), width=1)
    d.text((52 + 16, 58), tag, font=tf, fill=hex2rgb(th["title"]) + (255,) if light else acc + (255,), anchor="lm")

    # 强调短线
    d.rounded_rectangle([52, 112, 116, 117], radius=2, fill=acc + (235,))

    # 主标题
    ft = fit_font(title, 646, 56)
    d.text((52, 166), title, font=ft, fill=hex2rgb(th["title"]) + (255,), anchor="lm")

    # 副标题
    fs = fit_font(subtitle, 646, 26, bold=False)
    d.text((52, 226), subtitle, font=fs, fill=hex2rgb(th["sub"]) + (255,), anchor="lm")

    img = Image.alpha_composite(img, ov).convert("RGB")
    path = os.path.join(OUT, "kv_%s.png" % key)
    img.save(path, quality=95)
    print("  [kv] %s  %s" % (os.path.basename(path), title))
    return path


# ---------------------------------------------------------------- 内容配图
MW, MH = 750, 420
PANEL_BG = "#FBFCFF"
PANEL_BORDER = "#E3E8F2"


def panel(title, accent, dark_text="#1E293B"):
    """生成内容配图底板：浅色卡片 + 顶部标题 + 强调条"""
    img = Image.new("RGB", (MW, MH), PANEL_BG)
    d = ImageDraw.Draw(img)
    d.rounded_rectangle([12, 12, MW - 13, MH - 13], radius=18, fill="#FFFFFF", outline=PANEL_BORDER, width=2)
    d.rounded_rectangle([40, 44, 48, 82], radius=3, fill=hex2rgb(accent))
    ft = fit_font(title, 560, 30)
    d.text((64, 63), title, font=ft, fill=hex2rgb(dark_text), anchor="lm")
    return img, d


def blk(d, box, text, sub=None, fill="#F4F7FE", border=None, tc="#1E293B", sc="#64748B",
        fs=23, ss=18, radius=12):
    d.rounded_rectangle(box, radius=radius, fill=hex2rgb(fill),
                        outline=hex2rgb(border) if border else None, width=2 if border else 0)
    x0, y0, x1, y1 = box
    cx = (x0 + x1) / 2
    if sub:
        d.text((cx, (y0 + y1) / 2 - 13), text, font=F(fs, True), fill=hex2rgb(tc), anchor="mm")
        d.text((cx, (y0 + y1) / 2 + 15), sub, font=F(ss), fill=hex2rgb(sc), anchor="mm")
    else:
        d.text((cx, (y0 + y1) / 2), text, font=F(fs, True), fill=hex2rgb(tc), anchor="mm")


def arrow_down(d, x, y0, y1, color):
    d.line([x, y0, x, y1 - 8], fill=hex2rgb(color), width=3)
    d.polygon([(x - 7, y1 - 9), (x + 7, y1 - 9), (x, y1)], fill=hex2rgb(color))


def img_wedding_layout():
    img, d = panel("婚宴场地座位分布", "#C9A227")
    d.rounded_rectangle([40, 106, MW - 40, MH - 40], radius=16, fill="#FFFDF6", outline="#E8D9B5", width=2)
    blk(d, [275, 126, 475, 178], "主 舞 台", fill="#FBF1D8", border="#DCC58A", tc="#7A5B2E")
    xs = [(58, 258), (274, 474), (490, 692)]
    data = [("1-6 号桌", "亲友席"), ("7-12 号桌", "同事席"), ("13-18 号桌", "同学席")]
    for (x0, x1), (t, s) in zip(xs, data):
        blk(d, [x0, 200, x1, 300], t, s, fill="#FFF8E7", border="#EBD9B4", tc="#7A5B2E", sc="#A08A5E", fs=21, ss=18)
    blk(d, [58, 320, 340, 372], "签 到 台", "签到 · 查座位", fill="#FBF1D8", border="#DCC58A", tc="#7A5B2E", fs=21, ss=17)
    blk(d, [370, 320, 692, 372], "合 影 区", "新人合影 · 打卡墙", fill="#FBF1D8", border="#DCC58A", tc="#7A5B2E", fs=21, ss=17)
    img.save(os.path.join(OUT, "img_wedding_layout.png"))
    print("  [img] img_wedding_layout.png")


def img_course_path():
    img, d = panel("课程进阶路径", "#2C6BD8")
    rows = [
        ("Scratch 启蒙班", "6-8 岁 · 16 课时 · 图形化编程启蒙", "#EAF1FE", "#BBD1F5", "#12407F"),
        ("Python 进阶班", "9-11 岁 · 20 课时 · 独立完成小游戏", "#EAF1FE", "#BBD1F5", "#12407F"),
        ("C++ 竞赛班", "12-15 岁 · 24 课时 · 备战信奥 CSP-J/S", "#EAF1FE", "#BBD1F5", "#12407F"),
    ]
    y = 116
    for i, (t, s, f, b, tc) in enumerate(rows):
        blk(d, [70, y, 680, y + 74], t, s, fill=f, border=b, tc=tc, sc="#3F6AA8", fs=25, ss=18)
        d.ellipse([34, y + 15, 70, y + 51], fill=hex2rgb("#2C6BD8"))
        d.text((52, y + 33), str(i + 1), font=F(21, True), fill=(255, 255, 255), anchor="mm")
        if i < 2:
            arrow_down(d, 375, y + 76, y + 96, "#9BB6E0")
        y += 98
    img.save(os.path.join(OUT, "img_course_path.png"))
    print("  [img] img_course_path.png")


def img_summit_venue():
    img, d = panel("3F 会场导览", "#1D9E75")
    blk(d, [40, 108, 250, 176], "签 到 区", "扶梯口 · 凭二维码核销", fill="#EAF1FE", border="#BBD1F5",
        tc="#12407F", sc="#3F6AA8", fs=21, ss=16)
    blk(d, [268, 108, 712, 214], "主 会 场", "可容纳 600 人 · 主论坛", fill="#E7F0FE", border="#9FBEF0",
        tc="#0F3A75", sc="#3F6AA8", fs=25, ss=18)
    blk(d, [40, 230, 244, 320], "分论坛 A 厅", "零售数字化", fill="#EAF7F2", border="#A9DCC8",
        tc="#0F5A45", sc="#3E8871", fs=21, ss=17)
    blk(d, [262, 230, 466, 320], "分论坛 B 厅", "私域增长", fill="#EAF7F2", border="#A9DCC8",
        tc="#0F5A45", sc="#3E8871", fs=21, ss=17)
    blk(d, [484, 230, 712, 320], "茶 歇 区", "自助咖啡 · 洽谈", fill="#FFF7E8", border="#EBD9B4",
        tc="#7A5B2E", sc="#A08A5E", fs=21, ss=17)
    for i, (x0, x1, t) in enumerate([(40, 244, "洗手间"), (262, 466, "电梯厅"), (484, 712, "商务洽谈区")]):
        blk(d, [x0, 336, x1, 384], t, fill="#F4F6FA", border="#DFE5EF", tc="#475569", fs=19)
    img.save(os.path.join(OUT, "img_summit_venue.png"))
    print("  [img] img_summit_venue.png")


def img_annual_awards():
    img, d = panel("年度奖项与奖品", "#B8271F")
    tiles = [
        ("年度之星", "iPhone 17 · 1 名", "#FDF3E7", "#EBC79A", "#8A5A20"),
        ("最佳新人", "AirPods Pro · 3 名", "#FDF3E7", "#EBC79A", "#8A5A20"),
        ("最佳团队", "团队旅行基金 5000 元", "#FDEBEB", "#EBB4B4", "#7F1D1D"),
        ("特别贡献", "定制奖杯 + 现金 3000 元", "#FDEBEB", "#EBB4B4", "#7F1D1D"),
    ]
    pos = [(40, 112, 366, 238), (384, 112, 710, 238), (40, 254, 366, 380), (384, 254, 710, 380)]
    for box, (t, s, f, b, tc) in zip(pos, tiles):
        blk(d, list(box), t, s, fill=f, border=b, tc=tc, sc="#8A6A50", fs=26, ss=18)
    img.save(os.path.join(OUT, "img_annual_awards.png"))
    print("  [img] img_annual_awards.png")


def img_store_perks():
    img, d = panel("会员日福利一览", "#F5A524")
    tiles = [
        ("第二杯半价", "每日 14:00-17:00 · 全场饮品"),
        ("甜品第二件 1 元", "数量有限 · 售完即止"),
        ("10 月生日蛋糕", "凭会员码免费领取一块"),
        ("充值满 200 送 30", "上不封顶 · 全国门店通用"),
    ]
    pos = [(40, 112, 366, 238), (384, 112, 710, 238), (40, 254, 366, 380), (384, 254, 710, 380)]
    for box, (t, s) in zip(pos, tiles):
        blk(d, list(box), t, s, fill="#FFF8EC", border="#F0D9AE", tc="#8A5A20", sc="#A8845A", fs=24, ss=17)
    img.save(os.path.join(OUT, "img_store_perks.png"))
    print("  [img] img_store_perks.png")


def img_chamber_org():
    img, d = panel("协会组织架构", "#1E3E72")
    blk(d, [255, 106, 495, 152], "会 员 大 会", "最高权力机构", fill="#EAF0FA", border="#B7C8E4",
        tc="#0F2244", sc="#4A638C", fs=22, ss=17)
    arrow_down(d, 375, 154, 174, "#9AB1D6")
    blk(d, [255, 178, 495, 224], "理 事 会", "执行机构 · 任期 4 年", fill="#EAF0FA", border="#B7C8E4",
        tc="#0F2244", sc="#4A638C", fs=22, ss=17)
    arrow_down(d, 375, 226, 246, "#9AB1D6")
    blk(d, [255, 250, 495, 296], "秘 书 处", "日常事务 · 会员服务", fill="#EAF0FA", border="#B7C8E4",
        tc="#0F2244", sc="#4A638C", fs=22, ss=17)
    arrow_down(d, 375, 298, 316, "#9AB1D6")
    for x0, x1, t in [(40, 244, "青年创业专委会"), (274, 476, "对外联络专委会"), (506, 710, "公益事业专委会")]:
        blk(d, [x0, 324, x1, 384], t, fill="#F4F7FC", border="#D5DFEE", tc="#1E3E72", fs=19)
    img.save(os.path.join(OUT, "img_chamber_org.png"))
    print("  [img] img_chamber_org.png")


CONTENT_IMAGES = [img_wedding_layout, img_course_path, img_summit_venue,
                  img_annual_awards, img_store_perks, img_chamber_org]

DOC_LINES = [
    ("青年企业家协会", 30, True),
    ("章 程（演示文件）", 24, True),
    ("", 10, False),
    ("第一章  总  则", 18, True),
    ("第一条  本会名称为青年企业家协会，是由本市青年企业家自愿结成的联合性、非营利性社会组织。", 15, False),
    ("第二条  本会宗旨：团结引导青年企业家，促进交流合作，服务地方经济发展。", 15, False),
    ("", 8, False),
    ("第二章  会  员", 18, True),
    ("第三条  申请加入本会的会员，应当拥护本会章程，有加入本会的意愿。", 15, False),
    ("第四条  会员享有下列权利：参加本会活动、获得本会服务、对本会工作提出建议。", 15, False),
    ("", 8, False),
    ("第三章  组织机构", 18, True),
    ("第五条  会员大会是本会的最高权力机构，每届任期四年。", 15, False),
    ("", 8, False),
    ("—— 本文件为演示用示例文件，内容仅供参考 ——", 13, False),
]

def build_doc():
    pw, ph = 1240, 1754  # A4 @150dpi
    img = Image.new("RGB", (pw, ph), (255, 255, 255))
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, pw, 14], fill=(31, 59, 110))
    y = 150
    for text, size, bold in DOC_LINES:
        f = F(size * 2, bold)
        if text:
            d.text((140, y), text, font=f, fill=(30, 38, 60) if bold else (70, 80, 100), anchor="lt")
        y += int(size * 2 * 1.9) + 14
    d.text((140, ph - 120), "协会章程（演示文件）· 第 1 页 / 共 1 页", font=F(24), fill=(150, 160, 175), anchor="lt")
    path = os.path.join(OUT, "doc_charter.pdf")
    img.save(path, "PDF", resolution=150)
    print("  [pdf] %s" % os.path.basename(path))
    return path


if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    print("生成案例 KV 主视觉 ->", OUT)
    for key, tag, title, sub in CASES:
        build_kv(key, tag, title, sub)
    print("生成案例内容配图")
    for fn in CONTENT_IMAGES:
        fn()
    build_doc()
    print("完成")
