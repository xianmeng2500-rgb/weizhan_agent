#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""生成案例内容用的「实拍感」照片（如婚礼相册、场地实拍）

- 请求 1130×640（单边 ≥512 的 DashScope 限制），缩到 750×425 存 seed_assets/demo/
- 无文字原图自动备份到 _ai_raw/，改 prompt 重跑即可重新生成

用法:
    cd backend && .venv/bin/python tools/gen_case_photos.py
    .venv/bin/python tools/gen_case_photos.py --only img_wedding_venue
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
REQ_W, REQ_H = 1130, 640
OUT_W, OUT_H = 750, 425
MAX_RETRY = 3

TAIL = ("摄影级写实质感，真实婚礼现场跟拍风格，柔和暖光，浅景深，高级感；"
        "画面中不要出现任何文字、字母、数字、LOGO、水印，也不要出现人物面部")

# (文件名, 提示词)
PHOTOS = [
    ("img_wedding_venue",
     "婚礼宴会厅全景，香槟金与莫兰迪绿主题布置，中央舞台白色鲜花拱门与纱幔，"
     "成排圆桌铺米白色桌布，每桌中央有高低错落的鲜花桌花，暖色吊灯，通透大气"),
    ("img_wedding_detail",
     "婚礼桌花与喜糖伴手礼特写，香槟色玫瑰与绿色尤加利叶桌花，"
     "烫金喜字礼盒与丝带，木质桌面，窗边自然光，精致温馨"),
    ("img_course_room",
     "明亮整洁的少儿编程教室，木质桌椅排列，桌上放着笔记本电脑与彩色积木教具，"
     "墙面有作品展示板与绿植，窗外明亮自然光，活泼的蓝橙配色，现代教育空间"),
    ("img_summit_past",
     "大型会议厅观众席视角，深蓝色舞台灯光与巨幅LED背景墙，"
     "密集的座椅与观众背影剪影，专业会议氛围，科技感深蓝紫色调"),
    ("img_annual_stage",
     "企业年会舞台布置，红色与金色主视觉背景板，舞台两侧金色灯柱与花艺，"
     "台下圆桌铺红桌布与烛台，暖色灯光，喜庆热烈"),
    ("img_store_products",
     "两杯咖啡并排放在木质桌面上，一杯桂花拿铁带拉花，一杯燕麦拿铁，"
     "旁有咖啡豆与桂花枝点缀，浅景深，暖色调，产品摄影风格"),
    ("img_chamber_hall",
     "现代政务会议中心建筑外观，玻璃幕墙与石材立面，入口广场与旗杆，"
     "蓝天白云，庄重大气，建筑摄影风格"),
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
            if img.size != (OUT_W, OUT_H):
                img = img.resize((OUT_W, OUT_H), Image.LANCZOS)
            img.save(raw_path, "PNG", optimize=True)
            shutil.copy2(raw_path, os.path.join(OUT_DIR, f"{name}.png"))
            print(f"  [生成] {name}.png {OUT_W}×{OUT_H} "
                  f"{os.path.getsize(raw_path) // 1024}KB（第 {attempt} 次）")
            return True
        except Exception as e:  # noqa: BLE001
            print(f"  [重试 {attempt}/{MAX_RETRY}] {name}: {e}", file=sys.stderr)
            if attempt < MAX_RETRY:
                time.sleep(3 * attempt)
    print(f"  [失败] {name}", file=sys.stderr)
    return False


def main():
    p = argparse.ArgumentParser(description="案例内容照片生成")
    p.add_argument("--only", help="只生成指定一张（不含 .png）")
    p.add_argument("--dry-run", action="store_true")
    args = p.parse_args()

    targets = [t for t in PHOTOS if not args.only or t[0] == args.only]
    if not targets:
        sys.exit(f"--only 未匹配到，可选：{', '.join(t[0] for t in PHOTOS)}")

    if args.dry_run:
        for name, prompt in targets:
            print(f"\n[{name}] {REQ_W}×{REQ_H} -> {OUT_W}×{OUT_H}\n{prompt}，{TAIL}")
        return

    api_key, model = get_ai_config()
    print(f"模型: {model} | 共 {len(targets)} 张，串行执行\n")
    import time as _t
    ok = []
    for i, (name, prompt) in enumerate(targets):
        if i:
            _t.sleep(4)
        ok.append(gen_one(api_key, model, name, prompt))
    print(f"\n完成 {sum(ok)}/{len(targets)} -> {OUT_DIR}")
    if not all(ok):
        sys.exit(1)


if __name__ == "__main__":
    main()
