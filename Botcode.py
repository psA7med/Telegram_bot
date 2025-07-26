import logging
import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    filters,
    ContextTypes
)
import requests
import os
import time

# إعداداتك الشخصية
TOKEN = os.getenv('BOT_TOKEN')
if not TOKEN:
    print("❌ خطأ: لم يتم العثور على BOT_TOKEN في متغيرات البيئة!")
    print("⏱ إغلاق البوت في خلال 10 ثواني...")
    time.sleep(10)
    exit(1)

N8N_WEBHOOK_URL = "https://uykk.app.n8n.cloud/webhook-test/fe10ed64-3dca-4c5d-bb43-d2f2a83dca68"
WHATSAPP_LINK = "https://wa.me/201285687227"

# إعدادات التسجيل
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    handlers=[
        logging.FileHandler("bot.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# قاموس لربط button_code باسم المادة
SUBJECTS = {
    "1": "فيزياء 1",
    "2": "فيزياء 2",
    "3": "رياضيات 2",
    "4": "إلكترونيات",
    "5": "أساسيات البرمجة"
}

# حالات المحادثة
AWAITING_QUESTION, AFTER_RESPONSE = range(2)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    keyboard = [
        [InlineKeyboardButton("فيزياء 1", callback_data="1")],
        [InlineKeyboardButton("فيزياء 2", callback_data="2")],
        [InlineKeyboardButton("رياضيات 2", callback_data="3")],
        [InlineKeyboardButton("إلكترونيات", callback_data="4")],
        [InlineKeyboardButton("أساسيات البرمجة", callback_data="5")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        "🦅 أهلاً وسهلاً بيك في بوت C# Eagles\n"
        "إختر المادة اللي عاوز تذاكرها أو تسأل فيها\n"
        "وأنا هكون معاك كأني الدكتور بتاعك 👨‍🏫",
        reply_markup=reply_markup
    )
    return AWAITING_QUESTION

async def handle_button(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    button_code = query.data
    chat_id = query.message.chat.id
    
    # تخزين button_code و chat_id في context.user_data
    context.user_data['button_code'] = button_code
    context.user_data['chat_id'] = chat_id
    
    # عرض رسالة وطلب كتابة الاستفسار
    subject = SUBJECTS.get(button_code, "المادة")
    await query.edit_message_text(
        text=f"🦅 تمام يا صاحبي، إخترت {subject}\n"
             "دلوقتي أنا هكون الدكتور بتاعك في المادة دي\n"
             "متترددش، اكتب سؤالك هنا وانا تحت أمرك 👇"
    )
    return AWAITING_QUESTION

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_message = update.message.text
    chat_id = update.message.chat.id
    
    # التحقق من اختيار المادة أولاً
    if context.user_data.get('chat_id') != chat_id or not context.user_data.get('button_code'):
        await update.message.reply_text(
            "⌛ ياباشا متسرعش! لازم تختار المادة أولاً\n"
            "إضغط على /start واختار المادة"
        )
        return AWAITING_QUESTION
    
    # تخزين النص في context.user_data
    context.user_data['message'] = user_message
    
    # عرض رسالة تأكيد مع زرين
    subject = SUBJECTS.get(context.user_data['button_code'], "المادة")
    await update.message.reply_text(
        f"✅ تمام يا غالي، ده السؤال بتاعك في {subject}:\n\n"
        f"« {user_message} »\n\n"
        "لو عاوز ترسله دلوقتي إضغط 'إرسال'،\n"
        "ولو عاوز تعدل السؤال إضغط 'تعديل السؤال'",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("✅ إرسال", callback_data="send"), 
             InlineKeyboardButton("✏️ تعديل السؤال", callback_data="retry")]
        ])
    )
    return AWAITING_QUESTION

async def handle_send(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    
    # جلب البيانات من context.user_data
    chat_id = context.user_data.get('chat_id')
    button_code = context.user_data.get('button_code')
    user_message = context.user_data.get('message')
    
    # التحقق من وجود كل البيانات
    if not all([chat_id, button_code, user_message]):
        await query.edit_message_text(
            text="❌ يا عم الحكاية ناقصة حاجات! لازم تبدأ من الأول\n"
                 "إضغط على /start واختار المادة واكتب السؤال تاني"
        )
        return
    
    # إرسال البيانات للـ Webhook
    payload = {
        "chat_id": chat_id,
        "button_code": button_code,
        "message": user_message
    }
    
    try:
        response = requests.post(N8N_WEBHOOK_URL, json=payload)
        if response.status_code == 200:
            # عرض رسالة التأكيد
            subject = SUBJECTS.get(button_code, "المادة")
            await query.edit_message_text(
                f"✅ تم إرسال سؤالك في {subject} للدكتور!\n"
                "هيرد عليك في خلال ثواني قليلة إن شاء الله"
            )
            
            # الانتظار 5 ثواني (افتراضيًا)
            await asyncio.sleep(5)
            
            # إرسال رسالة المتابعة بعد استلام الرد
            await context.bot.send_message(
                chat_id=chat_id,
                text="عاوز تسأل تاني في نفس المادة ولا في مادة جديدة؟",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("معايا كمان سؤال في نفس الماده", callback_data="same_subject")],
                    [InlineKeyboardButton("معايا سؤال تاني بس في ماده مختلفه", callback_data="new_subject")],
                    [InlineKeyboardButton("لا مش معايا أسئله تانيه", callback_data="no_questions")]
                ])
            )
            return AFTER_RESPONSE
        else:
            await query.edit_message_text(
                text=f"⚠️ فيه مشكلة فنية دلوقتي، تواصل مع صاحب البوت\n"
                     f"رابط تواصله: {WHATSAPP_LINK}\n"
                     f"كود الخطأ: {response.status_code}",
                parse_mode="HTML"
            )
    except Exception as e:
        await query.edit_message_text(
            text=f"🚨 للأسف حصل خطأ غير متوقع: {str(e)}\n"
                 f"لو سمحت تواصل مع صاحب البوت على {WHATSAPP_LINK} عشان يحل المشكلة"
        )

