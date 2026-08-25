import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler, 
    CallbackQueryHandler, ContextTypes, ConversationHandler, filters
)

TOKEN = '8838346361:AAHZJCx5afaOERHjLeEugRbdGhB57PJcWv4'

# States
START_BUILD, ADD_TEXT, ADD_BUTTONS, SEND_CHANNEL = range(4)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    reply_keyboard = [['✨ إنشاء منشور جديد']]
    markup = ReplyKeyboardMarkup(reply_keyboard, resize_keyboard=True)
    await update.message.reply_text(
        "أهلاً بك! أرسل لي (صورة أو نصاً) مباشرة للبدء بإنشاء المنشور:",
        reply_markup=markup
    )

async def handle_media_or_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    context.user_data['buttons'] = []
    
    if update.message.photo:
        context.user_data['photo'] = update.message.photo[-1].file_id
        context.user_data['caption'] = update.message.caption or ""
    elif update.message.text and update.message.text != '✨ إنشاء منشور جديد':
        context.user_data['caption'] = update.message.text

    await show_preview(update, context)
    return START_BUILD

async def show_preview(update: Update, context: ContextTypes.DEFAULT_TYPE):
    caption = context.user_data.get('caption', 'لا يوجد نص بعد.')
    buttons = context.user_data.get('buttons', [])
    
    inline_keyboard = []
    for btn in buttons:
        inline_keyboard.append([InlineKeyboardButton(text=btn['text'], url=btn['url'])])
    
    control_buttons = [
        [InlineKeyboardButton("📝 إضافة/تعديل نص", callback_data="add_text"), InlineKeyboardButton("➕ إضافة أزرار", callback_data="add_buttons")],
        [InlineKeyboardButton("🚀 نشر في القناة (Done)", callback_data="done"), InlineKeyboardButton("❌ إلغاء", callback_data="cancel")]
    ]
    
    full_keyboard = InlineKeyboardMarkup(inline_keyboard + control_buttons)

    chat_id = update.effective_chat.id

    if 'photo' in context.user_data:
        await context.bot.send_photo(
            chat_id=chat_id,
            photo=context.user_data['photo'],
            caption=f"**معاينة المنشور:**\n\n{caption}",
            reply_markup=full_keyboard,
            parse_mode='Markdown'
        )
    else:
        await context.bot.send_message(
            chat_id=chat_id,
            text=f"**معاينة المنشور:**\n\n{caption}",
            reply_markup=full_keyboard,
            parse_mode='Markdown'
        )

async def button_click(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "add_text":
        await query.message.reply_text("أرسل النص الجديد الآن:")
        return ADD_TEXT
    elif query.data == "add_buttons":
        await query.message.reply_text(
            "أرسل الأزرار بهذا الشكل:\n"
            "اسم الزر - الرابط\n\n"
            "مثال:\n"
            "موقعنا - https://google.com"
        )
        return ADD_BUTTONS
    elif query.data == "done":
        await query.message.reply_text("أرسل الآن معرف قناتك للنشر فيها (مثال: `@my_channel`):")
        return SEND_CHANNEL
    elif query.data == "cancel":
        context.user_data.clear()
        await query.message.reply_text("تم إلغاء المنشور بنجاح.")
        return ConversationHandler.END

async def receive_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['caption'] = update.message.text
    await show_preview(update, context)
    return START_BUILD

async def receive_buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    raw_text = update.message.text
    buttons = context.user_data.get('buttons', [])
    
    for line in raw_text.split('\n'):
        if '-' in line:
            parts = line.split('-', 1)
            btn_text = parts[0].strip()
            btn_url = parts[1].strip()
            if btn_url.startswith('http://') or btn_url.startswith('https://'):
                buttons.append({'text': btn_text, 'url': btn_url})

    context.user_data['buttons'] = buttons
    await show_preview(update, context)
    return START_BUILD

async def send_to_channel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    channel_id = update.message.text.strip()
    caption = context.user_data.get('caption', '')
    buttons = context.user_data.get('buttons', [])
    
    inline_keyboard = [[InlineKeyboardButton(text=b['text'], url=b['url'])] for b in buttons]
    reply_markup = InlineKeyboardMarkup(inline_keyboard) if inline_keyboard else None

    try:
        if 'photo' in context.user_data:
            await context.bot.send_photo(
                chat_id=channel_id,
                photo=context.user_data['photo'],
                caption=caption,
                reply_markup=reply_markup
            )
        else:
            await context.bot.send_message(
                chat_id=channel_id,
                text=caption,
                reply_markup=reply_markup
            )
        await update.message.reply_text("تم نشر المنشور في القناة بنجاح! 🎉")
    except Exception as e:
        await update.message.reply_text(f"حدث خطأ أثناء النشر: {e}\nتأكد أن البوت مشرف في القناة.")

    context.user_data.clear()
    return ConversationHandler.END

if __name__ == '__main__':
    app = ApplicationBuilder().token(TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[
            MessageHandler(filters.PHOTO | (filters.TEXT & ~filters.COMMAND), handle_media_or_start)
        ],
        states={
            START_BUILD: [CallbackQueryHandler(button_click)],
            ADD_TEXT: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_text)],
            ADD_BUTTONS: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_buttons)],
            SEND_CHANNEL: [MessageHandler(filters.TEXT & ~filters.COMMAND, send_to_channel)],
        },
        fallbacks=[CommandHandler('start', start)]
    )

    app.add_handler(CommandHandler('start', start))
    app.add_handler(conv_handler)

    print("البوت يعمل الآن بنفس مواصفات PostBot...")
    app.run_polling()
