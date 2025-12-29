import os
import telebot
from google.cloud import vision
from telebot.types import Message

# توکن از متغیر محیطی (در Render تنظیم می‌شه)
BOT_TOKEN = os.environ.get('BOT_TOKEN')
if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN در متغیرهای محیطی تنظیم نشده است!")

# مسیر فایل credentials که Render از Secret File می‌سازه
credentials_path = '/app/google_credentials.json'

# چک کردن وجود فایل
if not os.path.exists(credentials_path):
    raise FileNotFoundError(f"فایل credentials پیدا نشد: {credentials_path}")

os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = credentials_path

bot = telebot.TeleBot(BOT_TOKEN)
client = vision.ImageAnnotatorClient()

print("بات با موفقیت شروع شد و آنلاین است!")

@bot.message_handler(commands=['start', 'help'])
def send_welcome(message: Message):
    bot.reply_to(message, 
                 "سلام! 👋\n"
                 "یک عکس از متن فارسی بفرستید (صفحه کتاب، جزوه، پوستر، دست‌نویس و ...)\n"
                 "متن رو با دقت بالا و چینش درست استخراج می‌کنم.\n"
                 "قدرت گرفته از Google Vision AI")

@bot.message_handler(content_types=['photo'])
def handle_photo(message: Message):
    try:
        bot.reply_to(message, "در حال پردازش عکس... ⏳")

        file_id = message.photo[-1].file_id
        file_info = bot.get_file(file_id)
        downloaded_file = bot.download_file(file_info.file_path)

        image = vision.Image(content=downloaded_file)
        response = client.document_text_detection(image=image)

        if response.text_annotations:
            full_text = response.text_annotations[0].description.strip()

            if not full_text:
                bot.reply_to(message, "متنی در عکس پیدا نشد.")
                return

            if len(full_text) > 4000:
                txt_file = "extracted_text.txt"
                with open(txt_file, "w", encoding="utf-8") as f:
                    f.write(full_text)
                with open(txt_file, "rb") as f:
                    bot.send_document(message.chat.id, f, caption="📄 متن کامل استخراج‌شده")
                os.remove(txt_file)
            else:
                bot.reply_to(message, full_text)

            bot.reply_to(message, "✅ استخراج با موفقیت انجام شد!")

        else:
            bot.reply_to(message, "متنی تشخیص داده نشد. عکس رو واضح‌تر بفرستید.")

    except Exception as e:
        bot.reply_to(message, f"⚠️ خطا: {str(e)}\nدوباره امتحان کنید.")

bot.infinity_polling()
