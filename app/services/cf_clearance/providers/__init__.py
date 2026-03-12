from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Sequence

__all__ = ["CfResult", "CfProvider", "create_providers"]


@dataclass(frozen=True)
class CfResult:
    """cf_clearance 获取结果（不可变）"""

    clearance: str
    user_agent: str


class CfProvider(ABC):
    """cf_clearance Provider 基类"""

    @abstractmethod
    async def solve(self, url: str) -> CfResult:
        """获取 cf_clearance，返回 CfResult"""
        ...


def create_providers(provider_names: Sequence[str]) -> list[CfProvider]:
    """根据配置名称列表创建 Provider 实例"""
    from .bypass import CloudflareBypassProvider
    from .flaresolverr import FlareSolverrProvider
    from .local import LocalSolverProvider

    registry: dict[str, type[CfProvider]] = {
        "flaresolverr": FlareSolverrProvider,
        "local": LocalSolverProvider,
        "cloudflare_bypass": CloudflareBypassProvider,
    }

    providers: list[CfProvider] = []
    for name in provider_names:
        cls = registry.get(name)
        if cls:
            providers.append(cls())
    return providers
