from telegram import Update
from telegram.ext import ContextTypes
from telegram.constants import ParseMode
from src.services import SearchService
from src.database import Database
from src.utils import RateLimiter, get_logger
from src.utils.helpers import format_search_results

logger = get_logger("command_handler")


class CommandHandler:
    def __init__(
        self,
        search_service: SearchService,
        database: Database,
        rate_limiter: RateLimiter
    ):
        self.search = search_service
        self.db = database
        self.rate_limiter = rate_limiter
    
    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        user = update.effective_user
        
        await self.db.get_or_create_user(
            user_id=user.id,
            username=user.username or "",
            first_name=user.first_name,
            last_name=user.last_name or ""
        )
        
        welcome_message = f"""
👋 <b>Merhaba {user.first_name}!</b>

Ben yapay zeka destekli bir asistanım. Sana yardımcı olmak için buradayım.

<b>🔹 Nasıl Kullanılır:</b>
• Beni @mention ederek soru sorabilirsin
• Mesajlarıma reply atarak konuşmaya devam edebilirsin
• Web araması için <code>/search sorgu</code> kullan

<b>🔹 Komutlar:</b>
• /help - Yardım menüsü
• /search - Web araması
• /clear - Sohbet geçmişini temizle
• /stats - Kullanım istatistiklerin

<b>🔹 Özellikler:</b>
• 🧠 Sohbet geçmişi hafızası
• 🔍 Web araması desteği
• ⚡ Hızlı yanıtlar
"""
        
        await update.message.reply_text(welcome_message, parse_mode=ParseMode.HTML)
        
        logger.info_ctx(
            "User started bot",
            user_id=user.id,
            action="command_start"
        )
    
    async def help(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        help_message = """
<b>📖 Yardım Menüsü</b>

<b>🔹 Temel Kullanım:</b>
• <code>@botusername sorunuz</code> - Soru sorun
• Mesajıma reply atarak konuşmaya devam edin

<b>🔹 Komutlar:</b>
• /start - Başlangıç mesajı
• /help - Bu yardım menüsü
• /search [sorgu] - Web'de arama yap
• /clear - Sohbet geçmişini temizle
• /stats - Kullanım istatistiklerin

<b>🔹 İpuçları:</b>
• Güncel bilgiler için sorularınızda "güncel", "bugün" gibi kelimeler kullanın
• Bot otomatik olarak web araması yapacaktır
• Her sohbet geçmişi kullanıcı ve chat bazında saklanır
"""
        
        await update.message.reply_text(help_message, parse_mode=ParseMode.HTML)
    
    async def search(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        user = update.effective_user
        chat = update.effective_chat
        
        if not context.args:
            await update.message.reply_text(
                "❌ Arama sorgusu belirtmelisiniz.\n\nKullanım: <code>/search sorgunuz</code>",
                parse_mode=ParseMode.HTML
            )
            return
        
        is_group = chat.type in ["group", "supergroup"]
        allowed, cooldown = await self.rate_limiter.check_rate_limit(
            user_id=user.id,
            chat_id=chat.id,
            is_group=is_group
        )
        
        if not allowed:
            await update.message.reply_text(
                f"⏳ Rate limit aşıldı. Lütfen {cooldown} saniye bekleyin."
            )
            return
        
        query = " ".join(context.args)
        
        await update.message.reply_text(f"🔍 <b>Aranıyor:</b> {query}", parse_mode=ParseMode.HTML)
        
        results = await self.search.search_web(query, max_results=5)
        
        if not results:
            await update.message.reply_text("❌ Arama sonucu bulunamadı.")
            return
        
        await self.db.update_stats(user.id, searches=1)
        
        formatted = format_search_results(results)
        response = f"<b>🔍 Arama Sonuçları: {query}</b>\n\n{formatted}"
        
        if len(response) > 4000:
            response = response[:3997] + "..."
        
        await update.message.reply_text(response, parse_mode=ParseMode.HTML, disable_web_page_preview=True)
        
        logger.info_ctx(
            f"Search command executed",
            user_id=user.id,
            chat_id=chat.id,
            action="command_search",
            extra_data={"query": query}
        )
    
    async def clear(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        user = update.effective_user
        chat = update.effective_chat
        
        deleted = await self.db.clear_conversation(user.id, chat.id)
        
        await update.message.reply_text(
            f"🗑️ Sohbet geçmişi temizlendi. ({deleted} mesaj silindi)"
        )
        
        logger.info_ctx(
            "Conversation cleared",
            user_id=user.id,
            chat_id=chat.id,
            action="command_clear",
            extra_data={"deleted_count": deleted}
        )
    
    async def stats(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        user = update.effective_user
        
        user_stats = await self.db.get_user_stats(user.id)
        usage = await self.rate_limiter.get_user_usage(user.id)
        
        if not user_stats:
            await update.message.reply_text("❌ İstatistik bulunamadı.")
            return
        
        stats_message = f"""
<b>📊 Kullanım İstatistiklerin</b>

<b>🔹 Genel:</b>
• Toplam Mesaj: <code>{user_stats.total_messages}</code>
• Toplam Token: <code>{user_stats.total_tokens:,}</code>
• Toplam Arama: <code>{user_stats.total_searches}</code>
• Son Aktiflik: <code>{user_stats.last_active.strftime('%Y-%m-%d %H:%M')}</code>

<b>🔹 Rate Limit:</b>
• Kullanılan: <code>{usage['used']}/{usage['limit']}</code>
• Kalan: <code>{usage['remaining']}</code>
• Pencere: <code>{usage['window_seconds']} saniye</code>
"""
        
        await update.message.reply_text(stats_message, parse_mode=ParseMode.HTML)
        
        logger.info_ctx(
            "Stats command executed",
            user_id=user.id,
            action="command_stats"
        )
