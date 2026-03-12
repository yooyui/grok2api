"""
cf_clearance 自动刷新器

后台 asyncio task，定时通过 Provider 链获取新的 cf_clearance，
成功后写入运行时配置供 headers.py 使用。
"""
from __future__ import annotations

import asyncio

from app.core.config import config, get_config
from app.core.logger import logger
from app.services.cf_clearance.providers import CfProvider, create_providers

TARGET_URL = "https://grok.com/"


class CfClearanceRefresher:
    def __init__(self):
        self._task: asyncio.Task | None = None
        self._providers: list[CfProvider] = []

    def start(self):
        """启动后台刷新任务"""
        provider_names = get_config(
            "cf_clearance.providers",
            ["local", "flaresolverr", "cloudflare_bypass"],
        )
        self._providers = create_providers(provider_names)
        if not self._providers:
            logger.warning(
                "cf_clearance: no valid providers configured, refresher disabled"
            )
            return
        logger.info(
            f"cf_clearance refresher starting with providers: "
            f"{[type(p).__name__ for p in self._providers]}"
        )
        self._task = asyncio.create_task(self._run())

    async def stop(self):
        """停止后台刷新任务"""
        if self._task and not self._task.done():
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
            logger.info("cf_clearance refresher stopped")

    async def _run(self):
        refresh_interval = get_config("cf_clearance.refresh_interval", 1200)
        max_backoff = get_config("cf_clearance.max_backoff", 300)
        initial_backoff = 30
        failure_backoff = initial_backoff

        try:
            while True:
                success = await self._try_refresh()
                if success:
                    failure_backoff = initial_backoff
                    await asyncio.sleep(refresh_interval)
                else:
                    logger.warning(
                        f"cf_clearance: all providers failed, retrying in {failure_backoff}s"
                    )
                    await asyncio.sleep(failure_backoff)
                    failure_backoff = min(failure_backoff * 2, max_backoff)
        except asyncio.CancelledError:
            logger.debug("cf_clearance refresher task cancelled")

    async def _try_refresh(self) -> bool:
        """尝试所有 Provider，成功返回 True"""
        for provider in self._providers:
            name = type(provider).__name__
            try:
                result = await provider.solve(TARGET_URL)
                # 写入运行时配置（原子操作，无需加锁）
                await config.update(
                    {
                        "grok": {
                            "cf_clearance": result.clearance,
                            "cf_user_agent": result.user_agent,
                        }
                    }
                )
                logger.info(f"cf_clearance refreshed via {name}")
                return True
            except asyncio.CancelledError:
                raise
            except Exception as e:
                logger.warning(f"cf_clearance provider {name} failed: {e}")
                continue
        return False
