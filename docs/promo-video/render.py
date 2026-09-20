#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""微站系统宣传片渲染器：S1 AI 实拍开场 + S2-S5 动效，1920x1080@30fps"""
import math, os, subprocess, sys, wave
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import qrcode
import imageio_ffmpeg

BASE = os.path.dirname(os.path.abspath(__file__))
FF = imageio_ffmpeg.get_ffmpeg_exe()
W, H, FPS = 1920, 1080, 30
XIANYU = os.path.join(BASE, "..", "xianyu-images")

BG_TOP, BG_MID, BG_BOT = (9, 14, 42), (20, 27, 72), (7, 11, 34)
BLUE, CYAN = (79, 124, 255), (34, 211, 238)
PURPLE, GREEN, AMBER = (139, 92, 246), (52, 211, 153), (251, 191, 36)
WHITE, MUTED = (240, 244, 255), (158, 168, 200)
CARD_F, CARD_O = (255, 255, 255, 14), (255, 255, 255, 40)

_HIRA = "/System/Library/Fonts/Hiragino Sans GB.ttc"
_fcache = {}
def F(size, bold=False):
    k = (size, bold)
    if k not in _fcache:
        _fcache[k] = ImageFont.truetype(_HIRA, size, index=2 if bold else 0)
    return _fcache[k]

def clamp01(x): return 0.0 if x < 0 else (1.0 if x > 1 else x)
def eo(x):
    x = clamp01(x); return 1 - (1 - x) ** 3
def eio(x):
    x = clamp01(x); return x * x * (3 - 2 * x)
def eback(x):
    x = clamp01(x); c1, c3 = 1.70158, 2.70158
    return 1 + c3 * (x - 1) ** 3 + c1 * (x - 1) ** 2
def seg(t, a, b): return clamp01((t - a) / max(b - a, 1e-6))

NARR = [10.77, 10.54, 15.21, 18.33, 2.72]
DUR = [NARR[0] + 1.0, NARR[1] + 1.0, NARR[2] + 1.0, NARR[3] + 1.0, NARR[4] + 3.8]
START = [sum(DUR[:i]) for i in range(5)]
TOTAL = sum(DUR)

