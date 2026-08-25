import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler, 
    CallbackQueryHandler, ContextTypes, ConversationHandler, filters
)

TOKEN = '8838346361:AAHZJCx5afaOERHjLeEugRbdGhB57PJcWv4'

# States
WAITING_PHOTO, WAITING_TEXT, WAITING_LAYOUT, WAITING_BUTTONS_DATA = range(4)

# 1. بداية المحادثة
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    await update.message.reply_text("أهلاً بك! الخطوة الأولى: الرجاء إرسال الصورة الآن.")
    return WAITING_PHOTO

# 2. استلام الصورة
async def receive_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message.photo:
        await update.message.reply_text("الرجاء إرسال صورة صحيحة.")
        return WAITING_PHOTO
        
    context.user_data['photo'] = update.message.photo[-1].file_id
    await update.message.reply_text("تمت إضافة الصورة بنجاح! الخطوة الثانية: أرسل الآن وصف الصورة (يمكنك تنسيق النص بنفسك واختيار اقتباس من خيارات تليجرام).")
    return WAITING_TEXT

# 3. استلام النص وتنسيق المستخدم
async def receive_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # حفظ النص والتنسيقات (Entities) التي حددها المستخدم بنفسه
    context.user_data['text'] = update.message.text
    context.user_data['entities'] = update.message.entities or update.message.caption_entities
    
    keyboard = [
        [InlineKeyboardButton("أفقية (بجانب بعض)", callback_data="layout_horizontal")],
        [InlineKeyboardButton("عمودية (فوق بعض)", callback_data="layout_vertical")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text("الخطوة الثالثة: اختر شكل ترتيب الأزرار (أفقي أم عمودي):", reply_markup=reply_markup)
    return WAITING_LAYOUT

# 4. طلب تفاصيل الأزرار والروابط من المستخدم
async def set_layout(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    context.user_data['layout'] = query.data
    
    msg = (
        "الخطوة الرابعة: أرسل الآن الأزرار والروابط التي تريدها.\n\n"
        "أرسل كل زر في سطر منفصل بهذا الشكل:\n"
        "اسم الزر - الرابط\n\n"
        "مثال:\n"
        "تحميل الصورة - https://example.com"
    )
    
    await query.message.reply_text(msg)
    return WAITING_BUTTONS_DATA

# 5. معالجة الأزرار وإرسال المنشور بتنسيق المستخدم الأصلي
async def process_buttons_and_show(update: Update, context: ContextTypes.DEFAULT_TYPE):
    raw_text = update.message.text
    layout = context.user_data.get('layout', 'layout_vertical')
    
    parsed_buttons = []
    for line in raw_text.split('\n'):
        if '-' in line:
            parts = line.split('-', 1)
            btn_text = parts[0].strip()
            btn_url = parts[1].strip()
            if btn_url.startswith('http://') or btn_url.startswith('https://'):
                parsed_buttons.append(InlineKeyboardButton(text=btn_text, url=btn_url))

    if not parsed_buttons:
        await update.message.reply_text("لم يتم التعرف على الأزرار! يرجى إرسالها بالصيغة الصحيحة:\nاسم الزر - الرابط")
        return WAITING_BUTTONS_DATA

    # بناء شكل الأزرار
    final_keyboard = []
    if layout == "layout_horizontal" and len(parsed_buttons) > 1:
        final_keyboard.append(parsed_buttons[:2])
        for btn in parsed_buttons[2:]:
            final_keyboard.append([btn])
    else:
        for btn in parsed_buttons:
            final_keyboard.append([btn])

    context.user_data['buttons_markup'] = InlineKeyboardMarkup(final_keyboard)
    
    # زر مشاركة المنشور
    share_button = InlineKeyboardMarkup([
        [InlineKeyboardButton("📲 مشاركة المنشور مع صديق", switch_inline_query=context.user_data['text'][:20])]
    ])
    
    # إرسال الصورة بنصها المنسق الأصلي الذي اختاره المستخدم
    await context.bot.send_photo(
        chat_id=update.effective_chat.id,
        photo=context.user_data['photo'],
        caption=context.user_data['text'],
        caption_entities=context.user_data['entities'],
        reply_markup=context.user_data['buttons_markup']
    )
    
    await update.message.reply_text("تم إنشاء المنشور بنجاح! اضغط على الزر أدناه لمشاركته في أي محادثة:", reply_markup=share_button)
    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("تم إلغاء العملية.")
    return ConversationHandler.END

if __name__ == '__main__':
    app = ApplicationBuilder().token(TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            WAITING_PHOTO: [MessageHandler(filters.PHOTO, receive_photo)],
            WAITING_TEXT: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_text)],
            WAITING_LAYOUT: [CallbackQueryHandler(set_layout, pattern="^layout_")],
            WAITING_BUTTONS_DATA: [MessageHandler(filters.TEXT & ~filters.COMMAND, process_buttons_and_show)],
        },
        fallbacks=[CommandHandler('cancel', cancel)]
    )

    app.add_handler(conv_handler)
    print("البوت يعمل وينقل تنسيق النص واقتباسات المستخدم بذكاء...")
    app.run_polling()
