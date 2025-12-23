from telegram import Update
from telegram.ext import ContextTypes
from telegram.constants import ParseMode
from src.database import Database
from src.utils import RateLimiter, get_logger

logger = get_logger("admin_handler")


class AdminHandler:
    def __init__(self, database: Database, rate_limiter: RateLimiter, admin_ids: list[int]):
        self.db = database
        self.rate_limiter = rate_limiter
        self.admin_ids = admin_ids
    
    def is_admin(self, user_id: int) -> bool:
        return user_id in self.admin_ids
    
    async def ban(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        user = update.effective_user
        
        if not self.is_admin(user.id):
            await update.message.reply_text("❌ Bu komutu kullanma yetkiniz yok.")
            return
        
        if not context.args:
            await update.message.reply_text(
                "❌ Kullanım: <code>/ban @username</code> veya <code>/ban user_id</code>",
                parse_mode=ParseMode.HTML
            )
            return
        
        target = context.args[0]
        target_user = None
        
        if target.startswith("@"):
            target_user = await self.db.get_user_by_username(target)
            if not target_user:
                await update.message.reply_text(f"❌ Kullanıcı bulunamadı: {target}")
                return
            target_id = target_user.user_id
        else:
            try:
                target_id = int(target)
            except ValueError:
                await update.message.reply_text("❌ Geçersiz kullanıcı ID.")
                return
        
        if target_id in self.admin_ids:
            await update.message.reply_text("❌ Admin kullanıcılar banlanamaz.")
            return
        
        success = await self.db.ban_user(target_id)
        
        if success:
            await update.message.reply_text(f"✅ Kullanıcı banlandı: <code>{target_id}</code>", parse_mode=ParseMode.HTML)
            logger.warning_ctx(
                f"User banned",
                user_id=user.id,
                action="admin_ban",
                extra_data={"target_id": target_id, "admin_id": user.id}
            )
        else:
            await update.message.reply_text("❌ Kullanıcı bulunamadı veya zaten banlı.")
    
    async def unban(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        user = update.effective_user
        
        if not self.is_admin(user.id):
            await update.message.reply_text("❌ Bu komutu kullanma yetkiniz yok.")
            return
        
        if not context.args:
            await update.message.reply_text(
                "❌ Kullanım: <code>/unban @username</code> veya <code>/unban user_id</code>",
                parse_mode=ParseMode.HTML
            )
            return
        
        target = context.args[0]
        target_user = None
        
        if target.startswith("@"):
            target_user = await self.db.get_user_by_username(target)
            if not target_user:
                await update.message.reply_text(f"❌ Kullanıcı bulunamadı: {target}")
                return
            target_id = target_user.user_id
        else:
            try:
                target_id = int(target)
            except ValueError:
                await update.message.reply_text("❌ Geçersiz kullanıcı ID.")
                return
        
        success = await self.db.unban_user(target_id)
        await self.rate_limiter.reset_user(target_id)
        
        if success:
            await update.message.reply_text(f"✅ Kullanıcı banı kaldırıldı: <code>{target_id}</code>", parse_mode=ParseMode.HTML)
            logger.info_ctx(
                f"User unbanned",
                user_id=user.id,
                action="admin_unban",
                extra_data={"target_id": target_id, "admin_id": user.id}
            )
        else:
            await update.message.reply_text("❌ Kullanıcı bulunamadı veya banlı değil.")
    
    async def admin_stats(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        user = update.effective_user
        
        if not self.is_admin(user.id):
            await update.message.reply_text("❌ Bu komutu kullanma yetkiniz yok.")
            return
        
        global_stats = await self.db.get_global_stats()
        
        stats_message = f"""
<b>📊 Global İstatistikler (Admin)</b>

<b>🔹 Kullanıcılar:</b>
• Toplam Kullanıcı: <code>{global_stats['total_users']}</code>
• Banlı Kullanıcı: <code>{global_stats['banned_users']}</code>

<b>🔹 Kullanım:</b>
• Toplam Mesaj: <code>{global_stats['total_messages']:,}</code>
• Toplam Token: <code>{global_stats['total_tokens']:,}</code>
• Toplam Arama: <code>{global_stats['total_searches']:,}</code>

<b>🔹 Adminler:</b>
• Admin Sayısı: <code>{len(self.admin_ids)}</code>
"""
        
        await update.message.reply_text(stats_message, parse_mode=ParseMode.HTML)
        
        logger.info_ctx(
            "Admin stats viewed",
            user_id=user.id,
            action="admin_stats"
        )
    
    async def health(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        user = update.effective_user
        
        if not self.is_admin(user.id):
            await update.message.reply_text("❌ Bu komutu kullanma yetkiniz yok.")
            return
        
        health_status = "✅ Healthy"
        
        try:
            global_stats = await self.db.get_global_stats()
            db_status = "✅ Connected"
        except Exception:
            db_status = "❌ Error"
            health_status = "⚠️ Degraded"
        
        health_message = f"""
<b>🏥 Health Check</b>

<b>Status:</b> {health_status}

<b>🔹 Servisler:</b>
• Database: {db_status}
• Bot: ✅ Running
• Rate Limiter: ✅ Active
"""
        
        await update.message.reply_text(health_message, parse_mode=ParseMode.HTML)