def build_bg():
    img = Image.new("RGB", (W, H))
    px = img.load()
    for y in range(H):
        if y < H // 2:
            k = y / (H / 2); c = tuple(int(a + (b - a) * k) for a, b in zip(BG_TOP, BG_MID))
        else:
            k = (y - H / 2) / (H / 2); c = tuple(int(a + (b - a) * k) for a, b in zip(BG_MID, BG_BOT))
        for x in range(W):
            px[x, y] = c
    d = ImageDraw.Draw(img, "RGBA")
    for x in range(0, W, 96): d.line([(x, 0), (x, H)], fill=(255, 255, 255, 7))
    for y in range(0, H, 96): d.line([(0, y), (W, y)], fill=(255, 255, 255, 7))
    m = Image.radial_gradient("L").resize((int(W * 1.9), int(H * 1.9)))
    m = m.crop((m.width // 2 - W // 2, m.height // 2 - H // 2, m.width // 2 + W // 2, m.height // 2 + H // 2))
    vig = Image.new("L", (W, H), 0)
    vig.paste(m.point(lambda v: int(v * 0.45)), (0, 0))
    img.paste(Image.new("RGB", (W, H), (0, 0, 8)), (0, 0), vig)
    return img
BG = build_bg()

def orb_sprite(color, size=560):
    m = Image.radial_gradient("L").resize((size, size))
    a = m.point(lambda v: max(0, 110 - v))
    s = Image.new("RGBA", (size, size), color + (0,))
    s.putalpha(a)
    return s
ORB1, ORB2 = orb_sprite(BLUE), orb_sprite(PURPLE)

POSTER = Image.open(os.path.join(
    XIANYU, "电商营销海报封面图_画面中央一台现代智能手机样机_屏幕展示一_2026-08-28T08-37-24.png")).convert("RGB")

def cover(img, tw, th):
    w, h = img.size; s = max(tw / w, th / h)
    r = img.resize((max(1, int(w * s + .5)), max(1, int(h * s + .5))))
    l, t = (r.width - tw) // 2, (r.height - th) // 2
    return r.crop((l, t, l + tw, t + th))
KV_BANNER = cover(POSTER, 272, 116)
PW5 = int(680 * 0.485)          # 场景5手机屏宽
HERO5 = cover(POSTER, PW5 - 28, 300)

_qr = qrcode.QRCode(border=1, box_size=8); _qr.add_data("https://wm.meetotour.com"); _qr.make()
QRCODE = _qr.make_image(fill_color="#0b1026", back_color="white").convert("RGB").resize((200, 200), Image.NEAREST)

_BOT = Image.new("L", (1, H), 0)
_bp = _BOT.load()
for _y in range(H):
    _bp[0, _y] = 0 if _y < 620 else int(min(1, (_y - 620) / 380) * 160)
BOTGRAD = _BOT.resize((W, H))

C1, C2 = os.path.join(BASE, "frames/clip1"), os.path.join(BASE, "frames/clip2")
N1 = len([f for f in os.listdir(C1) if f.endswith(".jpg")])
_jpeg_cache = {}
def clip_frame(d, idx):
    if idx in _jpeg_cache: return _jpeg_cache[idx]
    if len(_jpeg_cache) > 140: _jpeg_cache.clear()
    im = Image.open(os.path.join(d, "f%04d.jpg" % (idx + 1))).convert("RGB")
    _jpeg_cache[idx] = im; return im

def zoom_cover(img, z):
    if z <= 1.001: return img
    r = img.resize((int(W * z), int(H * z)))
    l, t = (r.width - W) // 2, (r.height - H) // 2
    return r.crop((l, t, l + W, t + H))

def base_frame(t):
    img = BG.copy()
    x1 = int(320 + 160 * math.sin(t * 0.21)); y1 = int(220 + 110 * math.cos(t * 0.17))
    x2 = int(1450 + 150 * math.cos(t * 0.15)); y2 = int(760 + 120 * math.sin(t * 0.19))
    img.paste(ORB1, (x1 - 280, y1 - 280), ORB1)
    img.paste(ORB2, (x2 - 280, y2 - 280), ORB2)
    return img

def card(d, box, r=24, fill=CARD_F, outline=CARD_O, width=2):
    d.rounded_rectangle(box, radius=r, fill=fill, outline=outline, width=width)

def shadow_text(d, xy, text, font, fill, anchor="mm"):
    d.text((xy[0] + 2, xy[1] + 4), text, font=font, fill=(0, 0, 0, 130), anchor=anchor)
    d.text(xy, text, font=font, fill=fill, anchor=anchor)

def logo(d, alpha=255):
    x, y = 60, 44
    d.rounded_rectangle([x, y, x + 54, y + 54], radius=14, fill=(79, 124, 255, alpha))
    d.text((x + 27, y + 28), "微", font=F(30, True), fill=(255, 255, 255, alpha), anchor="mm")
    d.text((x + 70, y + 28), "微站系统", font=F(28, True), fill=(235, 240, 255, alpha), anchor="lm")

def progress(d, t, alpha=150):
    w = int(W * clamp01(t / TOTAL))
    d.rectangle([0, H - 5, w, H], fill=(99, 140, 255, alpha))

def subtitle(d, text, a):
    if a <= 0: return
    f = F(37); w = d.textlength(text, font=f); pad = 40
    x0 = (W - w) / 2 - pad; y0 = H - 120
    d.rounded_rectangle([x0, y0, x0 + w + pad * 2, y0 + 74], radius=37, fill=(6, 10, 30, int(175 * a)))
    d.text((W / 2, y0 + 38), text, font=f, fill=(232, 238, 255, min(255, int(245 * a))), anchor="mm")

def pick_sub(d, subs, tl, dur):
    pr = tl / dur; idx = None
    for j, (_, x, y) in enumerate(subs):
        if x <= pr <= y or (j == len(subs) - 1 and pr > x): idx = j; break
    if idx is None: return
    txt, x, y = subs[idx]
    a = min(seg(tl, x * dur, x * dur + .35), 1 - seg(tl, y * dur - .3, y * dur))
    if a > 0: subtitle(d, txt, a)

SUBS = [
    [("微站系统 —— 无需开发", .0, .30), ("3 分钟搭一个活动微站", .28, .52),
     ("选模板 · 一键套用 · AI 生成主视觉 · 完成", .50, 1.0)],
    [("三大场景，一个系统全覆盖", .0, .17), ("内容展示：图文 / 外链 / 日程", .16, .43),
     ("报名收集：表单自定义 · 数据一键导出", .42, .70), ("现场签到：扫码核销 · 支持补签", .69, 1.0)],
    [("模板一键套用 · 模块级权限 · 实时数据统计", .0, .34), ("编辑页内置 AI 一键生图", .33, .55),
     ("KV / 背景 / 分享图 / 模块图标 全都能画", .54, .76), ("开放与关闭时间，自动控制", .75, 1.0)],
    [("下一个活动，就用微站系统", .05, .92)],
]

_mask_cache = {}
def phone(img, ov, content, cx=960, cy=610, ph=620):
    pw = int(ph * 0.485); x0, y0 = cx - pw // 2, cy - ph // 2
    key = (pw, ph)
    if key not in _mask_cache:
        m = Image.new("L", (pw, ph), 0)
        ImageDraw.Draw(m).rounded_rectangle([0, 0, pw, ph], radius=34, fill=255)
        _mask_cache[key] = m
    scr = Image.new("RGB", (pw, ph), (16, 22, 52))
    sd = ImageDraw.Draw(scr, "RGBA")
    content(sd, pw, ph)
    img.paste(scr, (x0, y0), _mask_cache[key])
    d = ImageDraw.Draw(ov, "RGBA")
    d.rounded_rectangle([x0 - 8, y0 - 8, x0 + pw + 8, y0 + ph + 8], radius=42,
                        outline=(255, 255, 255, 70), width=3)
    d.rounded_rectangle([cx - 44, y0 + 2, cx + 44, y0 + 22], radius=11, fill=(10, 14, 36, 255))

def skeleton(sd, pw, ph, p=1.0):
    p = clamp01(p)
    sd.rounded_rectangle([12, 40, pw - 12, 62], radius=8, fill=(255, 255, 255, int(60 * p)))
    sd.rounded_rectangle([14, 74, pw - 14, 190], radius=14, fill=(70, 100, 235, int(150 * p)))
    yy = 204
    for i in range(3):
        sd.rounded_rectangle([14, yy, pw - 14, yy + 84], radius=12, fill=(255, 255, 255, int(22 * p)))
        w1 = max(1, int(120 * clamp01(p * 2 - i * .3)))
        w2 = max(1, int(190 * clamp01(p * 1.6 - i * .2)))
        sd.rounded_rectangle([26, yy + 14, 26 + w1, yy + 30], radius=7, fill=(255, 255, 255, int(70 * p)))
        sd.rounded_rectangle([26, yy + 44, 26 + w2, yy + 56], radius=6, fill=(255, 255, 255, int(40 * p)))
        yy += 96

def sparkle(d, x, y, r, a, color=(255, 230, 140)):
    d.polygon([(x - r, y), (x, y - r * .32), (x + r, y), (x, y + r * .32)], fill=color + (a,))
    d.polygon([(x, y - r), (x + r * .32, y), (x, y + r), (x - r * .32, y)], fill=color + (a,))

# ---------- 场景 1：AI 实拍痛点 ----------
CAPS1 = [("活动就要开始了", .35, 3.0), ("页面还没做好？", 3.1, 5.0),
         ("找开发排期 · 改稿 · 等上线 ……", 5.35, 9.7), ("搭个移动端展示页，真的要这么麻烦吗？", 10.05, 12.0)]

def scene1(tl, dur):
    if tl < 5.04:
        f = clip_frame(C1, min(int(tl * 24), N1 - 1))
    elif tl < 10.08:
        f = clip_frame(C2, min(int((tl - 5.04) * 24), N1 - 1))
    else:
        f = clip_frame(C2, N1 - 1)
    f = zoom_cover(f, 1.08 + (0.05 * (tl - 10.08) if tl > 10.08 else 0))
    img = f.resize((W, H)) if f.size != (W, H) else f.copy()
    img.paste(Image.new("RGB", (W, H), (4, 6, 16)), (0, 0), BOTGRAD)
    ov = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(ov)
    d.rectangle([0, 0, W, H], fill=(5, 8, 20, 55))
    for txt, a, b in CAPS1:
        ai = min(seg(tl, a, a + .4), 1 - seg(tl, b - .3, b))
        if ai > 0:
            rise = int((1 - eo(seg(tl, a, a + .5))) * 26)
            shadow_text(d, (W / 2, 790 + rise), txt, F(58, True), (255, 255, 255, int(255 * ai)))
    return Image.alpha_composite(img.convert("RGBA"), ov).convert("RGB")

# ---------- 场景 2：产品亮相 ----------
STEPS = ["选模板", "一键套用", "AI 生成 KV", "完成"]

def scene2(tl, dur):
    img = base_frame(START[1] + tl)
    ov = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(ov)
    logo(d); progress(d, START[1] + tl)
    if tl < 3.0:
        a1 = eo(seg(tl, .15, .9)); a2 = eo(seg(tl, .75, 1.5))
        shadow_text(d, (W / 2, 470 + int((1 - a1) * 30)), "微站系统", F(112, True), (255, 255, 255, int(255 * a1)))
        d.rounded_rectangle([W / 2 - 130 * a1, 556, W / 2 + 130 * a1, 560], radius=2, fill=(99, 140, 255, int(220 * a1)))
        shadow_text(d, (W / 2, 630 + int((1 - a2) * 24)), "无需开发 · 3 分钟搭一个活动微站", F(46), (196, 206, 240, int(255 * a2)))
    else:
        s = tl - 3.0
        step = min(int(s / 2.14), 3); loc = s - step * 2.14
        for i, name in enumerate(STEPS):
            cx = W / 2 + (i - 1.5) * 240; act = i == step; done = i < step
            cc = (99, 140, 255, 235) if act else ((52, 211, 153, 150) if done else (255, 255, 255, 26))
            d.rounded_rectangle([cx - 96, 158, cx + 96, 214], radius=28, fill=cc,
                                outline=None if act else (255, 255, 255, 60), width=2)
            d.text((cx, 186), name, font=F(30, act), fill=(255, 255, 255, 255 if (act or done) else 170), anchor="mm")
        pa = eo(seg(loc, .1, .6))
        PX, PY = 810, 300   # 屏幕左上角（cx=960 cy=610 ph=620 pw=300）
        def content(sd, pw, ph):
            if step == 0:
                grads = [(236, 110, 173), (168, 120, 255), (240, 96, 96)]
                for i, g in enumerate(grads):
                    ai = eo(seg(loc, .15 + i * .18, .55 + i * .18))
                    yy = 90 + i * 150 - int((1 - ai) * 40)
                    hi = i == 1 and loc > .9
                    sd.rounded_rectangle([pw / 2 - 105, yy, pw / 2 + 105, yy + 130], radius=14,
                                         fill=g + (int(230 * ai),),
                                         outline=(255, 255, 255, 220) if hi else None, width=4)
                    sd.rounded_rectangle([pw / 2 - 80, yy + 18, pw / 2 + 40, yy + 34], radius=6, fill=(255, 255, 255, int(120 * ai)))
                    sd.rounded_rectangle([pw / 2 - 80, yy + 50, pw / 2 + 70, yy + 60], radius=5, fill=(255, 255, 255, int(70 * ai)))
                sd.text((pw / 2, 560), "选择喜欢的模板", font=F(26), fill=(200, 210, 245, int(230 * pa)), anchor="mm")
            elif step == 1:
                skeleton(sd, pw, ph, pa)
                sd.text((pw / 2, 560), "页面结构自动生成", font=F(26), fill=(200, 210, 245, int(230 * pa)), anchor="mm")
            elif step == 2:
                skeleton(sd, pw, ph, 1.0)
                sd.text((pw / 2, 560), "AI 一键生成主视觉", font=F(26), fill=(200, 210, 245, int(230 * pa)), anchor="mm")
            else:
                skeleton(sd, pw, ph, 1.0)
                k = eback(seg(loc, .2, .8)); r = int(34 * k)
                if r > 1:
                    sd.ellipse([pw / 2 - r - 8, 300 - r, pw / 2 + r - 8, 300 + r], fill=(52, 211, 153, 245))
                    sd.line([pw / 2 - 22, 300, pw / 2 - 12, 310], fill=(255, 255, 255, 255), width=5)
                    sd.line([pw / 2 - 12, 310, pw / 2 + 6, 288], fill=(255, 255, 255, 255), width=5)
                sd.rounded_rectangle([pw / 2 - 72, 356, pw / 2 + 72, 396], radius=20, fill=(52, 211, 153, int(220 * pa)))
                sd.text((pw / 2, 376), "已发布上线", font=F(24, True), fill=(255, 255, 255, int(255 * pa)), anchor="mm")
        phone(img, ov, content)
        if step == 2:
            k = eback(seg(loc, .3, .9))
            if k > 0.02:
                bw, bh = max(1, int(272 * k)), max(1, int(116 * k))
                kv = KV_BANNER.resize((bw, bh)).convert("RGBA")
                a = int(255 * min(1, k))
                kv.putalpha(Image.new("L", kv.size, a))
                ov.paste(kv, (int(PX + 15 + (272 - bw) / 2), int(PY + 74 + (116 - bh) / 2)))
                aa = 130 + 90 * math.sin(tl * 6)
                sparkle(d, PX + 250, PY + 66, 12 + 3 * math.sin(tl * 5), int(aa))
                sparkle(d, PX + 30, PY + 130, 8, int(aa * .8), (150, 220, 255))
    pick_sub(d, SUBS[0], tl, dur)
    return Image.alpha_composite(img.convert("RGBA"), ov).convert("RGB")

# ---------- 场景 3：三大核心能力 ----------
def scene3(tl, dur):
    img = base_frame(START[2] + tl)
    ov = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(ov)
    logo(d); progress(d, START[2] + tl)
    at = eo(seg(tl, .15, .9))
    shadow_text(d, (W / 2, 165 + int((1 - at) * 22)), "三大场景 · 一个系统全覆盖", F(58, True), (255, 255, 255, int(255 * at)))
    panels = [("内容展示", "图文 · 外链 · 日程", CYAN), ("报名收集", "自定义表单 · 导出", BLUE), ("现场签到", "扫码核销 · 补签", GREEN)]
    for i, (tt, desc, ac) in enumerate(panels):
        t0 = 1.6 + i * 1.1; pa = eo(seg(tl, t0, t0 + .5)); k = eback(seg(tl, t0, t0 + .6))
        if pa <= 0: continue
        cx = 480 + i * 480; w_ = 440
        x0, y0 = cx - w_ / 2, 300 + (1 - k) * 26
        card(d, [x0, y0, x0 + w_, y0 + 620], r=26)
        d.ellipse([x0 + 28, y0 + 26, x0 + 84, y0 + 82], fill=ac + (int(70 * pa),))
        bx, by = x0 + 56, y0 + 54
        if i == 0:
            d.rounded_rectangle([bx - 14, by - 14, bx + 14, by + 14], radius=5, outline=(255, 255, 255, int(230 * pa)), width=3)
            d.line([bx - 7, by - 5, bx + 7, by - 5], fill=(255, 255, 255, int(230 * pa)), width=3)
            d.line([bx - 7, by + 3, bx + 4, by + 3], fill=(255, 255, 255, int(230 * pa)), width=3)
        elif i == 1:
            d.rounded_rectangle([bx - 14, by - 12, bx + 14, by + 8], radius=5, outline=(255, 255, 255, int(230 * pa)), width=3)
            d.line([bx - 8, by + 16, bx + 8, by + 16], fill=(255, 255, 255, int(230 * pa)), width=3)
        else:
            d.rounded_rectangle([bx - 12, by - 12, bx + 12, by + 12], radius=4, outline=(255, 255, 255, int(230 * pa)), width=3)
            d.line([bx - 4, by - 12, bx - 4, by - 4], fill=(255, 255, 255, int(230 * pa)), width=3)
            d.line([bx + 4, by + 4, bx + 12, by + 12], fill=(255, 255, 255, int(230 * pa)), width=3)
        d.text((x0 + 102, y0 + 56), tt, font=F(38, True), fill=(255, 255, 255, int(255 * pa)), anchor="lm")
        d.text((x0 + 30, y0 + 112), desc, font=F(25), fill=(168, 178, 212, int(230 * pa)), anchor="lm")
        lt = tl - t0
        if i == 0:
            rows = ["富文本图文", "外部链接", "活动日程"]
            for r_, name in enumerate(rows):
                ra = eo(seg(lt, .3 + r_ * .35, .6 + r_ * .35)); yy = y0 + 170 + r_ * 118
                hl = math.sin(lt * 1.6 - r_ * 2.1) > .55
                d.rounded_rectangle([x0 + 26, yy, x0 + w_ - 26, yy + 96], radius=14,
                                    fill=(99, 140, 255, int(46 * ra)) if hl else (255, 255, 255, int(16 * ra)))
                d.ellipse([x0 + 46, yy + 30, x0 + 74, yy + 58], fill=ac + (int(200 * ra),))
                d.text((x0 + 92, yy + 32), name, font=F(27), fill=(240, 244, 255, int(235 * ra)), anchor="lm")
                d.rounded_rectangle([x0 + 92, yy + 62, x0 + 242, yy + 70], radius=4, fill=(255, 255, 255, int(36 * ra)))
                ax, ay = x0 + w_ - 52, yy + 44
                d.line([ax - 6, ay - 9, ax + 4, ay], fill=(150, 160, 195, int(200 * ra)), width=3)
                d.line([ax + 4, ay, ax - 6, ay + 9], fill=(150, 160, 195, int(200 * ra)), width=3)
        elif i == 1:
            for r_ in range(2):
                ra = eo(seg(lt, .3 + r_ * .3, .6 + r_ * .3)); yy = y0 + 160 + r_ * 86
                d.rounded_rectangle([x0 + 26, yy, x0 + w_ - 26, yy + 64], radius=12, fill=(255, 255, 255, int(18 * ra)))
                d.text((x0 + 46, yy + 32), ["姓名", "手机号"][r_], font=F(24), fill=(190, 200, 235, int(230 * ra)), anchor="lm")
                if r_ == 1:
                    if math.sin(lt * 7) > 0:
                        d.line([x0 + 180, yy + 18, x0 + 180, yy + 46], fill=(120, 200, 255, int(230 * ra)), width=2)
                    d.text((x0 + 118, yy + 32), "138****", font=F(24), fill=(240, 244, 255, int(220 * ra)), anchor="lm")
                else:
                    d.text((x0 + 118, yy + 32), "张三", font=F(24), fill=(240, 244, 255, int(220 * ra)), anchor="lm")
            d.rounded_rectangle([x0 + 26, y0 + 350, x0 + w_ - 26, y0 + 404], radius=16, fill=(99, 140, 255, int(235 * pa)))
            d.text((x0 + w_ / 2, y0 + 376), "立即报名", font=F(27, True), fill=(255, 255, 255, int(255 * pa)), anchor="mm")
            ca = eo(seg(lt, 1.6, 2.0))
            d.rounded_rectangle([x0 + 26, y0 + 430, x0 + w_ - 26, y0 + 486], radius=14,
                                outline=(52, 211, 153, int(190 * ca)), width=2)
            d.text((x0 + w_ / 2, y0 + 458), "一键导出 Excel  ↓", font=F(24), fill=(120, 230, 180, int(235 * ca)), anchor="mm")
        else:
            qx, qy = x0 + w_ / 2 - 100, y0 + 150
            ra = eo(seg(lt, .3, .7))
            d.rounded_rectangle([qx - 14, qy - 14, qx + 214, qy + 214], radius=14, fill=(255, 255, 255, int(240 * ra)))
            ov.paste(QRCODE.convert("RGBA"), (int(qx), int(qy)))
            cy2 = qy + ((lt * 95) % 228)
            d.line([qx, cy2, qx + 200, cy2], fill=(52, 211, 153, int(210 * ra)), width=4)
            cyc = lt % 3.2
            base = int(lt / 3.2) * 3.2
            if cyc > 2.0:
                ca = eback(seg(lt, base + 2.0, base + 2.3)); r = int(26 * ca)
                if r > 2:
                    d.ellipse([qx + 100 - r, qy + 100 - r, qx + 100 + r, qy + 100 + r], fill=(52, 211, 153, 240))
                    d.line([qx + 90, qy + 100, qx + 97, qy + 108], fill=(255, 255, 255, 255), width=4)
                    d.line([qx + 97, qy + 108, qx + 111, qy + 91], fill=(255, 255, 255, 255), width=4)
                aa = seg(lt, base + 2.35, base + 2.6) * (1 - seg(lt, base + 3.0, base + 3.2))
                d.text((x0 + w_ / 2, qy + 244), "签到成功", font=F(26, True), fill=(120, 230, 180, min(255, int(240 * aa))), anchor="mm")
            d.rounded_rectangle([x0 + 26, y0 + 500, x0 + w_ - 26, y0 + 552], radius=14, outline=(255, 255, 255, int(60 * pa)), width=2)
            d.text((x0 + w_ / 2, y0 + 526), "支持跨班补签", font=F(24), fill=(190, 200, 235, int(225 * pa)), anchor="mm")
    pick_sub(d, SUBS[1], tl, dur)
    return Image.alpha_composite(img.convert("RGBA"), ov).convert("RGB")

# ---------- 场景 4：独特优势 ----------
def scene4(tl, dur):
    img = base_frame(START[3] + tl)
    ov = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(ov)
    logo(d); progress(d, START[3] + tl)
    at = eo(seg(tl, .15, .9))
    shadow_text(d, (W / 2, 155 + int((1 - at) * 22)), "为什么选择微站系统", F(58, True), (255, 255, 255, int(255 * at)))
    d.rounded_rectangle([W / 2 - 90 * at, 205, W / 2 + 90 * at, 209], radius=2, fill=(99, 140, 255, int(220 * at)))
    left = [("模板一键套用", "多套风格模板 · 秒级建站"),
            ("模块级权限", "不同成员 · 看到不同模块"),
            ("实时数据统计", "PV / UV / 报名 实时看板")]
    for i, (tt, desc) in enumerate(left):
        t0 = 1.5 + i * 1.0; pa = eo(seg(tl, t0, t0 + .5))
        if pa <= 0: continue
        x0, y0 = 150, 268 + i * 186
        card(d, [x0, y0, x0 + 750, y0 + 160], r=22)
        d.rounded_rectangle([x0 + 30, y0 + 52, x0 + 78, y0 + 100], radius=12, fill=(99, 140, 255, int(60 * pa)))
        d.text((x0 + 54, y0 + 76), str(i + 1), font=F(30, True), fill=(150, 180, 255, int(255 * pa)), anchor="mm")
        d.text((x0 + 104, y0 + 58), tt, font=F(34, True), fill=(255, 255, 255, int(250 * pa)), anchor="lm")
        d.text((x0 + 104, y0 + 110), desc, font=F(25), fill=(168, 178, 212, int(230 * pa)), anchor="lm")
        if i == 0:
            for j, g in enumerate([(236, 110, 173), (168, 120, 255), (240, 150, 90)]):
                ja = eo(seg(tl, t0 + .25 + j * .12, t0 + .45 + j * .12))
                d.rounded_rectangle([x0 + 560 + j * 56 - int((1 - ja) * 20), y0 + 36, x0 + 606 + j * 56, y0 + 116], radius=8, fill=g + (int(200 * ja),))
        if i == 1:
            for j, c in enumerate([BLUE, PURPLE, GREEN]):
                ja = eo(seg(tl, t0 + .25 + j * .12, t0 + .45 + j * .12))
                d.ellipse([x0 + 566 + j * 56, y0 + 40, x0 + 600 + j * 56, y0 + 74], fill=c + (int(190 * ja),))
                d.rounded_rectangle([x0 + 560 + j * 56, y0 + 90, x0 + 606 + j * 56, y0 + 98], radius=4, fill=(255, 255, 255, int(40 * ja)))
        if i == 2:
            vals = [.35, .6, .45, .8, .65, .95]
            for j, v in enumerate(vals):
                ja = eo(seg(tl, t0 + .2 + j * .09, t0 + .5 + j * .09))
                bh = int(58 * v * ja)
                d.rounded_rectangle([x0 + 566 + j * 28, y0 + 104 - bh, x0 + 584 + j * 28, y0 + 104], radius=4,
                                    fill=(99, 140, 255, int(220 * ja)) if j % 2 == 0 else (34, 211, 238, int(220 * ja)))
    t0 = 5.2; pa = eo(seg(tl, t0, t0 + .5))
    if pa > 0:
        x0, y0 = 980, 268
        card(d, [x0, y0, x0 + 790, y0 + 250], r=22)
        d.text((x0 + 34, y0 + 52), "编辑页内置 AI 一键生图", font=F(34, True), fill=(255, 255, 255, int(250 * pa)), anchor="lm")
        d.text((x0 + 34, y0 + 106), "打开编辑器，输入一句话直接生成", font=F(24), fill=(168, 178, 212, int(230 * pa)), anchor="lm")
        chips = ["KV 主视觉", "背景图", "分享图", "模块图标"]
        for j, c in enumerate(chips):
            ca = eback(seg(tl, t0 + .4 + j * .3, t0 + .8 + j * .3))
            if ca <= 0: continue
            cx = x0 + 92 + j * 190; cy = y0 + 182; s = .8 + .2 * ca
            d.rounded_rectangle([cx - 78 * s, cy - 30 * s, cx + 78 * s, cy + 30 * s], radius=16,
                                fill=(99, 140, 255, int(52 * ca)), outline=(150, 180, 255, int(120 * ca)), width=2)
            sparkle(d, cx - 52, cy, 9, int(200 * ca))
            d.text((cx + 14, cy), c, font=F(24), fill=(225, 232, 255, int(240 * ca)), anchor="mm")
    t0 = 7.6; pa = eo(seg(tl, t0, t0 + .5))
    if pa > 0:
        x0, y0 = 980, 548
        card(d, [x0, y0, x0 + 790, y0 + 160], r=22)
        d.text((x0 + 34, y0 + 52), "开放 / 关闭时间自动控制", font=F(34, True), fill=(255, 255, 255, int(250 * pa)), anchor="lm")
        d.text((x0 + 34, y0 + 108), "到点自动开放 · 到点自动关闭", font=F(24), fill=(168, 178, 212, int(230 * pa)), anchor="lm")
        cyc = (tl - t0) % 3.0; on = cyc < 1.5
        if cyc < 1.5:
            k = eio(min(cyc / .4, 1)) if cyc < .8 else 1 - eio(max(0, (cyc - 1.1)) / .4)
            k = clamp01(k)
        else:
            k = 1 - eio((cyc - 1.5) / .4)
        tx, ty = x0 + 668, y0 + 92
        d.rounded_rectangle([tx - 52, ty - 26, tx + 52, ty + 26], radius=26,
                            fill=(52, 211, 153, int(235 * pa)) if on else (90, 100, 130, int(160 * pa)))
        kx = tx - 24 + 48 * k
        d.ellipse([kx - 20, ty - 20, kx + 20, ty + 20], fill=(255, 255, 255, int(255 * pa)))
        st = "09:00 自动开放" if on else "18:00 自动关闭"
        aa = min(1.0, abs(cyc - 1.5) * 3)
        d.text((tx - 72, ty), st, font=F(26), fill=(225, 232, 255, int(235 * pa * aa)), anchor="rm")
    t0 = 9.4; pa = eo(seg(tl, t0, t0 + .6))
    if pa > 0:
        f = F(42, True); w_ = d.textlength("从搭建到运营，一站搞定", font=f)
        shadow_text(d, (W / 2, 852 + int((1 - pa) * 16)), "从搭建到运营，一站搞定", f, (255, 255, 255, int(250 * pa)))
        d.rounded_rectangle([W / 2 - w_ / 2 - 70 * pa, 846, W / 2 - w_ / 2 - 50 * pa, 850], radius=2, fill=(99, 140, 255, int(220 * pa)))
        d.rounded_rectangle([W / 2 + w_ / 2 + 50 * pa, 846, W / 2 + w_ / 2 + 70 * pa, 850], radius=2, fill=(139, 92, 246, int(220 * pa)))
    pick_sub(d, SUBS[2], tl, dur)
    return Image.alpha_composite(img.convert("RGBA"), ov).convert("RGB")

# ---------- 场景 5：行动号召 ----------
def scene5(tl, dur):
    img = base_frame(START[4] + tl)
    ov = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(ov)
    logo(d); progress(d, START[4] + tl)
    def content(sd, pw, ph):
        sd.rounded_rectangle([14, 14, pw - 14, 328], radius=14, fill=(40, 55, 120, 255))
        for i in range(3):
            yy = 344 + i * 92
            sd.rounded_rectangle([14, yy, pw - 14, yy + 76], radius=12, fill=(255, 255, 255, 24))
            sd.rounded_rectangle([26, yy + 14, 146, yy + 30], radius=6, fill=(255, 255, 255, 70))
            sd.rounded_rectangle([26, yy + 42, 216, yy + 54], radius=5, fill=(255, 255, 255, 42))
    phone(img, ov, content, cx=600, cy=580, ph=680)
    hero = HERO5.convert("RGBA")
    ov.paste(hero, (600 - PW5 // 2 + 14, 580 - 340 + 14))
    a1 = eo(seg(tl, .25, .95)); a2 = eo(seg(tl, .65, 1.35))
    shadow_text(d, (1255, 400 + int((1 - a1) * 26)), "下一个活动", F(84, True), (255, 255, 255, int(255 * a1)))
    shadow_text(d, (1255, 520 + int((1 - a2) * 26)), "就用微站系统", F(84, True), (160, 190, 255, int(255 * a2)))
    qa = eo(seg(tl, 1.5, 2.1))
    if qa > 0:
        qx, qy = 1125, 620
        card(d, [qx, qy, qx + 260, qy + 300], r=22, fill=(255, 255, 255, int(246 * qa)))
        ov.paste(QRCODE.convert("RGBA"), (qx + 30, qy + 22))
        d.text((qx + 130, qy + 246), "扫码体验", font=F(28, True), fill=(20, 28, 60, int(255 * qa)), anchor="mm")
        d.text((qx + 130, qy + 280), "wm.meetotour.com", font=F(19), fill=(90, 100, 130, int(235 * qa)), anchor="mm")
    if tl > 4.2:
        ka = seg(tl, 4.2, 5.0)
        d.rectangle([0, 0, W, H], fill=(5, 8, 22, int(255 * ka)))
        ta = eo(seg(tl, 4.5, 5.3))
        shadow_text(d, (W / 2, 470), "微站系统", F(104, True), (255, 255, 255, int(255 * ta)))
        shadow_text(d, (W / 2, 590), "让活动搭建更简单", F(42), (170, 180, 215, int(240 * ta)))
    else:
        pick_sub(d, SUBS[3], tl, dur)
    return Image.alpha_composite(img.convert("RGBA"), ov).convert("RGB")

SCENES = [scene1, scene2, scene3, scene4, scene5]

def render_frame(t):
    i = 4
    for k in range(5):
        if t < START[k] + DUR[k]:
            i = k; break
    tl = t - START[i]
    XF = 0.4
    if i > 0 and tl < XF / 2:
        k = eio((tl + XF / 2) / XF)
        f_out = SCENES[i - 1](DUR[i - 1] - (XF / 2 - tl), DUR[i - 1])
        f_in = SCENES[i](tl, DUR[i])
        return Image.blend(f_out, f_in, k)
    return SCENES[i](tl, DUR[i])

# ---------- 音频 ----------
SR = 44100
def read_audio(path):
    raw = subprocess.run([FF, "-v", "error", "-i", path, "-f", "f32le", "-ac", "1", "-ar", str(SR), "pipe:1"],
                         capture_output=True).stdout
    return np.frombuffer(raw, np.float32).copy()

def build_bgm(total):
    n = int(total * SR); tt = np.arange(n) / SR; bgm = np.zeros(n)
    chords = [[130.81, 164.81, 196.00, 246.94], [98.00, 123.47, 146.83, 196.00],
              [110.00, 130.81, 164.81, 220.00], [87.31, 110.00, 130.81, 174.61]]
    seglen = 4.0; k = 0
    while k * seglen < total:
        ch = chords[k % 4]; t0 = k * seglen
        i0, i1 = int(t0 * SR), min(int((t0 + seglen + 1.2) * SR), n)
        if i0 >= n: break
        t2 = tt[i0:i1] - t0
        env = np.minimum(1, t2 / .9) * np.clip((seglen + 1.2 - t2) / 1.2, 0, 1)
        s = np.zeros(len(t2))
        for j, fr in enumerate(ch):
            s += np.sin(2 * np.pi * fr * t2 + j * .7) + .3 * np.sin(2 * np.pi * fr * 2 * t2)
        bgm[i0:i1] += s / len(ch) * env * .8
        bgm[i0:i1] += np.sin(2 * np.pi * ch[0] / 2 * t2) * .35 * env
        k += 1
    step = 0
    while step * .5 < total:
        t0 = step * .5; ch = chords[int(t0 / seglen) % 4]
        fr = ch[step % 4] * 2
        i0 = int(t0 * SR); ln = int(.4 * SR)
        if i0 + ln > n: break
        t2 = np.arange(ln) / SR
        bgm[i0:i0 + ln] += np.sin(2 * np.pi * fr * t2) * np.exp(-t2 * 7) * .16
        step += 1
    return bgm

def make_audio():
    n = int(TOTAL * SR); mix = np.zeros(n)
    for i in range(5):
        a = read_audio(os.path.join(BASE, "tts/s%d.aiff" % (i + 1)))
        s0 = int((START[i] + 0.35) * SR)
        e = min(s0 + len(a), n)
        fade = np.ones(len(a)); f = int(.02 * SR)
        fade[:f] = np.linspace(0, 1, f); fade[-f:] = np.linspace(1, 0, f)
        mix[s0:e] += a[:e - s0] * fade[:e - s0]
    bgm = build_bgm(TOTAL)
    duck = np.ones(n)
    for i in range(5):
        s0 = int((START[i] + 0.15) * SR); e0 = int((START[i] + 0.35 + NARR[i] + 0.3) * SR)
        duck[s0:e0] = 0.0
    k = int(.5 * SR)
    kern = np.hanning(k * 2 + 1); kern /= kern.sum()
    duck = np.convolve(duck, kern, "same")
    bgm *= (1 - .6 * (1 - duck)) * .11
    out = mix + bgm
    fi = int(.5 * SR); fo = int(1.8 * SR)
    out[:fi] *= np.linspace(0, 1, fi)
    out[-fo:] *= np.linspace(1, 0, fo) ** 1.5
    peak = np.abs(out).max()
    if peak > 0: out = out / peak * .88
    pcm = (np.stack([out, out], axis=1) * 32767).astype(np.int16)
    with wave.open(os.path.join(BASE, "audio.wav"), "wb") as wf:
        wf.setnchannels(2); wf.setsampwidth(2); wf.setframerate(SR)
        wf.writeframes(pcm.tobytes())

# ---------- 主流程 ----------
def main():
    if "--preview" in sys.argv:
        for t in [1.5, 4.0, 9.0, 13.0, 18.0, 26.0, 33.0, 41.0, 48.0, 55.0, 60.0, 64.0]:
            if t >= TOTAL: continue
            render_frame(t).resize((960, 540)).save(os.path.join(BASE, "preview_%04.1f.jpg" % t), quality=88)
        print("previews saved, TOTAL=%.2fs" % TOTAL); return
    make_audio()
    print("audio ok (%.2fs)" % TOTAL, flush=True)
    vpath = os.path.join(BASE, "video_nosound.mp4")
    proc = subprocess.Popen(
        [FF, "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", "%dx%d" % (W, H), "-r", str(FPS),
         "-i", "pipe:", "-c:v", "libx264", "-preset", "medium", "-crf", "19", "-pix_fmt", "yuv420p", vpath],
        stdin=subprocess.PIPE, stdout=subprocess.DEVNULL,
        stderr=open(os.path.join(BASE, "render_err.log"), "wb"))
    nf = int(TOTAL * FPS)
    for i in range(nf):
        proc.stdin.write(render_frame(i / FPS).tobytes())
        if i % 300 == 0: print("frame %d/%d" % (i, nf), flush=True)
    proc.stdin.close(); proc.wait()
    out = os.path.join(BASE, "weizhan-promo.mp4")
    subprocess.run([FF, "-y", "-i", vpath, "-i", os.path.join(BASE, "audio.wav"),
                    "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", out],
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
    print("DONE:", out)

if __name__ == "__main__":
    main()
