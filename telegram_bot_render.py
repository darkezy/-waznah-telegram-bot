#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
بوت وزنة مصاريف - نظام الموافقة/الرفض اليدوي
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
CHANNEL_IDS = os.environ.get('CHANNEL_IDS', '@username_qanatek').split(',')
WEB_APP_URL = os.environ.get('WEB_APP_URL', 'https://waznah.com')
ADMIN_ID = int(os.environ.get('ADMIN_ID', '0'))
PORT = int(os.environ.get('PORT', 10000))

if not BOT_TOKEN:
    logger.error("❌ BOT_TOKEN غير موجود")
    exit(1)

# ================== تخزين الطلبات ==================
join_requests = {}  # {user_id: {data}}

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
    """التحقق من عضوية المستخدم"""
    for channel_id in CHANNEL_IDS:
        try:
            channel_id = channel_id.strip()
            if not channel_id:
                continue
            member = await bot.get_chat_member(channel_id, user_id)
            if member.status in ["member", "administrator", "creator"]:
                return True
        except Exception as e:
            logger.error(f"❌ خطأ التحقق من {channel_id}: {e}")
    return False

# ================== BOT LOGIC ==================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """/start مع خيار تقديم طلب"""
    user = update.effective_user
    
    # ✅ التحقق من العضوية
    is_member = await check_membership(user.id, context.bot)
    
    if is_member:
        # المستخدم عضو - السماح بالوصول
        await update.effective_message.reply_text(
            f"✅ *تم التحقق من العضوية*\n\n"
            f"👤 أهلاً {user.first_name}\n"
            f"📊 [افتح نظام الميزانية]({WEB_APP_URL})",
            parse_mode="Markdown"
        )
        logger.info(f"✅ دخول ناجح: {user.id}")
        return

    # ❌ ليس عضواً - عرض أزرار الانضمام + طلب الانضمام
    buttons = []
    for ch_id in CHANNEL_IDS:
        ch_id = ch_id.strip()
        if ch_id:
            buttons.append([InlineKeyboardButton(
                f"📢 انضم إلى {ch_id}", 
                url=f"https://t.me/{ch_id[1:]}"
            )])
    
    # ➕ زر تقديم طلب جديد
    buttons.append([
        InlineKeyboardButton(
            "📝 تقديم طلب انضمام", 
            callback_data=f"request_join:{user.id}"
        )
    ])
    
    await update.effective_message.reply_text(
        "⚠️ *يجب أن تكون عضواً في قنواتنا/مجموعاتنا*\n\n"
        "اختر أحد الخيارات:",
        reply_markup=InlineKeyboardMarkup(buttons),
        parse_mode="Markdown"
    )
    logger.warning(f"🚫 ليس عضواً: {user.id}")

