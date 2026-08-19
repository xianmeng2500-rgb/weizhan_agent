"""IP 限流: 滑动窗口内存实现

防护目标:
- /auth/login、/p/sites/*/login: bcrypt 密码校验是 CPU 密集操作, 防暴力破解 + CPU DoS
- /p/sites/*/access、/click、表单提交: 每请求 INSERT 一次数据库, 防刷爆数据库连接池
- /p/sites/*/wechat-signature、/ai/*: 同步调用外部 API(微信/大模型), 防刷爆外部配额
- 其余接口: 通用兜底

实现说明:
- 基于进程内存的滑动窗口计数, 仅适用于单 worker 部署(默认 uvicorn 单进程)。
  多 worker / 多实例部署时需替换为共享存储(如 Redis), 见 _Storage 注释。
- IP 获取: nginx 反代后 request.client.host 是 127.0.0.1, 需信任 X-Forwarded-For。
  取最后一个值, 该值是 nginx 通过 $proxy_add_x_forwarded_for 追加的真实远端 IP,
  客户端伪造的前缀无法覆盖它。
"""
import threading
import time
from collections import defaultdict, deque

from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from app.config import settings


def _client_ip(request: Request) -> str:
    """获取客户端真实 IP (优先 X-Forwarded-For 最后一个值)"""
    xff = request.headers.get("x-forwarded-for", "")
    if xff:
        parts = [p.strip() for p in xff.split(",") if p.strip()]
        if parts:
            return parts[-1]
    if request.client:
        return request.client.host
    return "unknown"


class SlidingWindowLimiter:
    """滑动窗口计数器: key 在最近 period 秒内最多允许 max_requests 次"""

    def __init__(self, max_requests: int, period_seconds: int):
        self.max_requests = max_requests
        self.period_seconds = period_seconds
        self._hits: dict[str, deque[float]] = defaultdict(deque)
        self._last_cleanup = time.monotonic()
        self._lock = threading.Lock()

    def allow(self, key: str) -> bool:
        now = time.monotonic()
        with self._lock:
            self._maybe_cleanup(now)
            dq = self._hits[key]
            cutoff = now - self.period_seconds
            while dq and dq[0] <= cutoff:
                dq.popleft()
            if len(dq) >= self.max_requests:
                return False
            dq.append(now)
            return True

    def _maybe_cleanup(self, now: float) -> None:
        """每 60 秒清理一次不活跃的 key, 防止攻击者用大量 IP 撑爆内存"""
        if now - self._last_cleanup < 60:
            return
        self._last_cleanup = now
        cutoff = now - self.period_seconds * 2
        dead = [k for k, dq in self._hits.items() if not dq or dq[-1] <= cutoff]
        for k in dead:
            del self._hits[k]


def _make_limiter(config_key: str) -> SlidingWindowLimiter:
    max_requests = getattr(settings, config_key)
    return SlidingWindowLimiter(max_requests, settings.RATE_LIMIT_WINDOW)


# 分级限流器 (按路径规则命中)
_login_limiter = _make_limiter("RATE_LIMIT_LOGIN_MAX")
_write_limiter = _make_limiter("RATE_LIMIT_WRITE_MAX")
_external_limiter = _make_limiter("RATE_LIMIT_EXTERNAL_MAX")
_default_limiter = _make_limiter("RATE_LIMIT_DEFAULT_MAX")


def _match_limiter(path: str, method: str) -> SlidingWindowLimiter:
    """按路径+方法匹配限流规则, 命中第一个则返回"""
    if "/login" in path:
        return _login_limiter
    if "wechat-signature" in path:
        return _external_limiter
    if path.startswith("/api/v1/ai"):
        return _external_limiter
    # 公开写库接口: 访问日志 / 点击日志 / 表单提交
    if method == "POST" and (
        path.rstrip("/").endswith("/access")
        or path.rstrip("/").endswith("/click")
        or "form-submissions" in path
    ):
        return _write_limiter
    return _default_limiter


class RateLimitMiddleware(BaseHTTPMiddleware):
    """IP 维度限流中间件: 超限返回 429 + Retry-After"""

    async def dispatch(self, request: Request, call_next):
        # 静态资源不限流
        if request.url.path.startswith("/static"):
            return await call_next(request)

        ip = _client_ip(request)
        limiter = _match_limiter(request.url.path, request.method)
        if not limiter.allow(ip):
            return JSONResponse(
                status_code=429,
                content={"detail": "请求过于频繁，请稍后再试"},
                headers={"Retry-After": str(limiter.period_seconds)},
            )
        return await call_next(request)
