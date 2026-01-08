#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
بوت وزنة مصاريف - نسخة محسّنة مع دعم إرسال الصور
"""
from telegram import Update, WebAppInfo, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters
import logging
import os
from threading import Thread
from http.server import HTTPServer, BaseHTTPRequestHandler
import base64
import io
from PIL import Image

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
WEBAPP_URL = os.environ.get(https://darkezy.github.io/waznah-webapp/)

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
        # إنشاء لوحة مفاتيح مع زر Web App
        keyboard = [
            [InlineKeyboardButton(
                "💰 فتح تطبيق وزنة مصاريف",
                web_app=WebAppInfo(url=WEBAPP_URL)
            )],
            [InlineKeyboardButton(
                "📖 دليل الاستخدام",
                callback_data="help"
            )]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.effective_message.reply_text(
            "✅ *أهلاً بك في تطبيق وزنة مصاريف!*\n\n"
            "📊 *المميزات:*\n"
            "• تحليل الدخل والمصاريف\n"
            "• تقارير شهرية وسنوية\n"
            "• تحليل موقف الأسرة المالي\n"
            "• حفظ التقارير كصور\n\n"
            "📱 *للبدء:*\n"
            "اضغط على الزر أدناه لفتح التطبيق\n\n"
            "💡 *نصيحة:*\n"
            "لحفظ التقارير، اضغط زر 'حفظ صورة' داخل التطبيق",
            parse_mode="Markdown",
            reply_markup=reply_markup
        )
        return
    
    # ❌ الجميع
    await update.effective_message.reply_text(
        "⛔ *هذا النظام مغلق*\n\n"
        "البوت غير متاح للجمهور حالياً.",
        parse_mode="Markdown"
    )
    logger.info(f"🚫 محاولة دخول: {user.id}")


async def handle_webapp_data(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    معالجة البيانات المُرسلة من Web App
    يمكن استخدام هذه الدالة لاستقبال الصور من التطبيق وإرسالها للمستخدم
    """
    user = update.effective_user
    
    # التحقق من الصلاحيات
    if user.id != ADMIN_ID:
        return
    
    try:
        # استخراج البيانات من Web App
        web_app_data = update.effective_message.web_app_data.data
        
        # إذا كانت البيانات عبارة عن صورة Base64
        if web_app_data.startswith('data:image'):
            logger.info(f"📸 استقبال صورة من المستخدم {user.id}")
            
            # فصل الـ Base64 من الـ header
            image_data = web_app_data.split(',')[1]
            image_bytes = base64.b64decode(image_data)
            
            # تحويل إلى ملف
            image_file = io.BytesIO(image_bytes)
            image_file.name = 'وزنة_مصاريف.png'
            
            # إرسال الصورة للمستخدم
            await update.effective_message.reply_photo(
                photo=image_file,
                caption="📊 *تقرير من تطبيق وزنة مصاريف*\n\n"
                       "✅ تم حفظ التقرير بنجاح!\n"
                       "يمكنك الآن حفظه في هاتفك.",
                parse_mode="Markdown"
            )
            
            logger.info(f"✅ تم إرسال الصورة للمستخدم {user.id}")
            
        else:
            # بيانات أخرى (مثل JSON)
            await update.effective_message.reply_text(
                f"✅ تم استقبال البيانات:\n```\n{web_app_data}\n```",
                parse_mode="Markdown"
            )
            
    except Exception as e:
        logger.error(f"❌ خطأ في معالجة بيانات Web App: {e}")
        await update.effective_message.reply_text(
            "❌ حدث خطأ أثناء معالجة البيانات."
        )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """عرض دليل الاستخدام"""
    user = update.effective_user
    
    if user.id != ADMIN_ID:
        return
    
    help_text = """
📖 *دليل استخدام تطبيق وزنة مصاريف*

*1️⃣ فتح التطبيق:*
اضغط على زر "فتح تطبيق وزنة مصاريف"

*2️⃣ إدخال البيانات:*
• أدخل مصادر دخلك في تبويب "مصادر الدخل"
• أدخل مصاريفك في تبويب "ميزانية الأسرة"

*3️⃣ عرض التحليل:*
افتح تبويب "تحليل موقف الأسرة" لرؤية التقييم

*4️⃣ حفظ التقرير:*
اضغط زر "حفظ صورة" في أي تبويب

*5️⃣ طرق الحفظ:*
• سيُفتح المتصفح مع صفحة التحميل
• اضغط "تحميل الصورة" أو "مشاركة"
• أو اضغط مطولاً على الصورة واختر "حفظ"

*💡 نصائح:*
• استخدم الوضع الليلي/النهاري حسب تفضيلك
• يمكنك إضافة عدة مصادر دخل ومصاريف
• التقارير تُحفظ بتاريخ اليوم تلقائياً

*🆘 مشاكل الحفظ؟*
إذا لم يعمل زر الحفظ:
1. افتح التطبيق في المتصفح العادي بدلاً من Telegram
2. تأكد من إعطاء أذونات التنزيل للمتصفح
3. جرب متصفح آخر (Chrome/Safari)

*📞 الدعم:*
للمساعدة، تواصل مع المطور
"""
    
    await update.effective_message.reply_text(
        help_text,
        parse_mode="Markdown"
    )