async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """معالجة جميع الأزرار"""
    query = update.callback_query
    await query.answer()
    
    # استخراج البيانات
    try:
        action, target_user_id = query.data.split(":")
        target_user_id = int(target_user_id)
    except:
        await query.message.reply_text("❌ خطأ في المعالجة")
        return
    
    # 📝 طلب الانضمام (من المستخدم)
    if action == "request_join":
        user = update.effective_user
        
        # منع التكرار
        if user.id in join_requests:
            await query.message.reply_text("⚠️ لقد قدمت طلباً بالفعل، انتظر الموافقة.")
            return
        
        # تخزين الطلب
        join_requests[user.id] = {
            "telegram_id": user.id,
            "username": user.username,
            "first_name": user.first_name,
            "timestamp": datetime.now().isoformat()
        }
        
        # ✅ إشعار المشرف مع أزرار الموافقة/الرفض
        admin_buttons = [
            [
                InlineKeyboardButton(
                    "✅ موافق", 
                    callback_data=f"approve:{user.id}"
                ),
                InlineKeyboardButton(
                    "❌ رفض", 
                    callback_data=f"reject:{user.id}"
                )
            ]
        ]
        
        admin_msg = (
            f"📝 *طلب انضمام جديد*\n\n"
            f"👤 الاسم: {user.first_name}\n"
            f"🆔 المعرف: `@{user.username}`\n"
            f"🔢 الID: `{user.id}`\n"
            f"⏰ الوقت: {datetime.now().strftime('%Y-%m-%d %H:%M')}"
        )
        
        try:
            await context.bot.send_message(
                chat_id=ADMIN_ID,
                text=admin_msg,
                reply_markup=InlineKeyboardMarkup(admin_buttons),
                parse_mode="Markdown"
            )
            await query.message.reply_text(
                "✅ تم إرسال طلبك بنجاح!\n\n"
                "⏳ سيتم مراجعته خلال 24 ساعة.\n"
                "📩 ستصلك رسالة عند اتخاذ القرار."
            )
            logger.info(f"📝 طلب جديد: {user.id}")
        except Exception as e:
            logger.error(f"❌ خطأ إرسال للمشرف: {e}")
            await query.message.reply_text("❌ خطأ في إرسال الطلب، تواصل مع المشرف.")
    
    # ✅ الموافقة (من المشرف)
    elif action == "approve" and query.from_user.id == ADMIN_ID:
        if target_user_id not in join_requests:
            await query.message.reply_text("⚠️ الطلب غير موجود أو تمت معالجته.")
            return
        
        user_data = join_requests[target_user_id]
        del join_requests[target_user_id]
        
        # إشعار المستخدم بالموافقة
        try:
            await context.bot.send_message(
                chat_id=target_user_id,
                text=(
                    "🎉 *تهانينا! تمت الموافقة على طلبك*\n\n"
                    "يمكنك الآن استخدام نظام الميزانية:\n"
                    "👉 https://t.me/WaznahBot?startapp=main"
                ),
                parse_mode="Markdown"
            )
            await query.message.edit_text(
                f"✅ *تمت الموافقة*\n\nالمستخدم: {user_data['first_name']}",
                reply_markup=None
            )
            logger.info(f"✅ الموافقة على: {target_user_id}")
        except Exception as e:
            logger.error(f"❌ خطأ في إشعار المستخدم: {e}")
            await query.message.reply_text("❌ خطأ في إرسال الإشعار")
    
    # ❌ الرفض (من المشرف)
    elif action == "reject" and query.from_user.id == ADMIN_ID:
        if target_user_id not in join_requests:
            await query.message.reply_text("⚠️ الطلب غير موجود أو تمت معالجته.")
            return
        
        user_data = join_requests[target_user_id]
        del join_requests[target_user_id]
        
        # إشعار المستخدم بالرفض
        try:
            await context.bot.send_message(
                chat_id=target_user_id,
                text=(
                    "❌ *عذراً، تم رفض طلبك*\n\n"
                    "يرجى التأكد من استيفاء الشروط والمحاولة لاحقاً."
                ),
                parse_mode="Markdown"
            )
            await query.message.edit_text(
                f"❌ *تم الرفض*\n\nالمستخدم: {user_data['first_name']}",
                reply_markup=None
            )
            logger.info(f"❌ رفض: {target_user_id}")
        except Exception as e:
            logger.error(f"❌ خطأ في إشعار المستخدم: {e}")
            await query.message.reply_text("❌ خطأ في إرسال الإشعار")

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """/help بالعربية"""
    await update.effective_message.reply_text("""
📋 **الأوامر:**
• `/start` - بدء استخدام البوت
• `/help` - عرض القائمة

⚠️ البوت حصري لأعضاء قنواتنا/مجموعاتنا
    """, parse_mode="Markdown")

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.error(f"❌ خطأ: {context.error}")

# ================== MAIN ==================

def main():
    logger.info(f"🚀 بدء تشغيل البوت")
    logger.info(f"📋 القنوات/المجموعات: {CHANNEL_IDS}")
    logger.info(f"👑 المشرف: {ADMIN_ID}")

    Thread(target=run_http_server, daemon=True).start()

    application = Application.builder().token(BOT_TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CallbackQueryHandler(handle_callback))  # معالجة الأزرار
    
    application.add_error_handler(error_handler)

    application.run_polling(
        allowed_updates=Update.ALL_TYPES,
        drop_pending_updates=True
    )

if __name__ == "__main__":
    main()
