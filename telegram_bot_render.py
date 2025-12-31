#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
بوت وزنة مصاريف - التحقق من العضوية فقط
"""

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, ContextTypes
import logging
import json
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
# أضف معرفات جميع قنواتك ومجموعاتك (مفصولة بفاصلة)
CHANNEL_IDS = os.environ.get('CHANNEL_IDS', '@channel1,@channel2,@group1').split(',')
PORT = int(os.environ.get('PORT', 10000))

if not BOT_TOKEN:
    logger.error("❌ BOT_TOKEN غير موجود")
    exit(1)

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
            <small>{datetime.now()}</small>
            </body></html>
            """.encode("utf-8")
        )

    def log_message(self, format, *args):
        pass

def run_http_server():
    server = HTTPServer(('0.0.0.0', PORT), HealthCheckHandler)
    server.serve_forever()

# ================== دالة التحقق من العضوية ==================

async def check_membership(user_id, bot):
    """
    التحقق من عضوية المستخدم في جميع القنوات/المجموعات
    """
    for channel_id in CHANNEL_IDS:
        try:
            member = await bot.get_chat_member(channel_id.strip(), user_id)
            if member.status in ["member", "administrator", "creator"]:
                return True, channel_id.strip()
        except Exception as e:
            logger.error(f"❌ خطأ في التحقق من {channel_id}: {e}")
    
    return False, None

# ================== BOT LOGIC ==================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    /startapp مع التحقق من العضوية في القنوات/المجموعات
    """
    user = update.effective_user
    args = context.args

    # ✅ التحقق من العضوية أولاً
    is_member, channel = await check_membership(user.id, context.bot)
    
    if not is_member:
        # ❌ ليس عضواً - طلب الانضمام
        buttons = []
        for ch_id in CHANNEL_IDS:
            buttons.append([InlineKeyboardButton(
                f"📢 انضم إلى {ch_id}", 
                url=f"https://t.me/{ch_id[1:]}"
            )])
        
        # أضف زر إعادة المحاولة
        buttons.append([InlineKeyboardButton(
            "🔄 أعد الضغط هنا بعد الانضمام", 
            url=f"https://t.me/WaznahBot?startapp=main"
        )])
        
        await update.effective_message.reply_text(
            "⚠️ *يجب أن تكون عضواً في قنواتنا/مجموعاتنا لاستخدام هذا البوت*\n\n"
            "انضم إلى القناة/المجموعة ثم أعد الضغط على الرابط:",
            reply_markup=InlineKeyboardMarkup(buttons),
            parse_mode="Markdown"
        )
        logger.warning(f"🚫 ليس عضواً: {user.id} | @{user.username}")
        return

    # ✅ المستخدم عضو - السماح بالوصول
    await update.effective_message.reply_text(
        f"""
✅ *تم التحقق من العضوية*

👤 أهلاً {user.first_name}
📊 يمكنك الآن استخدام نظام الميزانية

[افتح النظام]({os.environ.get('WEB_APP_URL', 'https://waznah.com')})
        """,
        parse_mode="Markdown"
    )
    logger.info(f"✅ دخول ناجح: {user.id} | @{user.username}")

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """/help بالعربية"""
    await update.effective_message.reply_text("""
📋 **قائمة الأوامر:**

• `/start` - بدء استخدام البوت
• `/help` - عرض هذه القائمة

⚠️ **ملاحظة:** البوت يعمل فقط لأعضاء قنواتنا/مجموعاتنا
    """, parse_mode="Markdown")

async def handle_web_app_data(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        data = json.loads(update.message.web_app_data.data)
        user = update.effective_user
        logger.info(f"📊 WebApp from {user.id}: {data}")
        await update.effective_message.reply_text("✅ تم استلام البيانات بنجاح")
    except Exception as e:
        logger.error(f"❌ WebApp error: {e}")
        await update.effective_message.reply_text("❌ خطأ في معالجة البيانات")

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.error(f"❌ خطأ: {context.error}")

# ================== MAIN ==================

def main():
    logger.info(f"🚀 بدء تشغيل بوت وزنة مصاريف")
    logger.info(f"📋 القنوات/المجموعات: {CHANNEL_IDS}")

    Thread(target=run_http_server, daemon=True).start()

    application = Application.builder().token(BOT_TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(MessageHandler(filters.StatusUpdate.WEB_APP_DATA, handle_web_app_data))
    application.add_error_handler(error_handler)

    application.run_polling(
        allowed_updates=Update.ALL_TYPES,
        drop_pending_updates=True
    )

if __name__ == "__main__":
    main()
