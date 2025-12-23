import re
from typing import Optional
from telegram import Message


def extract_bot_mention(text: str, bot_username: str) -> Optional[str]:
    if not text or not bot_username:
        return None
    
    pattern = rf"@{re.escape(bot_username)}\s*(.*)"
    match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
    
    if match:
        return match.group(1).strip() or None
    
    if text.lower().startswith(f"@{bot_username.lower()}"):
        remaining = text[len(bot_username) + 1:].strip()
        return remaining or None
    
    return None


def is_reply_to_bot(message: Message, bot_id: int) -> bool:
    if not message.reply_to_message:
        return False
    if not message.reply_to_message.from_user:
        return False
    return message.reply_to_message.from_user.id == bot_id


def format_search_results(results: list[dict], max_results: int = 5) -> str:
    if not results:
        return ""
    
    formatted = []
    for i, result in enumerate(results[:max_results], 1):
        title = result.get("title", "")
        body = result.get("body", result.get("snippet", ""))
        url = result.get("href", result.get("url", ""))
        
        formatted.append(f"{i}. <b>{title}</b>\n{body}\nKaynak: {url}")
    
    return "\n\n".join(formatted)


def format_search_context(results: list[dict], max_results: int = 5) -> str:
    if not results:
        return ""
    
    context_parts = ["Web arama sonuçları:"]
    for i, result in enumerate(results[:max_results], 1):
        title = result.get("title", "")
        body = result.get("body", result.get("snippet", ""))
        url = result.get("href", result.get("url", ""))
        context_parts.append(f"[{i}] {title}: {body} (Kaynak: {url})")
    
    return "\n".join(context_parts)


def truncate_text(text: str, max_length: int = 4000) -> str:
    if len(text) <= max_length:
        return text
    return text[:max_length - 3] + "..."


def escape_markdown(text: str) -> str:
    escape_chars = ['_', '*', '[', ']', '(', ')', '~', '`', '>', '#', '+', '-', '=', '|', '{', '}', '.', '!']
    for char in escape_chars:
        text = text.replace(char, f'\\{char}')
    return text
