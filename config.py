import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    TELEGRAM_BOT_TOKEN: str = os.getenv("TELEGRAM_BOT_TOKEN", "")
    LORA_API_KEY: str = os.getenv("LORA_API_KEY", "")
    LORA_BASE_URL: str = "https://api.loratech.dev/v1"
    
    BOT_USERNAME: str = os.getenv("BOT_USERNAME", "")
    ADMIN_USER_IDS: list[int] = [
        int(uid.strip()) 
        for uid in os.getenv("ADMIN_USER_IDS", "").split(",") 
        if uid.strip()
    ]
    
    RATE_LIMIT_USER: int = int(os.getenv("RATE_LIMIT_USER", "10"))
    RATE_LIMIT_GROUP: int = int(os.getenv("RATE_LIMIT_GROUP", "30"))
    RATE_LIMIT_WINDOW: int = int(os.getenv("RATE_LIMIT_WINDOW", "60"))
    
    CONTEXT_WINDOW_SIZE: int = int(os.getenv("CONTEXT_WINDOW_SIZE", "20"))
    MAX_TOKENS: int = int(os.getenv("MAX_TOKENS", "4096"))
    MODEL: str = os.getenv("MODEL", "gemini-2.5-pro")
    
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    
    DATABASE_PATH: str = os.getenv("DATABASE_PATH", "data/bot.db")
    
    SYSTEM_PROMPT: str = """Sen yardımcı bir AI asistanısın. Şu an 2025 yılındayız.
Kullanıcıların sorularına doğru, net ve yararlı yanıtlar veriyorsun.
Web arama sonuçları sağlandığında, bu bilgileri kullanarak güncel ve doğru bilgiler sunuyorsun.
Türkçe sorulara Türkçe, İngilizce sorulara İngilizce yanıt veriyorsun.
Tarih ve zaman gerektiren sorularda güncel bilgi ver."""


config = Config()
