#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
بوت وزنة مصاريف - Telegram Bot for Render
الدخول فقط عبر startapp
"""

from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
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
WEB_APP_URL = os.environ.get('WEB_APP_URL')
PORT = int(os.environ.get('PORT', 10000))

if not BOT_TOKEN:
    logger.error("❌ BOT_TOKEN غير موجود")
    exit(1)

if not WEB_APP_URL:
    logger.warning("⚠️ WEB_APP_URL غير موجود")

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

# ================== BOT LOGIC ==================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    /start
    مسموح فقط عبر startapp
    """
    user = update.effective_user
    args = context.args

    # ❌ دخول عادي (ممنوع)
    if not args:
        await update.effective_message.reply_text(
            "⛔ *طريقة دخول غير مدعومة*\n\n"
            "لا يمكن استخدام النظام مباشرة.\n\n"
            "📊 الدخول المسموح فقط عبر الرابط الرسمي:\n"
            "👉 https://t.me/YourBotUsername?startapp=main",
            parse_mode="Markdown"
        )
        logger.warning(f"🚫 دخول مرفوض من المستخدم {user.id}")
        return

    # ✅ دخول عبر startapp
    source = args[0]

    await update.effective_message.reply_text(
        f"""
✅ *تم التحقق من طريقة الدخول*

👤 المستخدم: {user.first_name}
📣 المصدر: `{source}`

📊 إذا لم يفتح نظام الميزانية تلقائيًا،
أغلق المحادثة وأعد فتح الرابط الرسمي.
        """,
        parse_mode="Markdown"
    )

    logger.info(f"✅ دخول startapp صحيح من المستخدم {user.id}")

# ================== WebApp Data ==================

async def handle_web_app_data(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        data = json.loads(update.message.web_app_data.data)
        user = update.effective_user

        logger.info(f"📊 بيانات WebApp من المستخدم {user.id}: {data}")

        await update.effective_message.reply_text(
            "✅ تم استلام البيانات بنجاح",
            parse_mode="Markdown"
        )

    except Exception as e:
        logger.error(f"❌ خطأ WebApp: {e}")
        await update.effective_message.reply_text(
            "❌ حدث خطأ في معالجة البيانات"
        )

# ================== Error Handler ==================

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.error(f"❌ خطأ عام: {context.error}")

# ================== MAIN ==================

def main():
    logger.info("🚀 بدء تشغيل بوت وزنة مصاريف")

    # HTTP Server
    Thread(target=run_http_server, daemon=True).start()

    application = Application.builder().token(BOT_TOKEN).build()

    # Handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(
        MessageHandler(filters.StatusUpdate.WEB_APP_DATA, handle_web_app_data)
    )
    application.add_error_handler(error_handler)

    application.run_polling(
        allowed_updates=Update.ALL_TYPES,
        drop_pending_updates=True
    )

if __name__ == "__main__":
    main()
