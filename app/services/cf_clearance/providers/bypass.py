from __future__ import annotations

import httpx

from app.core.config import get_config
from app.core.logger import logger

from . import CfProvider, CfResult

__all__ = ["CloudflareBypassProvider"]


class CloudflareBypassProvider(CfProvider):
    """CloudflareBypassForScraping Provider"""

    async def solve(self, url: str) -> CfResult:
        endpoint = get_config("cf_clearance.cloudflare_bypass.endpoint", "http://127.0.0.1:8880")

        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.get(f"{endpoint}/cookies", params={"url": url})
            resp.raise_for_status()

        data = resp.json()
        cookies = data.get("cookies", {})
        clearance = cookies.get("cf_clearance", "")

        if not clearance:
            raise RuntimeError("CloudflareBypass: cf_clearance not found in response")

        user_agent = data.get("user_agent", "")
        logger.info("CloudflareBypass: cf_clearance obtained")
        return CfResult(clearance=clearance, user_agent=user_agent)
