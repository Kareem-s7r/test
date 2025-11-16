import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
import asyncio
from datetime import datetime, timedelta

# إعدادات التسجيل
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# رمز البوت - ضع الرمز الحقيقي هنا
BOT_TOKEN = "8502236014:AAFA8jtZx1fKUOSozgvnBHNOSydMwygD2G4"

# قاموس لتخزين المؤقتات النشطة
active_timers = {}

# أوامر البوت
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """رسالة الترحيب"""
    welcome_text = """
مرحباً! 👋 أنا بوت ساعة العد التنازلي ⏰

الأوامر المتاحة:
/start - عرض هذه الرسالة
/timer [ثواني] - بدء عد تنازلي
/cancel - إلغاء المؤقت النشط
/help - المساعدة

مثال:
/timer 60 - عد تنازلي لمدة دقيقة
/timer 300 - عد تنازلي لمدة 5 دقائق
"""
    await update.message.reply_text(welcome_text)

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """رسالة المساعدة"""
    help_text = """
كيفية استخدام البوت:

1. ابدأ مؤقتاً باستخدام /timer متبوعاً بعدد الثواني
2. يمكنك إلغاء المؤقت في أي وقت باستخدام /cancel
3. البوت سيرسل تنبيه عندما ينتهي الوقت

أمثلة:
/timer 30 - عد تنازلي 30 ثانية
/timer 120 - عد تنازلي دقيقتين
"""
    await update.message.reply_text(help_text)

async def timer_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """بدء عد تنازلي"""
    user_id = update.effective_user.id
    
    # التحقق من وجود مؤقت نشط
    if user_id in active_timers:
        await update.message.reply_text("⚠️ لديك مؤقت نشط بالفعل! استخدم /cancel لإلغائه أولاً.")
        return
    
    # التحقق من وجود معطيات
    if not context.args:
        await update.message.reply_text("❌ يرجى تحديد مدة العد التنازلي بالثواني\nمثال: /timer 60")
        return
    
    try:
        seconds = int(context.args[0])
        if seconds <= 0:
            await update.message.reply_text("❌ يرجى إدخال رقم موجب أكبر من الصفر")
            return
        if seconds > 86400:  # 24 ساعة
            await update.message.reply_text("❌ الحد الأقصى 24 ساعة (86400 ثانية)")
            return
    except ValueError:
        await update.message.reply_text("❌ يرجى إدخال رقم صحيح")
        return
    
    # بدء المؤقت
    await start_countdown(update, context, user_id, seconds)

async def start_countdown(update: Update, context: ContextTypes.DEFAULT_TYPE, user_id: int, seconds: int):
    """بدء العد التنازلي"""
    chat_id = update.effective_chat.id
    end_time = datetime.now() + timedelta(seconds=seconds)
    
    # حفظ المؤقت
    active_timers[user_id] = {
        'end_time': end_time,
        'seconds': seconds,
        'chat_id': chat_id
    }
    
    # رسالة البدء
    time_str = format_time(seconds)
    message = await update.message.reply_text(f"⏰ العد التنازلي بدأ: {time_str}")
    
    # تحديث المؤقت كل ثانية
    for remaining in range(seconds, 0, -1):
        if user_id not in active_timers:
            break
            
        time_str = format_time(remaining)
        try:
            await message.edit_text(f"⏳ الوقت المتبقي: {time_str}")
            await asyncio.sleep(1)
        except Exception as e:
            logging.error(f"Error updating timer: {e}")
            break
    
    # انتهاء المؤقت
    if user_id in active_timers:
        del active_timers[user_id]
        try:
            await message.edit_text("🔔 الوقت انتهى! ⏰")
            # إرسال تنبيه إضافي
            await context.bot.send_message(
                chat_id=chat_id,
                text="🎯 العد التنازلي انتهى!"
            )
        except Exception as e:
            logging.error(f"Error sending completion message: {e}")

async def cancel_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """إلغاء المؤقت النشط"""
    user_id = update.effective_user.id
    
    if user_id in active_timers:
        del active_timers[user_id]
        await update.message.reply_text("✅ تم إلغاء المؤقت")
    else:
        await update.message.reply_text("⚠️ لا يوجد مؤقت نشط لإلغائه")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """معالجة الرسائل النصية العادية"""
    text = update.message.text
    
    # إذا كان المستخدم يرسل أرقاماً فقط
    if text.isdigit():
        seconds = int(text)
        if 1 <= seconds <= 86400:
            user_id = update.effective_user.id
            if user_id not in active_timers:
                await start_countdown(update, context, user_id, seconds)
                return
    
    await update.message.reply_text("اكتب /help لمعرفة كيفية استخدام البوت")

def format_time(seconds: int) -> str:
    """تنسيق الوقت بصيغة جميلة"""
    if seconds < 60:
        return f"{seconds} ثانية"
    
    minutes, secs = divmod(seconds, 60)
    if minutes < 60:
        return f"{minutes:02d}:{secs:02d}"
    
    hours, minutes = divmod(minutes, 60)
    return f"{hours:02d}:{minutes:02d}:{secs:02d}"

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """معالج الأخطاء"""
    logging.error(f"حدث خطأ: {context.error}")

def main():
    """الدالة الرئيسية"""
    # إنشاء تطبيق البوت
    application = Application.builder().token(BOT_TOKEN).build()
    
    # إضافة المعالجات
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("timer", timer_command))
    application.add_handler(CommandHandler("cancel", cancel_command))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    # معالج الأخطاء
    application.add_error_handler(error_handler)
    
    # بدء البوت
    print("البوت يعمل...")
    application.run_polling()

if __name__ == "__main__":
    main()