async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.error(f"❌ خطأ: {context.error}")

# ================== MAIN ==================

def main():
    logger.info(f"🚀 بدء تشغيل البوت")
    logger.info(f"👑 المشرف: {ADMIN_ID}")
    logger.info(f"🌐 رابط Web App: {WEBAPP_URL}")
    
    # بدء HTTP Server
    Thread(target=run_http_server, daemon=True).start()
    
    # إنشاء التطبيق
    application = Application.builder().token(BOT_TOKEN).build()
    
    # إضافة المعالجات
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    
    # معالج بيانات Web App (اختياري - للاستخدام المستقبلي)
    application.add_handler(MessageHandler(
        filters.StatusUpdate.WEB_APP_DATA, 
        handle_webapp_data
    ))
    
    # معالج الأخطاء
    application.add_error_handler(error_handler)
    
    # بدء البوت
    application.run_polling(
        allowed_updates=Update.ALL_TYPES,
        drop_pending_updates=True
    )

if __name__ == "__main__":
    main()


"""
=============================================================================
ملاحظات التحسين:
=============================================================================

✅ التحسينات المُطبقة:

1. إضافة زر Web App في /start
   - يفتح التطبيق مباشرة من Telegram
   
2. إضافة أمر /help
   - دليل استخدام شامل للمستخدم
   
3. إضافة معالج لبيانات Web App
   - يمكن استخدامه مستقبلاً لإرسال الصور
   - حالياً غير مفعّل (اختياري)

4. تحسين رسائل البوت
   - رسائل أوضح وأكثر تفصيلاً
   - نصائح للاستخدام

=============================================================================
متطلبات التشغيل:
=============================================================================

1. إضافة متغير البيئة WEBAPP_URL:
   WEBAPP_URL=https://your-webapp-url.com

2. تثبيت مكتبات إضافية (للاستخدام المستقبلي):
   pip install Pillow

3. رفع ملف HTML على استضافة (مثل GitHub Pages, Vercel, Render)

=============================================================================
الاستخدام المستقبلي (اختياري):
=============================================================================

يمكن تطوير ميزة إرسال الصورة من Web App للبوت:

1. في JavaScript (وزنة.html):
   
   // بعد التقاط الصورة
   const dataUrl = canvas.toDataURL('image/png');
   
   // إرسال للبوت
   if (window.Telegram?.WebApp) {
       window.Telegram.WebApp.sendData(dataUrl);
   }

2. البوت سيستقبل الصورة ويُرسلها للمستخدم في Telegram
   (معالج handle_webapp_data جاهز لذلك)

3. المستخدم يحفظ الصورة مباشرة من Telegram

=============================================================================
"""
