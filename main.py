import logging
import uuid
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, InlineQueryResultArticle, InputTextMessageContent, InlineQueryResultPhoto
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler, 
    CallbackQueryHandler, InlineQueryHandler, ContextTypes, ConversationHandler, filters
)

TOKEN = '8838346361:AAHZJCx5afaOERHjLeEugRbdGhB57PJcWv4'

# ذاكرة لتخزين المنشورات الجاهزة للمشاركة
posts_db = {}

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
    await update.message.reply_text("تمت إضافة الصورة بنجاح! الخطوة الثانية: أرسل الآن وصف الصورة.")
    return WAITING_TEXT

# 3. استلام النص وتنسيق المستخدم
async def receive_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['text'] = update.message.text
    context.user_data['entities'] = update.message.entities or update.message.caption_entities
    
    keyboard = [
        [InlineKeyboardButton("أفقية (بجانب بعض)", callback_data="layout_horizontal")],
        [InlineKeyboardButton("عمودية (فوق بعض)", callback_data="layout_vertical")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text("الخطوة الثالثة: اختر شكل ترتيب الأزرار (أفقي أم عمودي):", reply_markup=reply_markup)
    return WAITING_LAYOUT

# 4. طلب تفاصيل الأزرار
async def set_layout(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    context.user_data['layout'] = query.data
    
    msg = (
        "الخطوة الرابعة: أرسل الآن الأزرار والروابط التي تريدها.\n\n"
        "أرسل كل زر في سطر منفصل بهذا الشكل:\n"
        "اسم الزر - الرابط"
    )
    
    await query.message.reply_text(msg)
    return WAITING_BUTTONS_DATA

# 5. معالجة الأزرار وتجهيز المنشور للمشاركة المباشرة
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

    final_keyboard = []
    if layout == "layout_horizontal" and len(parsed_buttons) > 1:
        final_keyboard.append(parsed_buttons[:2])
        for btn in parsed_buttons[2:]:
            final_keyboard.append([btn])
    else:
        for btn in parsed_buttons:
            final_keyboard.append([btn])

    buttons_markup = InlineKeyboardMarkup(final_keyboard)
    
    # حفظ المنشور برقم تعريفي فريد للمشاركة المباشرة
    post_id = str(uuid.uuid4())[:8]
    posts_db[post_id] = {
        'photo': context.user_data['photo'],
        'caption': context.user_data['text'],
        'entities': context.user_data['entities'],
        'markup': buttons_markup
    }
    
    # إرسال معاينة داخل المحادثة
    await context.bot.send_photo(
        chat_id=update.effective_chat.id,
        photo=context.user_data['photo'],
        caption=context.user_data['text'],
        caption_entities=context.user_data['entities'],
        reply_markup=buttons_markup
    )
    
    # زر المشاركة المباشرة
    bot_info = await context.bot.get_me()
    share_button = InlineKeyboardMarkup([
        [InlineKeyboardButton("📲 إرسال المنشور مباشرة", switch_inline_query=post_id)]
    ])
    
    await update.message.reply_text("تم إنشاء المنشور بنجاح! اضغط على الزر أدناه لإرساله مباشرة في أي محادثة أو قناة:", reply_markup=share_button)
    return ConversationHandler.END

# معالجة مشاركة المنشور عبر الـ Inline Mode
async def inline_query_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.inline_query.query.strip()
    
    if query in posts_db:
        post = posts_db[query]
        results = [
            InlineQueryResultPhoto(
                id=query,
                photo_file_id=post['photo'],
                title="إرسال المنشور",
                caption=post['caption'],
                caption_entities=post['entities'],
                reply_markup=post['markup']
            )
        ]
        await update.inline_query.answer(results, cache_time=1)

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
    app.add_handler(InlineQueryHandler(inline_query_handler))
    
    print("البوت يعمل ويدعم المشاركة المباشرة بكفاءة...")
    app.run_polling()
