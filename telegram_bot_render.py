#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
بوت وزنة مصاريف - مع نظام التسجيل والموافقة
"""
from telegram import Update, WebAppInfo, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters, ConversationHandler, CallbackQueryHandler
import logging
import os
from threading import Thread
from http.server import HTTPServer, BaseHTTPRequestHandler
import json
from datetime import datetime

# ================== Logging ==================
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# ================== ENV ==================
BOT_TOKEN = os.environ.get('BOT_TOKEN')
ADMIN_ID = os.environ.get('ADMIN_ID')  # معرف الأدمن لاستقبال طلبات التسجيل
PORT = int(os.environ.get('PORT', '10000'))
WEBAPP_URL = os.environ.get('WEBAPP_URL', 'https://your-webapp-url.com')

if not BOT_TOKEN:
    logger.error("❌ BOT_TOKEN غير موجود")
    exit(1)

if not ADMIN_ID:
    logger.error("⚠️ ADMIN_ID غير موجود - لن تعمل الموافقات")

try:
    ADMIN_ID = int(ADMIN_ID) if ADMIN_ID else None
except:
    logger.error("❌ ADMIN_ID يجب أن يكون رقماً")
    ADMIN_ID = None

# ================== قاعدة بيانات بسيطة (JSON) ==================
USERS_FILE = 'users_data.json'

def load_users():
    """تحميل بيانات المستخدمين"""
    try:
        if os.path.exists(USERS_FILE):
            with open(USERS_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
    except Exception as e:
        logger.error(f"خطأ في تحميل البيانات: {e}")
    return {}

def save_users(users_data):
    """حفظ بيانات المستخدمين"""
    try:
        with open(USERS_FILE, 'w', encoding='utf-8') as f:
            json.dump(users_data, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        logger.error(f"خطأ في حفظ البيانات: {e}")
        return False

def is_user_approved(user_id):
    """التحقق من موافقة المستخدم"""
    users = load_users()
    user_str = str(user_id)
    return user_str in users and users[user_str].get('approved', False)

def add_pending_user(user_id, user_data):
    """إضافة مستخدم في انتظار الموافقة"""
    users = load_users()
    users[str(user_id)] = {
        **user_data,
        'approved': False,
        'registration_date': datetime.now().isoformat()
    }
    return save_users(users)

def approve_user(user_id):
    """الموافقة على مستخدم"""
    users = load_users()
    user_str = str(user_id)
    if user_str in users:
        users[user_str]['approved'] = True
        users[user_str]['approval_date'] = datetime.now().isoformat()
        return save_users(users)
    return False

def reject_user(user_id):
    """رفض مستخدم (حذف من قاعدة البيانات)"""
    users = load_users()
    user_str = str(user_id)
    if user_str in users:
        del users[user_str]
        return save_users(users)
    return False

def get_user_data(user_id):
    """الحصول على بيانات مستخدم"""
    users = load_users()
    return users.get(str(user_id), None)

# ================== حالات المحادثة للتسجيل ==================
FULL_NAME, FAMILY_HEAD, PHONE, WHATSAPP = range(4)

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

# ================== دوال البوت ==================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """بداية التفاعل مع البوت"""
    user = update.effective_user
    user_id = user.id
    
    # التحقق من حالة المستخدم
    if is_user_approved(user_id):
        # مستخدم موافق عليه - عرض التطبيق مباشرة
        keyboard = [
            [InlineKeyboardButton(
                "💰 فتح تطبيق وزنة مصاريف",
                web_app=WebAppInfo(url=WEBAPP_URL)
            )],
            [InlineKeyboardButton("📖 دليل الاستخدام", callback_data="help")],
            [InlineKeyboardButton("👤 بياناتي", callback_data="my_info")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            f"✅ *مرحباً {user.first_name}!*\n\n"
            "أنت مسجل ومعتمد في نظام وزنة مصاريف 💰\n\n"
            "يمكنك البدء باستخدام التطبيق الآن:",
            parse_mode="Markdown",
            reply_markup=reply_markup
        )
        logger.info(f"✅ مستخدم معتمد دخل: {user_id} - {user.first_name}")
        return
    
    # التحقق إذا كان في انتظار الموافقة
    user_data = get_user_data(user_id)
    if user_data and not user_data.get('approved', False):
        await update.message.reply_text(
            "⏳ *طلبك قيد المراجعة*\n\n"
            "تم إرسال طلب التسجيل الخاص بك للإدارة.\n"
            "سيتم إشعارك فور الموافقة على طلبك.\n\n"
            "⏰ يرجى الانتظار...",
            parse_mode="Markdown"
        )
        return
    
    # مستخدم جديد - عرض خيار التسجيل
    keyboard = [
        [InlineKeyboardButton("📝 تسجيل حساب جديد", callback_data="register")],
        [InlineKeyboardButton("ℹ️ معلومات عن التطبيق", callback_data="about")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        f"👋 *أهلاً وسهلاً {user.first_name}!*\n\n"
        "مرحباً بك في تطبيق *وزنة مصاريف* 💰\n\n"
        "📊 *نظام شامل لإدارة ميزانية الأسرة:*\n"
        "• تحليل الدخل والمصاريف\n"
        "• تقارير شهرية وسنوية\n"
        "• تحليل الموقف المالي\n"
        "• حفظ التقارير كصور\n\n"
        "🔐 *للوصول إلى التطبيق:*\n"
        "يرجى التسجيل أولاً للحصول على حساب معتمد",
        parse_mode="Markdown",
        reply_markup=reply_markup
    )


async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """معالج الأزرار"""
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    
    if query.data == "register":
        # التحقق مرة أخرى
        if is_user_approved(user_id):
            await query.edit_message_text(
                "✅ أنت مسجل بالفعل!\n"
                "استخدم /start للوصول إلى التطبيق."
            )
            return
        
        user_data = get_user_data(user_id)
        if user_data and not user_data.get('approved', False):
            await query.edit_message_text(
                "⏳ *طلبك قيد المراجعة*\n\n"
                "تم إرسال طلب التسجيل الخاص بك للإدارة.\n"
                "سيتم إشعارك فور الموافقة على طلبك.",
                parse_mode="Markdown"
            )
            return
        
        # بدء عملية التسجيل
        await query.edit_message_text(
            "📝 *عملية التسجيل*\n\n"
            "سنحتاج بعض المعلومات لإنشاء حسابك:\n\n"
            "✅ الاسم الكامل\n"
            "✅ اسم ولي أمر الأسرة\n"
            "✅ رقم الهاتف\n"
            "✅ رقم الواتساب\n\n"
            "🔒 *ملاحظة:* جميع بياناتك محمية ولن تُستخدم إلا للتواصل\n\n"
            "❓ أرسل الآن *الاسم الكامل*:",
            parse_mode="Markdown"
        )
        return FULL_NAME
    
    elif query.data == "about":
        await query.edit_message_text(
            "ℹ️ *عن تطبيق وزنة مصاريف*\n\n"
            "💰 *وزنة مصاريف* هو نظام متكامل لإدارة وتحليل "
            "ميزانية الأسرة بطريقة احترافية وسهلة.\n\n"
            "🎯 *المميزات:*\n"
            "• إدارة مصادر الدخل المتعددة\n"
            "• تصنيف المصاريف بشكل تفصيلي\n"
            "• تحليل تلقائي للموقف المالي\n"
            "• توصيات لتحسين الوضع المالي\n"
            "• تقارير قابلة للطباعة والمشاركة\n"
            "• واجهة عربية سهلة الاستخدام\n\n"
            "📱 للتسجيل، اضغط /start",
            parse_mode="Markdown"
        )
    
    elif query.data == "help":
        await show_help(query)
    
    elif query.data == "my_info":
        user_data = get_user_data(user_id)
        if user_data:
            await query.edit_message_text(
                f"👤 *بياناتك المسجلة:*\n\n"
                f"📛 الاسم: {user_data.get('full_name', 'غير متوفر')}\n"
                f"👨‍👩‍👧‍👦 ولي الأمر: {user_data.get('family_head', 'غير متوفر')}\n"
                f"📱 الهاتف: {user_data.get('phone', 'غير متوفر')}\n"
                f"💬 واتساب: {user_data.get('whatsapp', 'غير متوفر')}\n"
                f"📅 تاريخ التسجيل: {user_data.get('registration_date', 'غير متوفر')[:10]}\n"
                f"✅ الحالة: معتمد",
                parse_mode="Markdown"
            )
        else:
            await query.edit_message_text("❌ لم نتمكن من العثور على بياناتك")


async def show_help(query):
    """عرض دليل الاستخدام"""
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

*💡 نصائح:*
• استخدم الوضع الليلي/النهاري حسب تفضيلك
• يمكنك إضافة عدة مصادر دخل ومصاريف
• التقارير تُحفظ بتاريخ اليوم تلقائياً

*📞 الدعم:*
للمساعدة، تواصل مع المطور
"""
    await query.edit_message_text(help_text, parse_mode="Markdown")


