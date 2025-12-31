#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
بوت وزنة مصاريف - مع التحقق من عضوية القناة
"""

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
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
CHANNEL_ID = os.environ.get('CHANNEL_ID', '@username_qanatek')  # ➕ أضف هذا المتغير
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

# ================== BOT LOGIC ==================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    /start مع التحقق المزدوج: startapp + عضوية القناة
    """
    user = update.effective_user
    args = context.args

    # ❌ رفض الدخول العادي
    if not args:
        await update.effective_message.reply_text(
            "⛔ *طريقة دخول غير مدعومة*\n\n"
            "يجب استخدام الرابط الرسمي فقط:\n"
            "👉 https://t.me/WaznahBot?startapp=main",
            parse_mode="Markdown"
        )
        logger.warning(f"🚫 دخول مرفوض من المستخدم {user.id}")
        return

    # ✅ التحقق من عضوية القناة
    try:
        member = await context.bot.get_chat_member(CHANNEL_ID, user.id)
        
        if member.status not in ["member", "administrator", "creator"]:
            keyboard = [[InlineKeyboardButton(
                "📢 انضم للقناة أولاً", 
                url=f"https://t.me/{CHANNEL_ID[1:]}"
            )]]
            await update.effective_message.reply_text(
                "⚠️ *يجب أن تكون عضواً في القناة لاستخدام البوت*\n\n"
                "انضم للقناة ثم أعد الضغط على الرابط:",
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode="Markdown"
            )
            logger.warning(f"🚫 ليس عضواً في القناة: {user.id}")
            return

    except Exception as e:
        await update.effective_message.reply_text(
            "❌ خطأ في التحقق من العضوية. تأكد من إضافة البوت مشرفاً في القناة."
        )
        logger.error(f"❌ خطأ التحقق: {e}")
        return

    # ✅ كل شيء صحيح
    await update.effective_message.reply_text(
        f"""
✅ *تم التحقق من طريقة الدخول*

👤 المستخدم: {user.first_name}
📣 المصدر: `startapp`

🎉 يمكنك الآن استخدام النظام.
        """,
        parse_mode="Markdown"
    )
    logger.info(f"✅ دخول ناجح من المستخدم {user.id}")

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    /help باللغة العربية
    """
    help_text = """
📋 **قائمة الأوامر المتاحة:**

🎯 **الأوامر الرئيسية:**
• `/start` - بدء استخدام البوت
• `/help` - عرض هذه القائمة

⚙️ **إعدادات الاشتراك الإجباري:**
• `/setfsub chatid yes` - إعداد القناة المطلوبة
• `/refreshlink yes` - تحديث رابط الانضمام

🔧 **الإعدادات:**
• `/settings` - إعدادات المجموعة
• `/fdel on/off` - تفعيل حذف الرسائل
• `/fsub on/off` - تفعيل الاشتراك الإجباري

📝 **تخصيص النصوص:**
• `/ftext` - نص رسالة الاشتراك
• `/fbtntext` - نص زر الانضمام
• `/fmsgdel 5m/off` - حذف تلقائي بعد وقت

✨ **تأكد من:**
1️⃣ إضافة البوت مشرفاً في القناة
2️⃣ منحه صلاحيات: دعوة، حذف، حظر، إرسال
3️⃣ استخدام الروابط الرسمية فقط
    """
    await update.effective_message.reply_text(help_text, parse_mode="Markdown")

async def handle_web_app_data(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        data = json.loads(update.message.web_app_data.data)
        user = update.effective_user
        logger.info(f"📊 WebApp data from {user.id}: {data}")
        await update.effective_message.reply_text("✅ تم استلام البيانات بنجاح")
    except Exception as e:
        logger.error(f"❌ WebApp error: {e}")
        await update.effective_message.reply_text("❌ حدث خطأ في معالجة البيانات")

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.error(f"❌ خطأ: {context.error}")

# ================== MAIN ==================

def main():
    logger.info("🚀 بدء تشغيل بوت وزنة مصاريف")

    Thread(target=run_http_server, daemon=True).start()

    application = Application.builder().token(BOT_TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))  # ➕ أمر جديد
    application.add_handler(MessageHandler(filters.StatusUpdate.WEB_APP_DATA, handle_web_app_data))
    application.add_error_handler(error_handler)

    application.run_polling(
        allowed_updates=Update.ALL_TYPES,
        drop_pending_updates=True
    )

if __name__ == "__main__":
    main()
