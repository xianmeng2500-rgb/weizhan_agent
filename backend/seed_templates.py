"""内置通用模板种子脚本：上传 KV/预览图到 OSS 并写入 site_templates（幂等，可重复执行）

用法（在 backend 目录下）:
    python seed_templates.py            # 写入 5 个内置模板
    python seed_templates.py --dry-run  # 只打印将要执行的操作，不改库不上传

说明:
- 以「模板名称」判重：已存在同名模板则更新其内容，不存在则插入
- 图片上传到 OSS 的 weizhan/template/ 目录下
- 不修改用户自建模板（name 不同的记录一概不碰）
"""
import json
import os
import sys
from datetime import datetime, timezone

import oss2
import pymysql

BASE = os.path.dirname(os.path.abspath(__file__))
ASSET_DIR = os.path.join(BASE, 'seed_assets', 'templates')

env = {}
for line in open(os.path.join(BASE, '.env'), encoding='utf-8'):
    line = line.strip()
    if line and not line.startswith('#') and '=' in line:
        k, v = line.split('=', 1)
        env[k.strip()] = v.strip()

DEFAULT_TITLE_CONFIG = {
    'enabled': False, 'text': '', 'font': 'sans', 'color': '#333333',
    'size': 20, 'bold': True, 'position_x': 5, 'position_y': 5, 'max_width': 80,
}

OSS_PREFIX = 'weizhan/template'

# ---- 5 个内置通用模板定义 ----
TEMPLATES = [
    {
        'name': '通用商务活动模板',
        'description': '经典蓝紫九宫格，覆盖活动全流程入口，适合发布会、论坛、展会、周年庆等通用活动场景',
        'template_key': 'classic', 'layout': 'grid', 'kv': 'kv_business.png', 'preview': 'preview_business.png',
        'share_title': '活动微站', 'share_subtitle': '查看议程、报名与出行指南',
        'modules': [
            ('活动介绍', 'img-bule-2.png', 'rich_text'), ('日程安排', 'img-bule-1.png', 'schedule'),
            ('在线报名', 'img-bule-5.png', 'registration_form'), ('嘉宾介绍', 'img-bule-7.png', 'rich_text'),
            ('交通指引', 'img-bule-3.png', 'rich_text'), ('住宿安排', 'img-bule-8.png', 'rich_text'),
            ('晚宴安排', 'img-bule-6.png', 'rich_text'), ('注意事项', 'img-bule-4.png', 'rich_text'),
            ('我的二维码', 'img-bule-9.png', 'qrcode'),
        ],
    },
    {
        'name': '峰会论坛模板',
        'description': '暗夜科技风按钮列表，议程、嘉宾、报名一站式入口，适合行业峰会、技术大会、圆桌论坛',
        'template_key': 'dark', 'layout': 'button', 'kv': 'kv_forum.png', 'preview': 'preview_forum.png',
        'share_title': '峰会微站', 'share_subtitle': '议程 · 嘉宾 · 报名',
        'modules': [
            ('会议议程', 'img-bule-1.png', 'schedule'), ('嘉宾阵容', 'img-bule-7.png', 'rich_text'),
            ('参会报名', 'img-bule-5.png', 'registration_form'), ('会场交通', 'img-bule-3.png', 'rich_text'),
            ('周边住宿', 'img-bule-8.png', 'rich_text'), ('商务晚宴', 'img-bule-6.png', 'rich_text'),
            ('会议须知', 'img-bule-4.png', 'rich_text'), ('我的二维码', 'img-bule-9.png', 'qrcode'),
        ],
    },
    {
        'name': '节日庆典模板',
        'description': '节日红金九宫格，喜庆大气，适合周年庆、开业庆典、年会、答谢会等喜庆场景',
        'template_key': 'festive', 'layout': 'grid', 'kv': 'kv_festival.png', 'preview': 'preview_festival.png',
        'share_title': '庆典微站', 'share_subtitle': '诚邀莅临，共襄盛举',
        'modules': [
            ('庆典介绍', 'img-bule-2.png', 'rich_text'), ('活动议程', 'img-bule-1.png', 'schedule'),
            ('立即报名', 'img-bule-5.png', 'registration_form'), ('嘉宾介绍', 'img-bule-7.png', 'rich_text'),
            ('庆典晚宴', 'img-bule-6.png', 'rich_text'), ('交通指引', 'img-bule-3.png', 'rich_text'),
            ('住宿安排', 'img-bule-8.png', 'rich_text'), ('我的二维码', 'img-bule-9.png', 'qrcode'),
        ],
    },
    {
        'name': '会务出行接待模板',
        'description': '清新出行风按钮列表，行程、接待、缴费一页搞定，适合商务考察、研学旅行、客户接待',
        'template_key': 'default', 'layout': 'button', 'kv': 'kv_travel.png', 'preview': 'preview_travel.png',
        'share_title': '会务出行微站', 'share_subtitle': '行程 · 接待 · 指南',
        'modules': [
            ('行程安排', 'img-trip-4.png', 'schedule'), ('接机接站', 'img-trip-3.png', 'rich_text'),
            ('签到报到', 'img-trip-1.png', 'rich_text'), ('活动通知', 'img-trip-5.png', 'rich_text'),
            ('会场位置', 'img-trip-7.png', 'rich_text'), ('住宿安排', 'img-trip-6.png', 'rich_text'),
            ('精彩瞬间', 'img-trip-8.png', 'rich_text'), ('费用缴纳', 'img-trip-9.png', 'rich_text'),
        ],
    },
    {
        'name': '企业内部服务模板',
        'description': '简洁九宫格，公告、制度、班车、餐厅等内部服务入口，适合企业行政、员工之家、园区服务',
        'template_key': 'default', 'layout': 'grid', 'kv': 'kv_corp.png', 'preview': 'preview_corp.png',
        'share_title': '企业服务微站', 'share_subtitle': '公告 · 服务 · 支持',
        'modules': [
            ('企业介绍', 'img-baier-4.jpg', 'rich_text'), ('公司动态', 'img-baier-3.jpg', 'rich_text'),
            ('制度文档', 'img-baier-2.jpg', 'rich_text'), ('意见反馈', 'img-baier-1.jpg', 'rich_text'),
            ('通勤班车', 'img-baier-5.jpg', 'rich_text'), ('员工餐厅', 'img-baier-6.jpg', 'rich_text'),
            ('团队风采', 'img-baier-7.jpg', 'rich_text'), ('企业文化', 'img-baier-8.jpg', 'rich_text'),
            ('客服支持', 'img-baier-9.jpg', 'rich_text'),
        ],
    },
]

