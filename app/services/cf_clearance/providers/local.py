from __future__ import annotations

import httpx

from app.core.config import get_config
from app.core.logger import logger

from . import CfProvider, CfResult

__all__ = ["LocalSolverProvider"]


class LocalSolverProvider(CfProvider):
    """Local Solver Provider（复用现有 turnstile solver）"""

    async def solve(self, url: str) -> CfResult:
        endpoint = get_config("cf_clearance.local.endpoint", "http://127.0.0.1:18888")

        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.get(f"{endpoint}/cf_clearance", params={"url": url})
            resp.raise_for_status()

        data = resp.json()

        if data.get("status") != "ok":
            raise RuntimeError(f"LocalSolver failed: {data}")

        clearance = data.get("cf_clearance", "")
        if not clearance:
            raise RuntimeError("LocalSolver: empty cf_clearance in response")

        user_agent = data.get("user_agent", "")
        logger.info("LocalSolver: cf_clearance obtained")
        return CfResult(clearance=clearance, user_agent=user_agent)
