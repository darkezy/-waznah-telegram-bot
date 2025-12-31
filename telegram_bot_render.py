#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
بوت وزنة مصاريف - Telegram Bot for Render
نظام إدارة ميزانية الأسرة
"""

from telegram import Update, WebAppInfo, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
import logging
import json
import os
from datetime import datetime
from threading import Thread
from http.server import HTTPServer, BaseHTTPRequestHandler

# إعداد التسجيل
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# قراءة المتغيرات من البيئة
BOT_TOKEN = os.environ.get('BOT_TOKEN')
WEB_APP_URL = os.environ.get('WEB_APP_URL')
PORT = int(os.environ.get('PORT', 10000))

# التحقق من وجود المتغيرات
if not BOT_TOKEN:
    logger.error("❌ خطأ: BOT_TOKEN غير موجود")
    exit(1)

if not WEB_APP_URL:
    logger.warning("⚠️ تحذير: WEB_APP_URL غير موجود")

# ===== HTTP Server لإرضاء Render =====
class HealthCheckHandler(BaseHTTPRequestHandler):
    """معالج بسيط للـ health checks"""
    
    def do_GET(self):
        """الرد على طلبات GET"""
        self.send_response(200)
        self.send_header('Content-type', 'text/html; charset=utf-8')
        self.end_headers()
        
        response = """
        <!DOCTYPE html>
        <html dir="rtl" lang="ar">
        <head>
            <meta charset="UTF-8">
            <title>وزنة مصاريف - البوت يعمل</title>
            <style>
                body { font-family: Arial; text-align: center; padding: 50px; background: #f0f0f0; }
                .status { background: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
                .running { color: #28a745; font-size: 24px; }
            </style>
        </head>
        <body>
            <div class="status">
                <h1>🤖 وزنة مصاريف</h1>
                <p class="running">✅ البوت يعمل بشكل طبيعي</p>
                <p>ابحث عن البوت في تليجرام واستخدم الأمر /start</p>
                <hr>
                <p><small>Render Health Check - """ + datetime.now().strftime('%Y-%m-%d %H:%M:%S') + """</small></p>
            </div>
        </body>
        </html>
        """
        self.wfile.write(response.encode('utf-8'))
    
    def log_message(self, format, *args):
        """تعطيل HTTP logs لتقليل الضجيج"""
        pass

def run_http_server():
    """تشغيل HTTP server في thread منفصل"""
    try:
        server = HTTPServer(('0.0.0.0', PORT), HealthCheckHandler)
        logger.info(f"🌐 HTTP Server يعمل على Port {PORT}")
        server.serve_forever()
    except Exception as e:
        logger.error(f"❌ خطأ في HTTP Server: {e}")

# ===== معالجات البوت =====

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """أمر /start - الرسالة الترحيبية"""
    user = update.effective_user
    
    keyboard = [
        [InlineKeyboardButton("📊 إدارة الميزانية", web_app=WebAppInfo(url=WEB_APP_URL))],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    welcome_message = f"""
السلام عليكم {user.first_name}! 👋

🎯 *مرحباً بك في وزنة مصاريف*

نظام ذكي لإدارة ميزانية أسرتك

✅ تسجيل الدخل والمصاريف
✅ تحليل تلقائي للموقف المالي
✅ تصدير التقارير PDF

اضغط على الزر أدناه للبدء:
    """
    
    try:
        await update.message.reply_text(
            welcome_message,
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
        logger.info(f"✅ /start من المستخدم {user.id} (@{user.username})")
    except Exception as e:
        logger.error(f"❌ خطأ في start: {e}")
        await update.message.reply_text("حدث خطأ، يرجى المحاولة مرة أخرى.")

async def budget(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """أمر /budget - فتح نظام الميزانية"""
    keyboard = [[InlineKeyboardButton("📊 فتح النظام", web_app=WebAppInfo(url=WEB_APP_URL))]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    message_text = """
💰 *نظام إدارة ميزانية الأسرة*

📝 الخدمات المتوفرة:

1️⃣ *مصادر الدخل*
   • تسجيل جميع مصادر الدخل
   • حساب المجاميع تلقائياً

2️⃣ *ميزانية الأسرة*
   • تسجيل جميع المصاريف
   • تصنيف دقيق للمصروفات

3️⃣ *تحليل موقف الأسرة*
   • تقييم الوضع المالي
   • نصائح للتطوير

اضغط على الزر لفتح النظام:
    """
    
    try:
        await update.message.reply_text(
            message_text,
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
        logger.info(f"✅ /budget من المستخدم {update.effective_user.id}")
    except Exception as e:
        logger.error(f"❌ خطأ في budget: {e}")
        await update.message.reply_text("حدث خطأ، يرجى المحاولة مرة أخرى.")

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """أمر /help - المساعدة"""
    help_text = """
📖 *دليل استخدام البوت*

🔹 *الأوامر المتاحة:*

/start - بدء البوت
/budget - فتح نظام الميزانية
/help - عرض المساعدة

📱 *كيفية الاستخدام:*

1. اضغط على /budget
2. اضغط على زر "فتح النظام"
3. أدخل بيانات الدخل والمصاريف
4. شاهد التحليل التلقائي
5. صدّر التقرير إذا أردت

💡 البيانات تُحفظ في جهازك فقط
🔒 خصوصيتك مهمة لنا
    """
    
    await update.message.reply_text(help_text, parse_mode='Markdown')

async def handle_web_app_data(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """معالجة البيانات المرسلة من Web App"""
    try:
        data = json.loads(update.message.web_app_data.data)
        user = update.effective_user
        
        monthly_income = data.get('monthly_income', 'غير محدد')
        monthly_expenses = data.get('monthly_expenses', 'غير محدد')
        net_surplus = data.get('net_surplus', 'غير محدد')
        
        try:
            surplus_value = float(str(net_surplus).replace(',', ''))
            if surplus_value > 0:
                status_emoji = "✅"
                status_text = "وضع جيد - لديك فائض"
            elif surplus_value == 0:
                status_emoji = "⚖️"
                status_text = "وضع متوازن"
            else:
                status_emoji = "⚠️"
                status_text = "انتبه - لديك عجز"
        except:
            status_emoji = "ℹ️"
            status_text = "غير محدد"
        
        summary = f"""
📊 *ملخص ميزانية {user.first_name}*

💰 الدخل الشهري: {monthly_income}
💳 المصاريف الشهرية: {monthly_expenses}
{status_emoji} صافي الفائض: {net_surplus}

📌 الحالة: {status_text}

⏰ الوقت: {datetime.now().strftime('%Y-%m-%d %H:%M')}

✅ تم حفظ بياناتك!

💡 يمكنك الرجوع للنظام في أي وقت باستخدام /budget
        """
        
        await update.message.reply_text(summary, parse_mode='Markdown')
        logger.info(f"✅ تم استقبال بيانات من المستخدم {user.id}")
        
    except Exception as e:
        logger.error(f"❌ خطأ في معالجة البيانات: {e}")
        await update.message.reply_text(
            "❌ عذراً، حدث خطأ في معالجة البيانات."
        )

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """معالج الأخطاء العام"""
    logger.error(f"❌ خطأ: {context.error}")
    
    if update and update.effective_message:
        await update.effective_message.reply_text(
            "❌ عذراً، حدث خطأ. يرجى المحاولة مرة أخرى."
        )

def main():
    """تشغيل البوت"""
    logger.info("=" * 60)
    logger.info("🤖 بوت وزنة مصاريف")
    logger.info("=" * 60)
    logger.info(f"📅 التاريخ: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info(f"🔗 Web App URL: {WEB_APP_URL}")
    logger.info(f"🌐 Port: {PORT}")
    logger.info("=" * 60)
    
    # تشغيل HTTP Server في thread منفصل (مهم لـ Render!)
    http_thread = Thread(target=run_http_server, daemon=True)
    http_thread.start()
    logger.info("✅ HTTP Server بدأ في الخلفية")
    
    # إنشاء التطبيق
    application = Application.builder().token(BOT_TOKEN).build()
    
    # إضافة معالجات الأوامر
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("budget", budget))
    application.add_handler(CommandHandler("help", help_command))
    
    # معالج البيانات من Web App
    application.add_handler(MessageHandler(filters.StatusUpdate.WEB_APP_DATA, handle_web_app_data))
    
    # معالج الأخطاء
    application.add_error_handler(error_handler)
    
    # بدء البوت
    logger.info("⏳ جاري بدء Telegram Polling...")
    
    try:
        application.run_polling(
            allowed_updates=Update.ALL_TYPES,
            drop_pending_updates=True
        )
    except KeyboardInterrupt:
        logger.info("👋 تم إيقاف البوت بواسطة المستخدم")
    except Exception as e:
        logger.error(f"❌ خطأ في Polling: {e}")
        raise

if __name__ == '__main__':
    main()