ICON_BASE = 'https://simon-node-test.oss-cn-hangzhou.aliyuncs.com/weizhan/icon/'


def build_modules(modules):
    return [
        {'title': title, 'icon': ICON_BASE + icon, 'content_type': ctype,
         'is_active': True, 'sort_order': idx}
        for idx, (title, icon, ctype) in enumerate(modules)
    ]


def main():
    dry = '--dry-run' in sys.argv
    conn = pymysql.connect(host=env['DB_HOST'], port=int(env['DB_PORT']), user=env['DB_USER'],
                           password=env['DB_PASSWORD'], database=env['DB_NAME'], charset='utf8mb4')
    cur = conn.cursor()

    cur.execute("SELECT id FROM users WHERE role='super_admin' ORDER BY id LIMIT 1")
    row = cur.fetchone()
    creator = row[0] if row else None

    auth = oss2.Auth(env['OSS_ACCESS_KEY_ID'], env['OSS_ACCESS_KEY_SECRET'])
    bucket = oss2.Bucket(auth, 'https://' + env['OSS_ENDPOINT'], env['OSS_BUCKET_NAME'])

    print(f"目标库: {env['DB_HOST']}/{env['DB_NAME']}   OSS: {env['OSS_BUCKET_NAME']}   dry_run={dry}")
    for idx, t in enumerate(TEMPLATES):
        # 1) 上传 KV / 预览图
        urls = {}
        for field, fname in (('kv_image', t['kv']), ('preview_image', t['preview'])):
            local = os.path.join(ASSET_DIR, fname)
            key = f"{OSS_PREFIX}/{fname}"
            urls[field] = f"https://{env['OSS_BUCKET_NAME']}.{env['OSS_ENDPOINT']}/{key}"
            if dry:
                print(f"  [dry] 上传 {fname} -> {key}")
            else:
                bucket.put_object_from_file(key, local)
                print(f"  [oss] {fname} -> {key}")

        payload = {
            'name': t['name'],
            'description': t['description'],
            'template_key': t['template_key'],
            'layout': t['layout'],
            'kv_image': urls['kv_image'],
            'title_config': json.dumps(DEFAULT_TITLE_CONFIG, ensure_ascii=False),
            'background_color': None,
            'background_image': None,
            'share_image': None,
            'share_title': t['share_title'],
            'share_subtitle': t['share_subtitle'],
            'preview_image': urls['preview_image'],
            'modules_config': json.dumps(build_modules(t['modules']), ensure_ascii=False),
            'status': 'active',
            'sort_order': idx + 1,
        }

        cur.execute("SELECT id FROM site_templates WHERE name=%s", (t['name'],))
        exist = cur.fetchone()
        if exist:
            sets = ', '.join(f"{k}=%s" for k in payload)
            sql = f"UPDATE site_templates SET {sets} WHERE id=%s"
            args = list(payload.values()) + [exist[0]]
            action = f"更新 id={exist[0]}"
        else:
            # is_system 在库中为 NOT NULL 且无默认值，插入时显式给 0（保留用户可删除）
            # created_at/updated_at 的默认值只在 ORM 层，裸 SQL 插入必须显式赋值，
            # 否则留 NULL 会让 SiteTemplateOut 校验失败、整个模板列表接口 500
            now = datetime.now(timezone.utc).replace(tzinfo=None)
            cols = list(payload.keys()) + ['is_system', 'created_by', 'created_at', 'updated_at']
            sql = (f"INSERT INTO site_templates ({', '.join(cols)}) "
                   f"VALUES ({', '.join(['%s'] * len(cols))})")
            args = list(payload.values()) + [0, creator, now, now]
            action = "新增"
        print(f"{action} 模板「{t['name']}」({t['template_key']}/{t['layout']}, "
              f"预置模块 {len(t['modules'])} 个, sort_order={payload['sort_order']})")
        if not dry:
            cur.execute(sql, args)
    if not dry:
        conn.commit()
        cur.execute("SELECT id, name, template_key, layout, sort_order FROM site_templates "
                    "ORDER BY sort_order, id")
        print('\n=== 当前全部模板 ===')
        for r in cur.fetchall():
            print('  ', r)
    conn.close()
    print('\n完成' + ('（dry-run，未实际写入）' if dry else ''))


if __name__ == '__main__':
    main()
