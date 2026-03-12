"""Token 池管理"""

import random
from typing import Dict, List, Optional, Iterator

from app.services.token.models import TokenInfo, TokenStatus, TokenPoolStats


class TokenPool:
    """Token 池（管理一组 Token）"""
    
    def __init__(self, name: str):
        self.name = name
        self._tokens: Dict[str, TokenInfo] = {}
    
    def add(self, token: TokenInfo):
        """添加 Token"""
        self._tokens[token.token] = token
    
    def remove(self, token_str: str) -> bool:
        """删除 Token"""
        if token_str in self._tokens:
            del self._tokens[token_str]
            return True
        return False
        
    def get(self, token_str: str) -> Optional[TokenInfo]:
        """获取 Token"""
        return self._tokens.get(token_str)
        
    def select(self, bucket: str = "normal") -> Optional[TokenInfo]:
        """
        选择一个可用 Token
        策略:
        1. 选择 active 状态且有配额的 token
        2. 优先选择剩余额度最多的
        3. 如果额度相同，随机选择（避免并发冲突）

        单次遍历完成筛选 + 最大值查找。
        """
        if bucket == "heavy":
            best_unknown: List[TokenInfo] = []
            best_known: List[TokenInfo] = []
            best_quota = 0
            for t in self._tokens.values():
                if t.status not in (TokenStatus.ACTIVE, TokenStatus.COOLING) or t.heavy_quota == 0:
                    continue
                if t.heavy_quota < 0:
                    best_unknown.append(t)
                elif t.heavy_quota > best_quota:
                    best_quota = t.heavy_quota
                    best_known = [t]
                elif t.heavy_quota == best_quota:
                    best_known.append(t)

            if best_unknown:
                return random.choice(best_unknown)
            return random.choice(best_known) if best_known else None

        # normal bucket — single pass
        candidates: List[TokenInfo] = []
        max_quota = 0
        for t in self._tokens.values():
            if t.status != TokenStatus.ACTIVE or t.quota <= 0:
                continue
            if t.quota > max_quota:
                max_quota = t.quota
                candidates = [t]
            elif t.quota == max_quota:
                candidates.append(t)

        return random.choice(candidates) if candidates else None
        
    def count(self) -> int:
        """Token 数量"""
        return len(self._tokens)
        
    def list(self) -> List[TokenInfo]:
        """获取所有 Token"""
        return list(self._tokens.values())
    
    def get_stats(self) -> TokenPoolStats:
        """获取池统计信息"""
        stats = TokenPoolStats(total=len(self._tokens))
        
        for token in self._tokens.values():
            stats.total_quota += token.quota
            
            if token.status == TokenStatus.ACTIVE:
                stats.active += 1
            elif token.status == TokenStatus.DISABLED:
                stats.disabled += 1
            elif token.status == TokenStatus.EXPIRED:
                stats.expired += 1
            elif token.status == TokenStatus.COOLING:
                stats.cooling += 1
        
        if stats.total > 0:
            stats.avg_quota = stats.total_quota / stats.total
            
        return stats
        
    def _rebuild_index(self):
        """重建索引（预留接口，用于加载时调用）"""
        pass
        
    def __iter__(self) -> Iterator[TokenInfo]:
        return iter(self._tokens.values())


__all__ = ["TokenPool"]
