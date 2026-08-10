"""静态二维码编码/校验工具

编码规则（服务端生成，同一用户同一微站内容恒定）:
    ck1.{base64url(site_id:account_id)}.{signature}

- version: 编码版本, 当前为 1
- payload: site_id:account_id 的 base64url 编码
- signature: HMAC-SHA256(secret, version + "." + payload) 取前 12 位 hex
- 不含手机号、姓名等明文敏感信息；密钥仅服务端持有

示例: ck1.MTI6MzQ1Ng.a1b2c3d4e5f6
"""
import base64
import hashlib
import hmac

from app.config import settings

CODE_VERSION = "1"
CODE_PREFIX = "ck"
SIGNATURE_LENGTH = 12  # 12 hex = 48bit, 足够防误扫

# 常量以字节形式使用
_ENCODING = "utf-8"


def _sign(version: str, payload: str) -> str:
    """计算 HMAC-SHA256 签名并取前 SIGNATURE_LENGTH 位 hex"""
    message = f"{version}.{payload}".encode(_ENCODING)
    digest = hmac.new(settings.SECRET_KEY.encode(_ENCODING), message, hashlib.sha256).hexdigest()
    return digest[:SIGNATURE_LENGTH]


def _encode_payload(site_id: int, account_id: int) -> str:
    """将 site_id:account_id 编码为 base64url（无填充）"""
    raw = f"{site_id}:{account_id}".encode(_ENCODING)
    return base64.urlsafe_b64encode(raw).rstrip(b"=").decode(_ENCODING)


def _decode_payload(payload_b64: str) -> tuple[int, int] | None:
    """解码 base64url 载荷为 (site_id, account_id)，失败返回 None"""
    try:
        padding = "=" * (-len(payload_b64) % 4)
        raw = base64.urlsafe_b64decode(payload_b64 + padding)
        text = raw.decode(_ENCODING)
        site_id_str, account_id_str = text.split(":", 1)
        return int(site_id_str), int(account_id_str)
    except (ValueError, TypeError, base64.binascii.Error):
        return None


def generate_checkin_code(site_id: int, account_id: int) -> str:
    """生成静态签到二维码内容（同一用户同一微站恒定）"""
    payload = _encode_payload(site_id, account_id)
    signature = _sign(CODE_VERSION, payload)
    return f"{CODE_PREFIX}{CODE_VERSION}.{payload}.{signature}"


def parse_checkin_code(code: str) -> tuple[int, int] | None:
    """解析并校验静态签到二维码

    返回 (site_id, account_id)；格式错误或签名不合法返回 None
    """
    if not code or not code.startswith(CODE_PREFIX):
        return None
    try:
        prefix, payload, signature = code.split(".")
    except ValueError:
        return None
    if prefix != f"{CODE_PREFIX}{CODE_VERSION}":
        return None
    # 常量时间比较，避免时序侧信道
    expected = _sign(CODE_VERSION, payload)
    if not hmac.compare_digest(signature, expected):
        return None
    return _decode_payload(payload)