async def handle_retry(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    
    # مسح النص القديم من context.user_data
    context.user_data['message'] = None
    
    # طلب كتابة سؤال جديد
    subject = SUBJECTS.get(context.user_data.get('button_code', ''), "المادة")
    await query.edit_message_text(
        text=f"🦅 تمام يا بيه، هنتجاهل السؤال القديم\n"
             f"اتفضل اكتب سؤالك الجديد في {subject}:\n"
             "(ابعت السؤال الجديد دلوقتي)"
    )
    return AWAITING_QUESTION

async def handle_same_subject(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    
    # الاحتفاظ بنفس المادة
    button_code = context.user_data.get('button_code')
    subject = SUBJECTS.get(button_code, "المادة")
    
    # مسح السؤال القديم فقط
    context.user_data['message'] = None
    
    # طلب سؤال جديد في نفس المادة
    await query.edit_message_text(
        text=f"🦅 ادخل سؤال في الماده {subject}👇"
    )
    return AWAITING_QUESTION

async def handle_new_subject(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    
    # مسح البيانات القديمة
    context.user_data.clear()
    
    # عرض قائمة المواد
    keyboard = [
        [InlineKeyboardButton("فيزياء 1", callback_data="1")],
        [InlineKeyboardButton("فيزياء 2", callback_data="2")],
        [InlineKeyboardButton("رياضيات 2", callback_data="3")],
        [InlineKeyboardButton("إلكترونيات", callback_data="4")],
        [InlineKeyboardButton("أساسيات البرمجة", callback_data="5")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(
        "🦅 تمام يا بيه، إختر المادة الجديدة اللي عاوز تسأل فيها\n"
        "وأنا تحت أمرك 👇",
        reply_markup=reply_markup
    )
    return AWAITING_QUESTION

async def handle_no_questions(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    
    # إرسال رسالة الوداع مع زر إعادة البدء
    await query.edit_message_text(
        text="شكرًا على استخدامك البوت! تمنياتي بالنجاح والتفوق ✨",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("إعادة بدء", callback_data="start_over")]
        ])
    )
    # مسح بيانات المحادثة
    context.user_data.clear()
    return ConversationHandler.END

async def handle_start_over(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    
    # مسح البيانات القديمة
    context.user_data.clear()
    
    # إعادة بدء المحادثة
    keyboard = [
        [InlineKeyboardButton("فيزياء 1", callback_data="1")],
        [InlineKeyboardButton("فيزياء 2", callback_data="2")],
        [InlineKeyboardButton("رياضيات 2", callback_data="3")],
        [InlineKeyboardButton("إلكترونيات", callback_data="4")],
        [InlineKeyboardButton("أساسيات البرمجة", callback_data="5")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(
        "🦅 أهلاً تاني! إختر المادة اللي عاوز تسأل فيها\n"
        "وأنا تحت أمرك 👇",
        reply_markup=reply_markup
    )
    return AWAITING_QUESTION

async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Log the error and send a message to the user."""
    logger.error(msg="Exception while handling an update:", exc_info=context.error)
    
    # إرسال رسالة خطأ للمستخدم
    if update and hasattr(update, 'message'):
        await update.message.reply_text(
            '⚠️ يا سيدي حصل شوية بلبلة هنا!\n'
            'البوت هيشتغل تاني بعد 5 ثواني إن شاء الله'
        )

def run_bot():
    """تشغيل البوت مع إعادة التشغيل التلقائي"""
    while True:
        try:
            # إنشاء التطبيق
            application = Application.builder().token(TOKEN).build()
            
            # إضافة ConversationHandler
            conv_handler = ConversationHandler(
                entry_points=[CommandHandler("start", start)],
                states={
                    AWAITING_QUESTION: [
                        CallbackQueryHandler(handle_button, pattern="^[1-5]$"),
                        CallbackQueryHandler(handle_send, pattern="^send$"),
                        CallbackQueryHandler(handle_retry, pattern="^retry$"),
                        CallbackQueryHandler(handle_same_subject, pattern="^same_subject$"),
                        CallbackQueryHandler(handle_new_subject, pattern="^new_subject$"),
                        CallbackQueryHandler(handle_no_questions, pattern="^no_questions$"),
                        CallbackQueryHandler(handle_start_over, pattern="^start_over$"),
                        MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message)
                    ],
                    AFTER_RESPONSE: [
                        CallbackQueryHandler(handle_same_subject, pattern="^same_subject$"),
                        CallbackQueryHandler(handle_new_subject, pattern="^new_subject$"),
                        CallbackQueryHandler(handle_no_questions, pattern="^no_questions$"),
                        CallbackQueryHandler(handle_start_over, pattern="^start_over$")
                    ]
                },
                fallbacks=[CommandHandler("start", start)]
            )
            
            application.add_handler(conv_handler)
            
            # إضافة معالج الأخطاء
            application.add_error_handler(error_handler)
            
            # بدء البوت
            logger.info("🟢 بدء تشغيل البوت...")
            print("🟢 البوت شغال دلوقتي!")
            application.run_polling(drop_pending_updates=True, close_loop=False)
            
        except Exception as e:
            logger.error(f"🔴 خطأ حرج: {e}")
            logger.info("🔄 إعادة تشغيل البوت بعد 10 ثواني...")
            print(f"🔴 حصل خطأ: {e}")
            print("🔄 هنعيد تشغيل البوت بعد 10 ثواني...")
            time.sleep(10)

if __name__ == "__main__":
    # طباعة متغيرات البيئة للتشخيص
    print("=== تشخيص المتغيرات البيئية ===")
    print("قائمة المتغيرات البيئية المتاحة:")
    for key in os.environ:
        print(f"- {key}")
    print(f"BOT_TOKEN موجود؟ {'نعم' if 'BOT_TOKEN' in os.environ else 'لا'}")
    
    # التأكد من وجود التوكن
    if not TOKEN:
        print("❌ خطأ جسيم: التوكن غير موجود!")
        exit(1)
    
    print("""
    ██████╗  ██████╗ ████████╗
    ██╔══██╗██╔═══██╗╚══██╔══╝
    ██████╔╝██║   ██║   ██║   
    ██╔══██╗██║   ██║   ██║   
    ██████╔╝╚██████╔╝   ██║   
    ╚═════╝  ╚═════╝    ╚═╝   
    """)
    print("🦅 C# Eagles Bot - Version 2.1")
    print("✅ البوت بدأ التشغيل وبيعمل بشكل دائم")
    print(f"📞 للتواصل: {WHATSAPP_LINK}")
    print("🔄 أي مشكلة هيحلها ويشتغل تاني لوحده")
    print("⏱  إضغط Ctrl+C عشان توقفه لما تريد")
    run_bot()
