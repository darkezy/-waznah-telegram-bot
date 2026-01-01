#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
بوت وزنة مصاريف - نسخة مغلقة ومضمونة
"""

from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
import logging
import os
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
PORT = int(os.environ.get('PORT', '10000'))

if not BOT_TOKEN:
    logger.error("❌ BOT_TOKEN غير موجود")
    exit(1)
if ADMIN_ID == 0:
    logger.error("❌ ADMIN_ID غير موجود")
    exit(1)

# ================== HTTP Health Check ==================
class HealthCheckHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/html; charset=utf-8')
        self.end_headers()
        # ✅ تم إزالة b"" وتغييره لـ encode('utf-8')
        self.wfile.write("""
        <html><body style="text-align:center;font-family:Arial">
        <h2>🤖 وزنة مصاريف</h2>
        <p style="color:green">البوت يعمل بشكل طبيعي</p>
        </body></html>
        """.encode('utf-8'))

def run_http_server():
    server = HTTPServer(('0.0.0.0', PORT), HealthCheckHandler)
    server.serve_forever()

# ================== BOT LOGIC ==================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """البوت مغلق للجميع ما عدا المشرف"""
    user = update.effective_user
    
    # ✅ المشرف فقط
    if user.id == ADMIN_ID:
        await update.effective_message.reply_text(
            "✅ *أهلاً بك يا مشرف!*\n\n"
            "البوت جاهز للاستخدام.",
            parse_mode="Markdown"
        )
        return
    
    # ❌ الجميع
    await update.effective_message.reply_text(
        "⛔ *هذا النظام مغلق*\n\n"
        "البوت غير متاح للجمهور حالياً.",
        parse_mode="Markdown"
    )
    logger.info(f"🚫 محاولة دخول: {user.id}")

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.error(f"❌ خطأ: {context.error}")

# ================== MAIN ==================

def main():
    logger.info(f"🚀 بدء تشغيل البوت")
    logger.info(f"👑 المشرف: {ADMIN_ID}")

    Thread(target=run_http_server, daemon=True).start()

    application = Application.builder().token(BOT_TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_error_handler(error_handler)

    application.run_polling(
        allowed_updates=Update.ALL_TYPES,
        drop_pending_updates=True
    )

if __name__ == "__main__":
    main()
