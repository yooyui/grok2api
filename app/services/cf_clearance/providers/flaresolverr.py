from __future__ import annotations

import httpx

from app.core.config import get_config
from app.core.logger import logger

from . import CfProvider, CfResult

__all__ = ["FlareSolverrProvider"]


class FlareSolverrProvider(CfProvider):
    """FlareSolverr / Byparr 兼容 Provider"""

    async def solve(self, url: str) -> CfResult:
        endpoint = get_config("cf_clearance.flaresolverr.endpoint", "http://127.0.0.1:8191/v1")
        max_timeout = get_config("cf_clearance.flaresolverr.max_timeout", 60000)

        timeout = max(30.0, max_timeout / 1000 + 10)

        async with httpx.AsyncClient(timeout=timeout) as client:
            resp = await client.post(
                endpoint,
                json={
                    "cmd": "request.get",
                    "url": url,
                    "maxTimeout": max_timeout,
                    "returnOnlyCookies": True,
                },
            )
            resp.raise_for_status()

        data = resp.json()

        if data.get("status") != "ok":
            msg = data.get("message", "unknown error")
            raise RuntimeError(f"FlareSolverr failed: {msg}")

        solution = data.get("solution", {})
        cookies = solution.get("cookies", [])
        clearance = next(
            (c["value"] for c in cookies if c.get("name") == "cf_clearance"),
            None,
        )

        if not clearance:
            raise RuntimeError("FlareSolverr: cf_clearance cookie not found in response")

        user_agent = solution.get("userAgent", "")
        logger.info("FlareSolverr: cf_clearance obtained")
        return CfResult(clearance=clearance, user_agent=user_agent)
