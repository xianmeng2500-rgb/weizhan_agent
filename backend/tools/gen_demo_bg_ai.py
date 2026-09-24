#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""生成「整页背景图」风格的案例背景（竖向 750×1334）

与 KV（750×340 横向横幅）不同：背景图是 H5 页面的固定底层（SiteView.vue 的 .bg-layer，
position:fixed + object-fit:cover），模块卡片浮在其上，因此需要
- 竖向构图（手机满屏比例）
- 上部较暗、留出可放标题的干净区域
- 无任何文字/LOGO/水印

用法:
    cd backend && .venv/bin/python tools/gen_demo_bg_ai.py
    .venv/bin/python tools/gen_demo_bg_ai.py --dry-run
"""
import argparse
import io
import os
import shutil
import sys
import time
import urllib.request

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE)

OUT_DIR = os.path.join(BASE, "seed_assets", "demo")
RAW_DIR = os.path.join(OUT_DIR, "_ai_raw")
REQ_W, REQ_H = 750, 1334
MAX_RETRY = 3

TAIL = ("竖向构图，画面重心在下方三分之二，上部三分之一是较暗且干净的墙面与暖色吊灯，"
        "留出可叠加标题的深色区域，浅景深，摄影级写实质感，高级感；"
        "画面中不要出现任何文字、字母、数字、LOGO、水印、招牌")

BGS = [
    ("bg_store",
     "温馨精品咖啡馆内景，深色木质吧台横向贯穿画面中下部，暖黄吊灯与绿植，"
     "手冲壶与滤杯摆在吧台右侧，台面左侧干净空旷，暖棕色调，午后慵懒氛围"),
]


def get_ai_config() -> tuple[str, str]:
    from app.database import SessionLocal
    from app.models.system_config import SystemConfig

    db = SessionLocal()
    try:
        cfg = db.query(SystemConfig).first()
        key = (cfg.ai_api_key if cfg else "") or ""
        model = (cfg.ai_image_model if cfg else "") or "wan2.2-t2i-flash"
    finally:
        db.close()
    if not key:
        sys.exit("数据库中未配置 ai_api_key")
    return key, model


def gen_one(api_key: str, model: str, name: str, prompt: str) -> bool:
    from dashscope import ImageSynthesis
    from PIL import Image

    full = f"{prompt}，{TAIL}"
    os.makedirs(RAW_DIR, exist_ok=True)
    raw_path = os.path.join(RAW_DIR, f"{name}.png")

    for attempt in range(1, MAX_RETRY + 1):
        try:
            rsp = ImageSynthesis.call(api_key=api_key, model=model, prompt=full,
                                      n=1, size=f"{REQ_W}*{REQ_H}")
            if rsp.status_code != 200:
                raise RuntimeError(f"{rsp.status_code} {getattr(rsp, 'message', '')}")
            results = (rsp.output or {}).get("results") or []
            url = results[0].get("url") if results else None
            if not url:
                raise RuntimeError(f"未返回图片 URL: {rsp.output}")

            with urllib.request.urlopen(url, timeout=90) as resp:
                raw = resp.read()
            img = Image.open(io.BytesIO(raw)).convert("RGB")
            if img.size != (REQ_W, REQ_H):
                img = img.resize((REQ_W, REQ_H), Image.LANCZOS)
            img.save(raw_path, "PNG", optimize=True)
            out = os.path.join(OUT_DIR, f"{name}.png")
            shutil.copy2(raw_path, out)
            print(f"  [生成] {name}.png {img.size[0]}×{img.size[1]} "
                  f"{os.path.getsize(raw_path) // 1024}KB（第 {attempt} 次）")
            return True
        except Exception as e:  # noqa: BLE001
            print(f"  [重试 {attempt}/{MAX_RETRY}] {name}: {e}", file=sys.stderr)
            if attempt < MAX_RETRY:
                time.sleep(3 * attempt)
    print(f"  [失败] {name}", file=sys.stderr)
    return False


def main():
    p = argparse.ArgumentParser(description="案例整页背景图生成")
    p.add_argument("--dry-run", action="store_true")
    args = p.parse_args()

    if args.dry_run:
        for name, prompt in BGS:
            print(f"\n[{name}] {REQ_W}×{REQ_H}\n{prompt}，{TAIL}")
        return

    api_key, model = get_ai_config()
    print(f"模型: {model} | 尺寸 {REQ_W}×{REQ_H} | 共 {len(BGS)} 张\n")
    ok = [gen_one(api_key, model, n, pr) for n, pr in BGS]
    print(f"\n完成 {sum(ok)}/{len(BGS)} -> {OUT_DIR}")
    if not all(ok):
        sys.exit(1)


if __name__ == "__main__":
    main()
