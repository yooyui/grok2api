"""
共享 HTTP 请求头模板

所有 Grok API 服务共用的静态请求头在模块加载时构建一次，
每次请求只需覆盖动态字段（Cookie、request-id 等）。
"""

import uuid
from typing import Dict

from app.core.config import get_config
from app.services.grok.statsig import StatsigService


# 静态请求头模板（不可变部分），模块加载时构建一次
_STATIC_HEADERS: Dict[str, str] = {
    "Accept": "*/*",
    "Accept-Encoding": "gzip, deflate, br, zstd",
    "Accept-Language": "zh-CN,zh;q=0.9",
    "Baggage": (
        "sentry-environment=production,"
        "sentry-release=d6add6fb0460641fd482d767a335ef72b9b6abb8,"
        "sentry-public_key=b311e0f2690c81f25e2c4cf6d4f7ce1c"
    ),
    "Cache-Control": "no-cache",
    "Content-Type": "application/json",
    "Origin": "https://grok.com",
    "Pragma": "no-cache",
    "Priority": "u=1, i",
    "Referer": "https://grok.com/",
    "Sec-Ch-Ua": '"Google Chrome";v="136", "Chromium";v="136", "Not(A:Brand";v="24"',
    "Sec-Ch-Ua-Arch": "arm",
    "Sec-Ch-Ua-Bitness": "64",
    "Sec-Ch-Ua-Mobile": "?0",
    "Sec-Ch-Ua-Model": "",
    "Sec-Ch-Ua-Platform": '"macOS"',
    "Sec-Fetch-Dest": "empty",
    "Sec-Fetch-Mode": "cors",
    "Sec-Fetch-Site": "same-origin",
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/136.0.0.0 Safari/537.36"
    ),
}


def build_cookie(token: str) -> str:
    """构建 Cookie 字符串"""
    token = token[4:] if token.startswith("sso=") else token
    cf = get_config("grok.cf_clearance", "")
    return f"sso={token};cf_clearance={cf}" if cf else f"sso={token}"


def build_headers(token: str, referer: str = "https://grok.com/") -> Dict[str, str]:
    """
    构建完整请求头（静态模板 + 动态字段）

    Args:
        token: SSO token
        referer: Referer URL，默认 https://grok.com/
    """
    headers = _STATIC_HEADERS.copy()
    headers["Referer"] = referer
    # cf_clearance 绑定 User-Agent，优先使用获取时配对的 UA
    cf_ua = get_config("grok.cf_user_agent", "")
    if cf_ua:
        headers["User-Agent"] = cf_ua
    headers["x-statsig-id"] = StatsigService.gen_id()
    headers["x-xai-request-id"] = str(uuid.uuid4())
    headers["Cookie"] = build_cookie(token)
    return headers


__all__ = ["build_headers", "build_cookie", "_STATIC_HEADERS"]
