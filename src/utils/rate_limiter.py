import asyncio
from collections import defaultdict
from datetime import datetime, timedelta
from typing import Optional


class RateLimiter:
    def __init__(self, user_limit: int, group_limit: int, window_seconds: int):
        self.user_limit = user_limit
        self.group_limit = group_limit
        self.window = timedelta(seconds=window_seconds)
        self._user_requests: dict[int, list[datetime]] = defaultdict(list)
        self._group_requests: dict[int, list[datetime]] = defaultdict(list)
        self._cooldowns: dict[int, datetime] = {}
        self._lock = asyncio.Lock()
        self._last_cleanup = datetime.now()
        self._cleanup_interval = timedelta(minutes=10)
    
    async def _cleanup_old_requests(self, requests: list[datetime]) -> list[datetime]:
        now = datetime.now()
        return [req for req in requests if now - req < self.window]
    
    async def _periodic_cleanup(self) -> None:
        now = datetime.now()
        if now - self._last_cleanup < self._cleanup_interval:
            return
        
        self._last_cleanup = now
        
        empty_users = [uid for uid, reqs in self._user_requests.items() if not reqs]
        for uid in empty_users:
            del self._user_requests[uid]
        
        empty_groups = [cid for cid, reqs in self._group_requests.items() if not reqs]
        for cid in empty_groups:
            del self._group_requests[cid]
        
        expired_cooldowns = [uid for uid, exp in self._cooldowns.items() if now >= exp]
        for uid in expired_cooldowns:
            del self._cooldowns[uid]
    
    async def check_rate_limit(self, user_id: int, chat_id: int, is_group: bool = False) -> tuple[bool, Optional[int]]:
        async with self._lock:
            now = datetime.now()
            
            await self._periodic_cleanup()
            
            if user_id in self._cooldowns:
                if now < self._cooldowns[user_id]:
                    remaining = (self._cooldowns[user_id] - now).seconds
                    return False, remaining
                else:
                    del self._cooldowns[user_id]
            
            self._user_requests[user_id] = await self._cleanup_old_requests(
                self._user_requests[user_id]
            )
            
            if len(self._user_requests[user_id]) >= self.user_limit:
                cooldown_time = 30
                self._cooldowns[user_id] = now + timedelta(seconds=cooldown_time)
                return False, cooldown_time
            
            if is_group:
                self._group_requests[chat_id] = await self._cleanup_old_requests(
                    self._group_requests[chat_id]
                )
                
                if len(self._group_requests[chat_id]) >= self.group_limit:
                    return False, 10
                
                self._group_requests[chat_id].append(now)
            
            self._user_requests[user_id].append(now)
            return True, None
    
    async def get_user_usage(self, user_id: int) -> dict:
        async with self._lock:
            self._user_requests[user_id] = await self._cleanup_old_requests(
                self._user_requests[user_id]
            )
            return {
                "used": len(self._user_requests[user_id]),
                "limit": self.user_limit,
                "remaining": self.user_limit - len(self._user_requests[user_id]),
                "window_seconds": self.window.seconds
            }
    
    async def reset_user(self, user_id: int) -> None:
        async with self._lock:
            self._user_requests[user_id] = []
            if user_id in self._cooldowns:
                del self._cooldowns[user_id]
