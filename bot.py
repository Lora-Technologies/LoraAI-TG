import asyncio
import signal
import sys
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler as TelegramCommandHandler,
    MessageHandler as TelegramMessageHandler,
    filters
)

from config import config
from src.database import Database
from src.services import AIService, SearchService
from src.handlers import MessageHandler, CommandHandler, AdminHandler
from src.utils import setup_logger, RateLimiter

logger = setup_logger("bot", config.LOG_LEVEL)


class TelegramBot:
    def __init__(self):
        self.database = Database(config.DATABASE_PATH)
        self.rate_limiter = RateLimiter(
            user_limit=config.RATE_LIMIT_USER,
            group_limit=config.RATE_LIMIT_GROUP,
            window_seconds=config.RATE_LIMIT_WINDOW
        )
        
        self.ai_service = AIService(
            api_key=config.LORA_API_KEY,
            base_url=config.LORA_BASE_URL,
            model=config.MODEL,
            max_tokens=config.MAX_TOKENS,
            system_prompt=config.SYSTEM_PROMPT
        )
        
        self.search_service = SearchService()
        
        self.message_handler = MessageHandler(
            ai_service=self.ai_service,
            search_service=self.search_service,
            database=self.database,
            rate_limiter=self.rate_limiter,
            bot_username=config.BOT_USERNAME,
            context_window=config.CONTEXT_WINDOW_SIZE
        )
        
        self.command_handler = CommandHandler(
            search_service=self.search_service,
            database=self.database,
            rate_limiter=self.rate_limiter
        )
        
        self.admin_handler = AdminHandler(
            database=self.database,
            rate_limiter=self.rate_limiter,
            admin_ids=config.ADMIN_USER_IDS
        )
        
        self.app = None
    
    async def start(self) -> None:
        logger.info_ctx("Starting bot...", action="bot_start")
        
        await self.database.connect()
        logger.info_ctx("Database connected", action="db_connect")
        
        self.app = Application.builder().token(config.TELEGRAM_BOT_TOKEN).build()
        
        self.app.add_handler(TelegramCommandHandler("start", self.command_handler.start))
        self.app.add_handler(TelegramCommandHandler("help", self.command_handler.help))
        self.app.add_handler(TelegramCommandHandler("search", self.command_handler.search))
        self.app.add_handler(TelegramCommandHandler("clear", self.command_handler.clear))
        self.app.add_handler(TelegramCommandHandler("stats", self.command_handler.stats))
        
        self.app.add_handler(TelegramCommandHandler("ban", self.admin_handler.ban))
        self.app.add_handler(TelegramCommandHandler("unban", self.admin_handler.unban))
        self.app.add_handler(TelegramCommandHandler("adminstats", self.admin_handler.admin_stats))
        self.app.add_handler(TelegramCommandHandler("health", self.admin_handler.health))
        
        self.app.add_handler(
            TelegramMessageHandler(
                filters.TEXT & ~filters.COMMAND,
                self.message_handler.handle_message
            )
        )
        
        self.app.add_error_handler(self.error_handler)
        
        logger.info_ctx("Bot started successfully", action="bot_ready")
        
        await self.app.initialize()
        await self.app.start()
        await self.app.updater.start_polling(allowed_updates=Update.ALL_TYPES)
        
        stop_event = asyncio.Event()
        
        def signal_handler(*args):
            stop_event.set()
        
        if sys.platform != "win32":
            loop = asyncio.get_event_loop()
            for sig in (signal.SIGINT, signal.SIGTERM):
                loop.add_signal_handler(sig, signal_handler)
        else:
            signal.signal(signal.SIGINT, signal_handler)
        
        await stop_event.wait()
        await self.stop()
    
    async def stop(self) -> None:
        logger.info_ctx("Stopping bot...", action="bot_stop")
        
        if self.app:
            await self.app.updater.stop()
            await self.app.stop()
            await self.app.shutdown()
        
        await self.database.close()
        logger.info_ctx("Bot stopped", action="bot_stopped")
    
    async def error_handler(self, update: Update, context) -> None:
        logger.error_ctx(
            f"Exception while handling an update: {context.error}",
            action="error",
            extra_data={"error": str(context.error)}
        )


async def main():
    if not config.TELEGRAM_BOT_TOKEN:
        print("ERROR: TELEGRAM_BOT_TOKEN is not set")
        return
    
    if not config.LORA_API_KEY:
        print("ERROR: LORA_API_KEY is not set")
        return
    
    if not config.BOT_USERNAME:
        print("ERROR: BOT_USERNAME is not set")
        return
    
    bot = TelegramBot()
    await bot.start()


if __name__ == "__main__":
    asyncio.run(main())
