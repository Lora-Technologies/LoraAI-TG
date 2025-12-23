import aiosqlite
import os
from datetime import datetime
from typing import Optional
from .models import User, Message, Stats


class Database:
    def __init__(self, db_path: str):
        self.db_path = db_path
        self._connection: Optional[aiosqlite.Connection] = None
    
    async def connect(self) -> None:
        db_dir = os.path.dirname(self.db_path)
        if db_dir:
            os.makedirs(db_dir, exist_ok=True)
        self._connection = await aiosqlite.connect(self.db_path)
        self._connection.row_factory = aiosqlite.Row
        await self._create_tables()
    
    async def close(self) -> None:
        if self._connection:
            await self._connection.close()
    
    async def _create_tables(self) -> None:
        await self._connection.executescript("""
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                first_name TEXT NOT NULL,
                last_name TEXT,
                is_banned INTEGER DEFAULT 0,
                is_whitelisted INTEGER DEFAULT 0,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );
            
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                chat_id INTEGER NOT NULL,
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                tokens_used INTEGER DEFAULT 0,
                created_at TEXT NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users (user_id)
            );
            
            CREATE TABLE IF NOT EXISTS stats (
                user_id INTEGER PRIMARY KEY,
                total_messages INTEGER DEFAULT 0,
                total_tokens INTEGER DEFAULT 0,
                total_searches INTEGER DEFAULT 0,
                last_active TEXT NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users (user_id)
            );
            
            CREATE INDEX IF NOT EXISTS idx_messages_user_chat ON messages (user_id, chat_id);
            CREATE INDEX IF NOT EXISTS idx_messages_created ON messages (created_at);
        """)
        await self._connection.commit()
    
    async def get_or_create_user(self, user_id: int, username: str, first_name: str, last_name: str) -> User:
        cursor = await self._connection.execute(
            "SELECT * FROM users WHERE user_id = ?", (user_id,)
        )
        row = await cursor.fetchone()
        
        if row:
            await self._connection.execute(
                "UPDATE users SET username = ?, first_name = ?, last_name = ?, updated_at = ? WHERE user_id = ?",
                (username, first_name, last_name, datetime.now().isoformat(), user_id)
            )
            await self._connection.commit()
            return User(
                user_id=row["user_id"],
                username=row["username"],
                first_name=row["first_name"],
                last_name=row["last_name"],
                is_banned=bool(row["is_banned"]),
                is_whitelisted=bool(row["is_whitelisted"]),
                created_at=datetime.fromisoformat(row["created_at"]),
                updated_at=datetime.now()
            )
        
        now = datetime.now().isoformat()
        await self._connection.execute(
            "INSERT INTO users (user_id, username, first_name, last_name, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?)",
            (user_id, username, first_name, last_name, now, now)
        )
        await self._connection.commit()
        
        await self._connection.execute(
            "INSERT INTO stats (user_id, last_active) VALUES (?, ?)",
            (user_id, now)
        )
        await self._connection.commit()
        
        return User(
            user_id=user_id,
            username=username,
            first_name=first_name,
            last_name=last_name
        )
    
    async def is_user_banned(self, user_id: int) -> bool:
        cursor = await self._connection.execute(
            "SELECT is_banned FROM users WHERE user_id = ?", (user_id,)
        )
        row = await cursor.fetchone()
        return bool(row["is_banned"]) if row else False
    
    async def ban_user(self, user_id: int) -> bool:
        result = await self._connection.execute(
            "UPDATE users SET is_banned = 1, updated_at = ? WHERE user_id = ?",
            (datetime.now().isoformat(), user_id)
        )
        await self._connection.commit()
        return result.rowcount > 0
    
    async def unban_user(self, user_id: int) -> bool:
        result = await self._connection.execute(
            "UPDATE users SET is_banned = 0, updated_at = ? WHERE user_id = ?",
            (datetime.now().isoformat(), user_id)
        )
        await self._connection.commit()
        return result.rowcount > 0
    
    async def add_message(self, user_id: int, chat_id: int, role: str, content: str, tokens_used: int = 0) -> None:
        await self._connection.execute(
            "INSERT INTO messages (user_id, chat_id, role, content, tokens_used, created_at) VALUES (?, ?, ?, ?, ?, ?)",
            (user_id, chat_id, role, content, tokens_used, datetime.now().isoformat())
        )
        await self._connection.commit()
    
    async def get_conversation_history(self, user_id: int, chat_id: int, limit: int = 20) -> list[dict]:
        cursor = await self._connection.execute(
            """SELECT role, content FROM messages 
               WHERE user_id = ? AND chat_id = ? 
               ORDER BY created_at DESC LIMIT ?""",
            (user_id, chat_id, limit)
        )
        rows = await cursor.fetchall()
        return [{"role": row["role"], "content": row["content"]} for row in reversed(rows)]
    
    async def clear_conversation(self, user_id: int, chat_id: int) -> int:
        result = await self._connection.execute(
            "DELETE FROM messages WHERE user_id = ? AND chat_id = ?",
            (user_id, chat_id)
        )
        await self._connection.commit()
        return result.rowcount
    
    async def update_stats(self, user_id: int, messages: int = 0, tokens: int = 0, searches: int = 0) -> None:
        await self._connection.execute(
            """UPDATE stats SET 
               total_messages = total_messages + ?,
               total_tokens = total_tokens + ?,
               total_searches = total_searches + ?,
               last_active = ?
               WHERE user_id = ?""",
            (messages, tokens, searches, datetime.now().isoformat(), user_id)
        )
        await self._connection.commit()
    
    async def get_user_stats(self, user_id: int) -> Optional[Stats]:
        cursor = await self._connection.execute(
            "SELECT * FROM stats WHERE user_id = ?", (user_id,)
        )
        row = await cursor.fetchone()
        if not row:
            return None
        return Stats(
            user_id=row["user_id"],
            total_messages=row["total_messages"],
            total_tokens=row["total_tokens"],
            total_searches=row["total_searches"],
            last_active=datetime.fromisoformat(row["last_active"])
        )
    
    async def get_global_stats(self) -> dict:
        cursor = await self._connection.execute(
            """SELECT 
               COUNT(*) as total_users,
               SUM(total_messages) as total_messages,
               SUM(total_tokens) as total_tokens,
               SUM(total_searches) as total_searches
               FROM stats"""
        )
        row = await cursor.fetchone()
        
        banned_cursor = await self._connection.execute(
            "SELECT COUNT(*) as banned FROM users WHERE is_banned = 1"
        )
        banned_row = await banned_cursor.fetchone()
        
        return {
            "total_users": row["total_users"] or 0,
            "total_messages": row["total_messages"] or 0,
            "total_tokens": row["total_tokens"] or 0,
            "total_searches": row["total_searches"] or 0,
            "banned_users": banned_row["banned"] or 0
        }
    
    async def get_user_by_username(self, username: str) -> Optional[User]:
        cursor = await self._connection.execute(
            "SELECT * FROM users WHERE username = ?", (username.lstrip("@"),)
        )
        row = await cursor.fetchone()
        if not row:
            return None
        return User(
            user_id=row["user_id"],
            username=row["username"],
            first_name=row["first_name"],
            last_name=row["last_name"],
            is_banned=bool(row["is_banned"]),
            is_whitelisted=bool(row["is_whitelisted"]),
            created_at=datetime.fromisoformat(row["created_at"]),
            updated_at=datetime.fromisoformat(row["updated_at"])
        )
