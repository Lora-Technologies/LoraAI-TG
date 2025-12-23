from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


@dataclass
class User:
    user_id: int
    username: Optional[str]
    first_name: str
    last_name: Optional[str]
    is_banned: bool = False
    is_whitelisted: bool = False
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)


@dataclass
class Message:
    id: Optional[int]
    user_id: int
    chat_id: int
    role: str
    content: str
    tokens_used: int = 0
    created_at: datetime = field(default_factory=datetime.now)


@dataclass
class Stats:
    user_id: int
    total_messages: int = 0
    total_tokens: int = 0
    total_searches: int = 0
    last_active: datetime = field(default_factory=datetime.now)
