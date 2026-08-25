import logging
from telegram import InlineQueryResultArticle, InputTextMessageContent, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import Application, InlineQueryHandler, CommandHandler

# التوكن الخاص بك
TOKEN = "8838346361:AAFE5CVv-dQ-rl4pl73Zy_IM2FWYKM5h1yg"

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

async def start(update, context):
    await update.message.reply_text(
        "أهلاً بك! 👋\n\n"
        "هذا البوت مخصص لنشر المنشورات والأزرار التفاعلية بحقوقك الخاصة.\n"
        "لاستخدامه، قم بكتابة معرف البوت في أي محادثة متبوعاً بالنص والأزرار."
    )

async def inline_query(update, context):
    query = update.inline_query.query.strip()
    if not query:
        return

    # تقسيم النص عن الأزرار عند استخدام الرمز |
    parts = [p.strip() for p in query.split('|')]
    text_content = parts[0]
    button_parts = parts[1:]

    buttons = []
    row = []

    for btn_def in button_parts:
        sub_parts = [s.strip() for s in btn_def.split('-')]
        if len(sub_parts) >= 2:
            btn_name = sub_parts[0]
            btn_url = sub_parts[1]
            if not btn_url.startswith('http'):
                btn_url = 'https://' + btn_url

            row.append(InlineKeyboardButton(text=btn_name, url=btn_url))
            if len(row) == 2:
                buttons.append(row)
                row = []

    if row:
        buttons.append(row)

    if not buttons:
        buttons = [[InlineKeyboardButton("🔗 رابط مخصص", url="https://t.me")]]

    keyboard = InlineKeyboardMarkup(buttons)

    results = [
        InlineQueryResultArticle(
            id="1",
            title="نشر المنشور بحقوقك",
            description=text_content[:50],
            input_message_content=InputTextMessageContent(
                text_content
            ),
            reply_markup=keyboard
        )
    ]

    await update.inline_query.answer(results, cache_time=1)

def main():
    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(InlineQueryHandler(inline_query))

    print("البوت يعمل الآن...")
    app.run_polling()

if __name__ == "__main__":
    main()