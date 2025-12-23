from telegram import Update
from telegram.ext import ContextTypes
from telegram.constants import ChatAction, ParseMode
from src.services import AIService, SearchService
from src.database import Database
from src.utils import RateLimiter, get_logger
from src.utils.helpers import extract_bot_mention, is_reply_to_bot, truncate_text

logger = get_logger("message_handler")


class MessageHandler:
    def __init__(
        self,
        ai_service: AIService,
        search_service: SearchService,
        database: Database,
        rate_limiter: RateLimiter,
        bot_username: str,
        context_window: int
    ):
        self.ai = ai_service
        self.search = search_service
        self.db = database
        self.rate_limiter = rate_limiter
        self.bot_username = bot_username
        self.context_window = context_window
    
    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        message = update.effective_message
        user = update.effective_user
        chat = update.effective_chat
        
        if not message or not message.text or not user:
            return
        
        bot_id = context.bot.id
        is_reply = is_reply_to_bot(message, bot_id)
        mentioned_text = extract_bot_mention(message.text, self.bot_username)
        
        if not is_reply and mentioned_text is None:
            return
        
        user_message = mentioned_text if mentioned_text else message.text
        
        if is_reply and not mentioned_text:
            user_message = message.text
        
        if not user_message.strip():
            return
        
        db_user = await self.db.get_or_create_user(
            user_id=user.id,
            username=user.username or "",
            first_name=user.first_name,
            last_name=user.last_name or ""
        )
        
        if db_user.is_banned:
            logger.warning_ctx(
                "Banned user attempted to use bot",
                user_id=user.id,
                chat_id=chat.id,
                action="banned_attempt"
            )
            return
        
        is_group = chat.type in ["group", "supergroup"]
        allowed, cooldown = await self.rate_limiter.check_rate_limit(
            user_id=user.id,
            chat_id=chat.id,
            is_group=is_group
        )
        
        if not allowed:
            await message.reply_text(
                f"⏳ Rate limit aşıldı. Lütfen {cooldown} saniye bekleyin.",
                parse_mode=ParseMode.HTML
            )
            return
        
        logger.info_ctx(
            f"Processing message",
            user_id=user.id,
            chat_id=chat.id,
            action="message_received",
            extra_data={"message_length": len(user_message)}
        )
        
        await context.bot.send_chat_action(chat_id=chat.id, action=ChatAction.TYPING)
        
        try:
            search_results = None
            if await self.ai.should_search(user_message):
                search_results = await self.search.search_web(user_message)
                if search_results:
                    await self.db.update_stats(user.id, searches=1)
            
            conversation_history = await self.db.get_conversation_history(
                user_id=user.id,
                chat_id=chat.id,
                limit=self.context_window
            )
            
            response, tokens_used = await self.ai.generate_response(
                user_message=user_message,
                conversation_history=conversation_history,
                search_results=search_results
            )
            
            await self.db.add_message(
                user_id=user.id,
                chat_id=chat.id,
                role="user",
                content=user_message
            )
            
            await self.db.add_message(
                user_id=user.id,
                chat_id=chat.id,
                role="assistant",
                content=response,
                tokens_used=tokens_used
            )
            
            await self.db.update_stats(
                user_id=user.id,
                messages=1,
                tokens=tokens_used
            )
            
            response = truncate_text(response, 4000)
            
            await message.reply_text(response)
            
            logger.info_ctx(
                "Response sent",
                user_id=user.id,
                chat_id=chat.id,
                action="response_sent",
                extra_data={"tokens": tokens_used}
            )
            
        except Exception as e:
            logger.error_ctx(
                f"Error processing message: {str(e)}",
                user_id=user.id,
                chat_id=chat.id,
                action="message_error"
            )
            await message.reply_text(
                "❌ Bir hata oluştu. Lütfen daha sonra tekrar deneyin."
            )
