import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler, 
    ContextTypes, ConversationHandler, filters
)

TOKEN = '8838346361:AAFE5CVv-dQ-rl4pl73Zy_IM2FWYKM5h1yg'

TEXT, BUTTONS, CONFIRM = range(3)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    reply_keyboard = [['✨ إنشاء منشور']]
    markup = ReplyKeyboardMarkup(reply_keyboard, resize_keyboard=True)
    await update.message.reply_text(
        "القائمة الرئيسية:\nاختر ما تريد من الأزرار أدناه:",
        reply_markup=markup
    )

async def new_post(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "أرسل الآن نص المنشور الذي تريد نشره:",
        reply_markup=ReplyKeyboardRemove()
    )
    return TEXT

async def get_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['post_text'] = update.message.text
    await update.message.reply_text(
        "ممتاز! الآن أرسل الأزرار بهذا الشكل:\n"
        "اسم الزر - الرابط\n\n"
        "مثال:\n"
        "رابط الموقع - https://google.com\n"
        "قناتنا - https://t.me"
    )
    return BUTTONS

async def get_buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    raw_text = update.message.text
    inline_keyboard = []
    
    lines = raw_text.split('\n')
    for line in lines:
        if '-' in line:
            parts = line.split('-', 1)
            btn_text = parts[0].strip()
            btn_url = parts[1].strip()
            if btn_url.startswith('http://') or btn_url.startswith('https://'):
                inline_keyboard.append([InlineKeyboardButton(text=btn_text, url=btn_url)])

    if not inline_keyboard:
        await update.message.reply_text("الرجاء إرسال الأزرار بالصيغة الصحيحة (اسم الزر - الرابط):")
        return BUTTONS

    context.user_data['keyboard'] = InlineKeyboardMarkup(inline_keyboard)
    
    await update.message.reply_text("معاينة المنشور قبل الإرسال:")
    await update.message.reply_text(
        text=context.user_data['post_text'],
        reply_markup=context.user_data['keyboard']
    )

    confirm_keyboard = [['أرسل الآن إلى القناة', 'إلغاء']]
    await update.message.reply_text(
        "هل تريد إرسال هذا المنشور لقناتك؟",
        reply_markup=ReplyKeyboardMarkup(confirm_keyboard, resize_keyboard=True, one_time_keyboard=True)
    )
    return CONFIRM

async def send_post(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_choice = update.message.text

    if user_choice == 'أرسل الآن إلى القناة':
        await update.message.reply_text(
            "أرسل الآن معرف قناتك (مثال: `@my_channel`) أو قم بتوجيه أي رسالة من القناة إلى هنا:",
            reply_markup=ReplyKeyboardRemove()
        )
        return CONFIRM

    if user_choice.startswith('@') or user_choice.startswith('-100'):
        try:
            channel_id = user_choice.strip()
            await context.bot.send_message(
                chat_id=channel_id,
                text=context.user_data['post_text'],
                reply_markup=context.user_data['keyboard']
            )
            await update.message.reply_text("تم نشر المنشور في القناة بنجاح! 🎉")
        except Exception as e:
            await update.message.reply_text(f"حدث خطأ أثناء النشر: {e}\nتأكد أن البوت مشرف في القناة.")
        
        return await cancel(update, context)

    if user_choice == 'إلغاء':
        return await cancel(update, context)

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    reply_keyboard = [['✨ إنشاء منشور']]
    markup = ReplyKeyboardMarkup(reply_keyboard, resize_keyboard=True)
    await update.message.reply_text("تمت العودة للقائمة الرئيسية.", reply_markup=markup)
    return ConversationHandler.END

if __name__ == '__main__':
    app = ApplicationBuilder().token(TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[MessageHandler(filters.Regex('^✨ إنشاء منشور$'), new_post)],
        states={
            TEXT: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_text)],
            BUTTONS: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_buttons)],
            CONFIRM: [MessageHandler(filters.TEXT & ~filters.COMMAND, send_post)]
        },
        fallbacks=[CommandHandler('cancel', cancel), MessageHandler(filters.Regex('^إلغاء$'), cancel)]
    )

    app.add_handler(CommandHandler('start', start))
    app.add_handler(conv_handler)
    
    print("البوت يعمل بنظام الأزرار التفتاعلية الآن...")
    app.run_polling()
