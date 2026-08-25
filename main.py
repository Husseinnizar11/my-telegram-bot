import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, InlineQueryResultArticle, InputTextMessageContent
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler, 
    CallbackQueryHandler, InlineQueryHandler, ContextTypes, ConversationHandler, filters
)

TOKEN = '8838346361:AAHZJCx5afaOERHjLeEugRbdGhB57PJcWv4'

# States
WAITING_PHOTO, WAITING_TEXT, WAITING_LAYOUT = range(3)

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
    await update.message.reply_text("تمت إضافة الصورة بنجاح! الخطوة الثانية: أرسل الآن وصف الصورة (النص).")
    return WAITING_TEXT

# 3. استلام النص وتحديد ترتيب الأزرار
async def receive_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['text'] = update.message.text
    
    # خيارات الترتيب
    keyboard = [
        [InlineKeyboardButton("أفقية (زرين بجانب بعض)", callback_data="layout_horizontal")],
        [InlineKeyboardButton("عمودية (زر فوق زر)", callback_data="layout_vertical")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text("الخطوة الثالثة: اختر ترتيب أزرار التحميل والمعاينة:", reply_markup=reply_markup)
    return WAITING_LAYOUT

# 4. اختيار الترتيب وعرض المنشور النهائي
async def set_layout(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    layout = query.data
    btn_preview = InlineKeyboardButton("معاينة الصورة ↗️", url="https://google.com")
    btn_download = InlineKeyboardButton("تحميل الصورة ↗️", url="https://google.com")
    
    if layout == "layout_horizontal":
        buttons = [[btn_preview, btn_download]]
    else:
        buttons = [[btn_preview], [btn_download]]
        
    context.user_data['buttons_markup'] = InlineKeyboardMarkup(buttons)
    
    # عرض المنشور النهائي مع زر المشاركة
    share_button = InlineKeyboardMarkup([
        [InlineKeyboardButton("📲 مشاركة المنشور مع صديق", switch_inline_query=context.user_data['text'][:20])]
    ])
    
    await context.bot.send_photo(
        chat_id=query.message.chat_id,
        photo=context.user_data['photo'],
        caption=f"إليك وصف الصورة المرفقة:\n{context.user_data['text']}",
        reply_markup=context.user_data['buttons_markup']
    )
    
    await query.message.reply_text("تم إنشاء المنشور بنجاح! اضغط على الزر أدناه لمشاركته مباشرة في أي محادثة:", reply_markup=share_button)
    return ConversationHandler.END

# إلغاء العملية
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
        },
        fallbacks=[CommandHandler('cancel', cancel)]
    )

    app.add_handler(conv_handler)
    print("البوت يعمل بالتسلسل المطلوب...")
    app.run_polling()
