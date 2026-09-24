#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""给 AI 生成的案例图合成标题文字（渐变压暗 + 主标题 + 副标题）

- 输入: seed_assets/demo/ 下的无文字原图（KV 750×340 / 背景图 750×1334）
- 备份: 无文字原图统一放在 seed_assets/demo/_ai_raw/，改文案只需重跑本脚本
- 输出: 原地覆盖同名文件

两种布局：
- bottom（KV 横幅）: 文字在左下，安全带纵向 y≈140–254（H5 全图可见；案例集卡片
  object-fit:cover 居中裁切可见区约 y79–258，不裁字）
- top（整页背景图）: 文字在左上（背景图上部是标题留白区），竖向手机不裁顶

用法:
    cd backend && .venv/bin/python tools/kv_add_text.py            # 全部合成
    .venv/bin/python tools/kv_add_text.py --only kv_wedding        # 只处理一张
"""
import argparse
import os
import shutil
import sys

from PIL import Image, ImageDraw, ImageFont

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT_DIR = os.path.join(BASE, "seed_assets", "demo")
RAW_DIR = os.path.join(OUT_DIR, "_ai_raw")
FONT_PATH = "/System/Library/Fonts/Hiragino Sans GB.ttc"
FONT_BOLD = 2   # W6
FONT_REG = 0    # W3

# (文件名, 布局, 主标题, 副标题, 强调色)  文案与站点内模块内容一致
TEXTS = [
    ("kv_wedding",  "bottom", "张伟 & 李娜 婚礼邀请",     "2026.10.18 · 杭州云栖厅",                 "#D8B26E"),
    ("kv_course",   "bottom", "少儿编程秋季班招生",       "10 月 12 日开课 · 限额 20 人 · 可免费试听", "#FF8A3D"),
    ("kv_summit",   "bottom", "2026 数字零售行业峰会",    "10.24 - 10.25 · 上海国际会议中心",        "#5EA0FF"),
    ("kv_annual",   "bottom", "同心同行 · 2026 公司年会", "2027.1.16 · 星河宴会厅",                  "#F2B84B"),
    ("kv_store",    "bottom", "星空咖啡 · 会员日",        "10.1 - 10.7 · 全国 12 家门店同步",        "#C98A5B"),
    ("kv_chamber",  "bottom", "青年企业家协会换届大会",   "11.8 · 市会议中心 A 厅",                  "#7FB2F0"),
    ("bg_store",    "poster", "星空咖啡 · 会员日",        "10.1 - 10.7 · 全国 12 家门店同步",        "#C98A5B"),
]

# 版式（各布局自带的基准尺寸下）
LAYOUTS = {
    # KV 750×340：底部渐变（起点 y95 → 底部 alpha195）
    "bottom": dict(x=34, bar_y=140, title_base=218, sub_base=254,
                   title_size=38, sub_size=19,
                   scrim=("down", 95, 195, 1.5)),
    # 背景图 750×1334：顶部渐变（顶部 alpha210 → y620 处 0）
    "top": dict(x=60, bar_y=152, title_base=232, sub_base=274,
                title_size=42, sub_size=21,
                scrim=("up", 620, 210, 1.2)),
    # 背景图 750×1334：左下海报式（H5 背景为 fixed+cover，竖屏手机完整显示纵向，
    # 页面上部被模块卡片遮挡，因此标题放左下干净台面；底部向上渐变）
    "poster": dict(x=60, bar_y=1138, title_base=1226, sub_base=1286,
                   title_size=44, sub_size=21,
                   scrim=("down", 820, 200, 1.5)),
}
SCRIM_RGB = (8, 12, 24)


def backup_raw(name: str):
    src = os.path.join(OUT_DIR, f"{name}.png")
    os.makedirs(RAW_DIR, exist_ok=True)
    dst = os.path.join(RAW_DIR, f"{name}.png")
    if not os.path.exists(dst) and os.path.exists(src):
        shutil.copy2(src, dst)
    return dst if os.path.exists(dst) else None


def hex_rgb(h: str) -> tuple[int, int, int]:
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))  # type: ignore


def draw_scrim(d: ImageDraw.ImageDraw, w: int, h: int, scrim):
    """scrim=(方向, 起点, 极值 alpha, gamma)：down=向下加深，up=从顶部向下减淡"""
    direction, start, max_a, gamma = scrim
    for y in range(h):
        if direction == "down":
            if y < start:
                continue
            t = (y - start) / (h - start)
            a = int(max_a * (t ** gamma))
        else:  # up：顶部最强，到 start 处衰减为 0
            if y > start:
                continue
            t = y / start
            a = int(max_a * ((1 - t) ** gamma))
        d.line([(0, y), (w, y)], fill=SCRIM_RGB + (a,))


def compose(name: str, layout: str, title: str, sub: str, accent: str) -> bool:
    raw = backup_raw(name)
    if not raw:
        print(f"  [跳过] {name}.png 不存在", file=sys.stderr)
        return False
    L = LAYOUTS[layout]
    img = Image.open(raw).convert("RGBA")
    w, h = img.size

    ov = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(ov)
    draw_scrim(d, w, h, L["scrim"])

    f_title = ImageFont.truetype(FONT_PATH, L["title_size"], index=FONT_BOLD)
    f_sub = ImageFont.truetype(FONT_PATH, L["sub_size"], index=FONT_REG)
    x, bar_y, tb, sb = L["x"], L["bar_y"], L["title_base"], L["sub_base"]
    d.rounded_rectangle([x, bar_y, x + 50, bar_y + 7], radius=3.5,
                        fill=hex_rgb(accent) + (255,))

    for text, font, base_y, color, sw in ((title, f_title, tb, (255, 255, 255, 255), 2),
                                          (sub, f_sub, sb, (255, 255, 255, 240), 1)):
        d.text((x + 1, base_y + 2), text, font=font, fill=(0, 0, 0, 110), anchor="ls")
        d.text((x, base_y), text, font=font, fill=color, anchor="ls",
               stroke_width=sw, stroke_fill=(0, 0, 0, 130))

    Image.alpha_composite(img, ov).convert("RGB").save(
        os.path.join(OUT_DIR, f"{name}.png"), "PNG", optimize=True)
    print(f"  [合成] {name}.png（{layout}）「{title}」/「{sub}」")
    return True


def main():
    p = argparse.ArgumentParser(description="KV / 背景图标题文字合成")
    p.add_argument("--only", help="只处理指定的一张（不含 .png）")
    args = p.parse_args()

    targets = [t for t in TEXTS if not args.only or t[0] == args.only]
    if not targets:
        sys.exit(f"--only 未匹配到，可选：{', '.join(t[0] for t in TEXTS)}")

    ok = [compose(*t) for t in targets]
    print(f"\n完成 {sum(ok)}/{len(targets)} 张 -> {OUT_DIR}（无文字原图在 _ai_raw/）")
    if not all(ok):
        sys.exit(1)


if __name__ == "__main__":
    main()
