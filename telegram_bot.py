#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
بوت وزنة مصاريف - Telegram Bot
"""

from telegram import Update, WebAppInfo, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
import logging
import json
import os
from datetime import datetime

# إعداد التسجيل
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# قراءة المتغيرات من البيئة (Environment Variables)
BOT_TOKEN = os.environ.get('BOT_TOKEN')
WEB_APP_URL = os.environ.get('WEB_APP_URL')

# التحقق من وجود المتغيرات
if not BOT_TOKEN:
    logger.error("❌ خطأ: BOT_TOKEN غير موجود في Environment Variables")
    exit(1)

if not WEB_APP_URL:
    logger.error("⚠️ تحذير: WEB_APP_URL غير موجود في Environment Variables")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """أمر /start - الرسالة الترحيبية"""
    user = update.effective_user
    
    keyboard = [
        [InlineKeyboardButton("📊 إدارة الميزانية", web_app=WebAppInfo(url=WEB_APP_URL))],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    welcome_message = f"""
السلام عليكم {user.first_name}! 👋

🎯 *مرحباً بك في بوت وزنة مصاريف*

نظام ذكي لإدارة ميزانية أسرتك

✅ تسجيل الدخل والمصاريف
✅ تحليل تلقائي للموقف المالي
✅ تصدير التقارير PDF
✅ واجهة عربية جميلة

اضغط على الزر أدناه للبدء:
    """
    
    await update.message.reply_text(
        welcome_message,
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )

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
    
    await update.message.reply_text(
        message_text,
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )

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
        
        # تحديد حالة الميزانية
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
        """
        
        await update.message.reply_text(summary, parse_mode='Markdown')
        logger.info(f"تم استقبال بيانات من المستخدم {user.id}")
        
    except Exception as e:
        logger.error(f"خطأ في معالجة البيانات: {e}")
        await update.message.reply_text(
            "❌ عذراً، حدث خطأ في معالجة البيانات."
        )

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """معالج الأخطاء"""
    logger.error(f"حدث خطأ: {context.error}")
    
    if update and update.effective_message:
        await update.effective_message.reply_text(
            "❌ عذراً، حدث خطأ. يرجى المحاولة لاحقاً."
        )

def main():
    """تشغيل البوت"""
    logger.info("=" * 50)
    logger.info("🤖 بوت وزنة مصاريف")
    logger.info("=" * 50)
    logger.info(f"✅ البوت يعمل الآن...")
    logger.info(f"🔗 Web App URL: {WEB_APP_URL}")
    logger.info(f"📅 التاريخ: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info("=" * 50)
    
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
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        logger.error(f"❌ خطأ في تشغيل البوت: {e}")