#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
بوت وزنة مصاريف - نظام طلب انضمام مبسط
"""

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, ContextTypes, CallbackQueryHandler
import logging
import os
from datetime import datetime
from threading import Thread
from http.server import HTTPServer, BaseHTTPRequestHandler

# ================== Logging ==================
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# ================== ENV ==================
BOT_TOKEN = os.environ.get('BOT_TOKEN')
ADMIN_ID = int(os.environ.get('ADMIN_ID', '0'))
WEB_APP_URL = os.environ.get('WEB_APP_URL', 'https://waznah.com')
PORT = int(os.environ.get('PORT', '10000'))

if not BOT_TOKEN:
    logger.error("❌ BOT_TOKEN غير موجود")
    exit(1)
if ADMIN_ID == 0:
    logger.error("❌ ADMIN_ID غير موجود")
    exit(1)

# ================== تخزين البيانات ==================
join_requests = {}  # {user_id: user_data}
approved_users = set()  # {user_id, ...}

# ================== HTTP Health Check ==================
class HealthCheckHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/html; charset=utf-8')
        self.end_headers()
        self.wfile.write(
            f"""
            <html><body style="text-align:center;font-family:Arial">
            <h2>🤖 وزنة مصاريف</h2>
            <p style="color:green">البوت يعمل بشكل طبيعي</p>
            </body></html>
            """.encode("utf-8")
        )

def run_http_server():
    server = HTTPServer(('0.0.0.0', PORT), HealthCheckHandler)
    server.serve_forever()

# ================== BOT LOGIC ==================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """/start - دخول المستخدمين"""
    user = update.effective_user
    
    # ✅ إذا كان موافق عليه
    if user.id in approved_users:
        await update.effective_message.reply_text(
            f"✅ *أهلاً بك مجدداً!*\n\n"
            f"👤 {user.first_name}\n"
            f"📊 [افتح نظام الميزانية]({WEB_APP_URL})",
            parse_mode="Markdown"
        )
        return
    
    # ❌ إذا لم يكن موافق عليه
    keyboard = [
        [InlineKeyboardButton("📝 تقديم طلب انضمام", callback_data=f"request_join:{user.id}")],
        [InlineKeyboardButton("💬 تواصل مع الإدارة", url=f"tg://user?id={ADMIN_ID}")]
    ]
    
    await update.effective_message.reply_text(
        "⛔ *هذا البوت خاص ويتطلب موافقة*\n\n"
        "يمكنك تقديم طلب للحصول على صلاحية الوصول.",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )

async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """معالجة جميع الأزرار"""
    query = update.callback_query
    await query.answer()
    
    try:
        action, target_user_id = query.data.split(":")
        target_user_id = int(target_user_id)
    except:
        await query.message.reply_text("❌ خطأ في المعالجة")
        return

    # 📝 تقديم طلب (من المستخدم)
    if action == "request_join":
        user = update.effective_user
        
        if user.id in join_requests or user.id in approved_users:
            await query.message.reply_text("⚠️ لديك طلب سابق أو موافقة فعالة.")
            return
        
        join_requests[user.id] = {
            "telegram_id": user.id,
            "username": user.username,
            "first_name": user.first_name,
            "timestamp": datetime.now().isoformat()
        }
        
        # 🔔 إشعار المشرف
        admin_buttons = [
            [
                InlineKeyboardButton("✅ موافق", callback_data=f"approve:{user.id}"),
                InlineKeyboardButton("❌ رفض", callback_data=f"reject:{user.id}")
            ]
        ]
        
        admin_msg = (
            f"📝 *طلب انضمام جديد*\n\n"
            f"👤 الاسم: {user.first_name}\n"
            f"🆔 المعرف: `@{user.username}`\n"
            f"🔢 الID: `{user.id}`"
        )
        
        try:
            await context.bot.send_message(
                chat_id=ADMIN_ID,
                text=admin_msg,
                reply_markup=InlineKeyboardMarkup(admin_buttons),
                parse_mode="Markdown"
            )
            await query.message.reply_text(
                "✅ تم إرسال طلبك!\n\n"
                "⏳ ستتم المراجعة خلال 24 ساعة.\n"
                "📩 ستصلك رسالة بالقرار."
            )
        except Exception as e:
            logger.error(f"❌ خطأ: {e}")
            await query.message.reply_text("❌ خطأ في إرسال الطلب.")
    
    # ✅ الموافقة (من المشرف)
    elif action == "approve" and query.from_user.id == ADMIN_ID:
        if target_user_id not in join_requests:
            await query.message.reply_text("⚠️ الطلب غير موجود.")
            return
        
        user_data = join_requests[target_user_id]
        approved_users.add(target_user_id)
        del join_requests[target_user_id]
        
        try:
            keyboard = [[InlineKeyboardButton("📊 افتح النظام", url=f"https://t.me/WaznahBot?startapp=main")]]
            await context.bot.send_message(
                chat_id=target_user_id,
                text="🎉 *تمت الموافقة!*\n\nيمكنك الآن استخدام النظام.",
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode="Markdown"
            )
            await query.message.edit_text(
                f"✅ *تمت الموافقة*\n\nالمستخدم: {user_data['first_name']}",
                reply_markup=None
            )
        except Exception as e:
            logger.error(f"❌ خطأ: {e}")
    
    # ❌ الرفض (من المشرف)
    elif action == "reject" and query.from_user.id == ADMIN_ID:
        if target_user_id not in join_requests:
            await query.message.reply_text("⚠️ الطلب غير موجود.")
            return
        
        user_data = join_requests[target_user_id]
        del join_requests[target_user_id]
        
        try:
            await context.bot.send_message(
                chat_id=target_user_id,
                text="❌ *تم رفض طلبك*\n\nيرجى المحاولة لاحقاً.",
                parse_mode="Markdown"
            )
            await query.message.edit_text(
                f"❌ *تم الرفض*\n\nالمستخدم: {user_data['first_name']}",
                reply_markup=None
            )
        except Exception as e:
            logger.error(f"❌ خطأ: {e}")

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """/help"""
    await update.effective_message.reply_text("📋 /start - بدء استخدام البوت")

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.error(f"❌ خطأ: {context.error}")

# ================== MAIN ==================

def main():
    logger.info(f"🚀 بدء تشغيل البوت")
    logger.info(f"👑 المشرف: {ADMIN_ID}")

    Thread(target=run_http_server, daemon=True).start()

    application = Application.builder().token(BOT_TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CallbackQueryHandler(handle_callback))
    
    application.add_error_handler(error_handler)

    application.run_polling(
        allowed_updates=Update.ALL_TYPES,
        drop_pending_updates=True
    )

if __name__ == "__main__":
    main()
