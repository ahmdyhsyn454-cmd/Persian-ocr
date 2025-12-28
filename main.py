import os
import telebot
from google.cloud import vision


BOT_TOKEN = os.environ['BOT_TOKEN']  # توکن از Environment Variables

import json
import os

# گرفتن محتوای JSON از متغیر محیطی
google_credentials_content = os.environ.get('GOOGLE_CREDENTIALS')

if not google_credentials_content:
    raise ValueError("متغیر GOOGLE_CREDENTIALS تنظیم نشده است!")

# تبدیل رشته JSON به دیکشنری
credentials_dict = json.loads(google_credentials_content)

# ساخت فایل موقت در /tmp (که Railway اجازه نوشتن داره)
temp_credentials_path = '/tmp/google_credentials.json'
with open(temp_credentials_path, 'w') as f:
    json.dump(credentials_dict, f)

# تنظیم مسیر برای گوگل
os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = temp_credentials_path

bot = telebot.TeleBot(BOT_TOKEN)
client = vision.ImageAnnotatorClient()

@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    bot.reply_to(message, "سلام! عکس متن فارسی بفرست تا با دقت بالا استخراج کنم (Google Vision)")

@bot.message_handler(content_types=['photo'])
def handle_photo(message):
    try:
        bot.reply_to(message, "در حال پردازش عکس...")

        file_id = message.photo[-1].file_id
        file_info = bot.get_file(file_id)
        downloaded_file = bot.download_file(file_info.file_path)

        image = vision.Image(content=downloaded_file)
        response = client.document_text_detection(image=image)

        if response.text_annotations:
            text = response.text_annotations[0].description
            if len(text) > 4096:
                with open("text.txt", "w", encoding="utf-8") as f:
                    f.write(text)
                with open("text.txt", "rb") as f:
                    bot.send_document(message.chat.id, f, caption="متن کامل استخراج‌شده")
                os.remove("text.txt")
            else:
                bot.reply_to(message, text)
        else:
            bot.reply_to(message, "متنی در عکس پیدا نشد.")

    except Exception as e:
        bot.reply_to(message, f"خطا: {str(e)}")

print("بات شروع شد!")
bot.infinity_polling()

