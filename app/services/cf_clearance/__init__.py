"""cf_clearance 自动刷新模块"""
from __future__ import annotations

from app.services.cf_clearance.refresher import CfClearanceRefresher

_refresher: CfClearanceRefresher | None = None


def start_refresher() -> CfClearanceRefresher:
    global _refresher
    _refresher = CfClearanceRefresher()
    _refresher.start()
    return _refresher


async def stop_refresher():
    global _refresher
    if _refresher:
        await _refresher.stop()
        _refresher = None


__all__ = ["CfClearanceRefresher", "start_refresher", "stop_refresher"]