# ================== عملية التسجيل (Conversation Handler) ==================

async def registration_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """بداية التسجيل - طلب الاسم الكامل"""
    await update.message.reply_text(
        "📝 *عملية التسجيل*\n\n"
        "✅ أرسل الآن *الاسم الكامل*:",
        parse_mode="Markdown"
    )
    return FULL_NAME


async def get_full_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """استقبال الاسم الكامل"""
    full_name = update.message.text.strip()
    
    if len(full_name) < 3:
        await update.message.reply_text(
            "❌ الاسم قصير جداً.\n"
            "يرجى إدخال الاسم الكامل (على الأقل 3 أحرف):"
        )
        return FULL_NAME
    
    context.user_data['full_name'] = full_name
    
    await update.message.reply_text(
        f"✅ تم حفظ الاسم: *{full_name}*\n\n"
        "✅ أرسل الآن *اسم ولي أمر الأسرة*:",
        parse_mode="Markdown"
    )
    return FAMILY_HEAD


async def get_family_head(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """استقبال اسم ولي الأمر"""
    family_head = update.message.text.strip()
    
    if len(family_head) < 3:
        await update.message.reply_text(
            "❌ الاسم قصير جداً.\n"
            "يرجى إدخال اسم ولي أمر الأسرة (على الأقل 3 أحرف):"
        )
        return FAMILY_HEAD
    
    context.user_data['family_head'] = family_head
    
    await update.message.reply_text(
        f"✅ تم حفظ اسم ولي الأمر: *{family_head}*\n\n"
        "✅ أرسل الآن *رقم الهاتف*:\n"
        "مثال: 0501234567 أو +966501234567",
        parse_mode="Markdown"
    )
    return PHONE


async def get_phone(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """استقبال رقم الهاتف"""
    phone = update.message.text.strip()
    
    # تنظيف رقم الهاتف
    phone = phone.replace(' ', '').replace('-', '')
    
    if len(phone) < 10:
        await update.message.reply_text(
            "❌ رقم الهاتف غير صحيح.\n"
            "يرجى إدخال رقم هاتف صحيح:\n"
            "مثال: 0501234567"
        )
        return PHONE
    
    context.user_data['phone'] = phone
    
    await update.message.reply_text(
        f"✅ تم حفظ رقم الهاتف: *{phone}*\n\n"
        "✅ أرسل الآن *رقم الواتساب*:\n"
        "مثال: 0501234567 أو +966501234567\n\n"
        "💡 إذا كان نفس رقم الهاتف، أرسل: نفس الرقم",
        parse_mode="Markdown"
    )
    return WHATSAPP


async def get_whatsapp(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """استقبال رقم الواتساب وإنهاء التسجيل"""
    whatsapp = update.message.text.strip()
    
    # إذا كتب "نفس الرقم"
    if 'نفس' in whatsapp or 'same' in whatsapp.lower():
        whatsapp = context.user_data['phone']
    else:
        # تنظيف رقم الواتساب
        whatsapp = whatsapp.replace(' ', '').replace('-', '')
        
        if len(whatsapp) < 10:
            await update.message.reply_text(
                "❌ رقم الواتساب غير صحيح.\n"
                "يرجى إدخال رقم واتساب صحيح:\n"
                "مثال: 0501234567\n\n"
                "أو اكتب: نفس الرقم"
            )
            return WHATSAPP
    
    context.user_data['whatsapp'] = whatsapp
    
    # جمع كل البيانات
    user_id = update.effective_user.id
    username = update.effective_user.username
    first_name = update.effective_user.first_name
    
    user_data = {
        'telegram_id': user_id,
        'telegram_username': username,
        'telegram_first_name': first_name,
        'full_name': context.user_data['full_name'],
        'family_head': context.user_data['family_head'],
        'phone': context.user_data['phone'],
        'whatsapp': context.user_data['whatsapp']
    }
    
    # حفظ في قاعدة البيانات
    if add_pending_user(user_id, user_data):
        # إرسال للمستخدم
        await update.message.reply_text(
            "✅ *تم إرسال طلب التسجيل بنجاح!*\n\n"
            "📋 *ملخص بياناتك:*\n"
            f"• الاسم: {user_data['full_name']}\n"
            f"• ولي الأمر: {user_data['family_head']}\n"
            f"• الهاتف: {user_data['phone']}\n"
            f"• واتساب: {user_data['whatsapp']}\n\n"
            "⏳ *الخطوة التالية:*\n"
            "تم إرسال طلبك للإدارة للمراجعة.\n"
            "سيتم إشعارك فور الموافقة على طلبك.\n\n"
            "🔔 ابقَ متابعاً للإشعارات!",
            parse_mode="Markdown"
        )
        
        # إرسال للأدمن
        if ADMIN_ID:
            keyboard = [
                [
                    InlineKeyboardButton("✅ قبول", callback_data=f"approve_{user_id}"),
                    InlineKeyboardButton("❌ رفض", callback_data=f"reject_{user_id}")
                ]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await context.bot.send_message(
                chat_id=ADMIN_ID,
                text=f"🆕 *طلب تسجيل جديد*\n\n"
                     f"👤 *معلومات المستخدم:*\n"
                     f"• Telegram ID: `{user_id}`\n"
                     f"• Username: @{username if username else 'لا يوجد'}\n"
                     f"• الاسم على Telegram: {first_name}\n\n"
                     f"📋 *البيانات المُدخلة:*\n"
                     f"• الاسم الكامل: {user_data['full_name']}\n"
                     f"• ولي أمر الأسرة: {user_data['family_head']}\n"
                     f"• رقم الهاتف: {user_data['phone']}\n"
                     f"• رقم الواتساب: {user_data['whatsapp']}\n\n"
                     f"⏰ التاريخ: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n\n"
                     f"❓ هل توافق على هذا الطلب؟",
                parse_mode="Markdown",
                reply_markup=reply_markup
            )
            logger.info(f"📤 تم إرسال طلب تسجيل للأدمن: {user_id}")
        else:
            logger.warning("⚠️ لم يتم إرسال للأدمن - ADMIN_ID غير موجود")
    else:
        await update.message.reply_text(
            "❌ حدث خطأ في حفظ البيانات.\n"
            "يرجى المحاولة مرة أخرى: /start"
        )
    
    # مسح البيانات المؤقتة
    context.user_data.clear()
    return ConversationHandler.END


async def cancel_registration(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """إلغاء التسجيل"""
    context.user_data.clear()
    await update.message.reply_text(
        "❌ تم إلغاء عملية التسجيل.\n"
        "يمكنك البدء من جديد بإرسال /start"
    )
    return ConversationHandler.END


# ================== معالج موافقة/رفض الأدمن ==================

async def admin_decision(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """معالجة قرار الأدمن (موافقة أو رفض)"""
    query = update.callback_query
    await query.answer()
    
    # التحقق من أن المستخدم هو الأدمن
    if query.from_user.id != ADMIN_ID:
        await query.answer("❌ غير مصرح لك بهذا الإجراء", show_alert=True)
        return
    
    data = query.data
    action, user_id = data.split('_')
    user_id = int(user_id)
    
    user_data = get_user_data(user_id)
    
    if not user_data:
        await query.edit_message_text(
            "❌ لم يتم العثور على بيانات المستخدم.\n"
            "ربما تم حذفه أو معالجة الطلب مسبقاً."
        )
        return
    
    if action == "approve":
        # الموافقة على المستخدم
        if approve_user(user_id):
            await query.edit_message_text(
                f"✅ *تمت الموافقة على الطلب*\n\n"
                f"👤 المستخدم: {user_data['full_name']}\n"
                f"📱 Telegram ID: `{user_id}`\n"
                f"📅 تاريخ الموافقة: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n\n"
                f"✉️ تم إشعار المستخدم بالموافقة.",
                parse_mode="Markdown"
            )
            
            # إشعار المستخدم
            try:
                keyboard = [
                    [InlineKeyboardButton(
                        "💰 فتح تطبيق وزنة مصاريف",
                        web_app=WebAppInfo(url=WEBAPP_URL)
                    )]
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)
                
                await context.bot.send_message(
                    chat_id=user_id,
                    text=f"🎉 *مبروك {user_data['full_name']}!*\n\n"
                         "✅ تمت الموافقة على طلب التسجيل الخاص بك!\n\n"
                         "يمكنك الآن استخدام تطبيق *وزنة مصاريف* 💰\n\n"
                         "📱 اضغط على الزر أدناه للبدء:",
                    parse_mode="Markdown",
                    reply_markup=reply_markup
                )
                logger.info(f"✅ تمت الموافقة على المستخدم: {user_id}")
            except Exception as e:
                logger.error(f"خطأ في إرسال إشعار الموافقة: {e}")
        else:
            await query.edit_message_text("❌ حدث خطأ في الموافقة على الطلب")
    
    elif action == "reject":
        # رفض المستخدم
        if reject_user(user_id):
            await query.edit_message_text(
                f"❌ *تم رفض الطلب*\n\n"
                f"👤 المستخدم: {user_data['full_name']}\n"
                f"📱 Telegram ID: `{user_id}`\n"
                f"📅 تاريخ الرفض: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n\n"
                f"✉️ تم إشعار المستخدم بالرفض.",
                parse_mode="Markdown"
            )
            
            # إشعار المستخدم
            try:
                await context.bot.send_message(
                    chat_id=user_id,
                    text=f"❌ *عذراً {user_data['full_name']}*\n\n"
                         "تم رفض طلب التسجيل الخاص بك.\n\n"
                         "💡 يمكنك التواصل مع الإدارة لمعرفة الأسباب.",
                    parse_mode="Markdown"
                )
                logger.info(f"❌ تم رفض المستخدم: {user_id}")
            except Exception as e:
                logger.error(f"خطأ في إرسال إشعار الرفض: {e}")
        else:
            await query.edit_message_text("❌ حدث خطأ في رفض الطلب")


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """أمر المساعدة"""
    await update.message.reply_text(
        "📖 *قائمة الأوامر المتاحة:*\n\n"
        "/start - بدء التفاعل مع البوت\n"
        "/help - عرض هذه المساعدة\n"
        "/cancel - إلغاء عملية التسجيل\n\n"
        "💡 للتسجيل، استخدم /start",
        parse_mode="Markdown"
    )


async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """معالج الأخطاء"""
    error = context.error
    
    # معالجة خاصة لخطأ Conflict
    if "Conflict" in str(error) and "terminated by other getUpdates" in str(error):
        logger.error("❌ خطأ Conflict: هناك نسخة أخرى من البوت تعمل!")
        logger.info("💡 الحل: أوقف جميع نسخ البوت الأخرى أو استخدم stop_old_bot.py")
        return
    
    logger.error(f"❌ خطأ: {error}")


# ================== MAIN ==================

def main():
    logger.info(f"🚀 بدء تشغيل البوت")
    logger.info(f"🌐 رابط Web App: {WEBAPP_URL}")
    logger.info(f"👑 Admin ID: {ADMIN_ID if ADMIN_ID else 'غير محدد'}")
    
    # بدء HTTP Server
    Thread(target=run_http_server, daemon=True).start()
    
    # تنظيف أي نسخ قديمة من البوت
    try:
        import requests
        logger.info("🔄 تنظيف البوت القديم...")
        # حذف webhook
        requests.get(f"https://api.telegram.org/bot{BOT_TOKEN}/deleteWebhook?drop_pending_updates=true", timeout=5)
        logger.info("✅ تم تنظيف البوت")
    except Exception as e:
        logger.warning(f"⚠️ تحذير في التنظيف: {e}")
    
    # إنشاء التطبيق
    application = Application.builder().token(BOT_TOKEN).build()
    
    # Conversation Handler للتسجيل
    registration_conv = ConversationHandler(
        entry_points=[
            CallbackQueryHandler(button_handler, pattern="^register$")
        ],
        states={
            FULL_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_full_name)],
            FAMILY_HEAD: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_family_head)],
            PHONE: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_phone)],
            WHATSAPP: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_whatsapp)],
        },
        fallbacks=[CommandHandler("cancel", cancel_registration)],
    )
    
    # إضافة المعالجات
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(registration_conv)
    application.add_handler(CallbackQueryHandler(admin_decision, pattern="^(approve|reject)_"))
    application.add_handler(CallbackQueryHandler(button_handler))
    
    # معالج الأخطاء
    application.add_error_handler(error_handler)
    
    # بدء البوت
    logger.info("✅ البوت جاهز للعمل")
    application.run_polling(
        allowed_updates=Update.ALL_TYPES,
        drop_pending_updates=True
    )

if __name__ == "__main__":
    main()
