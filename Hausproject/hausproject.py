import sqlite3
import requests
from bs4 import BeautifulSoup
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, CallbackContext
from openai import AsyncOpenAI
from dotenv import load_dotenv,dotenv_values
import os

load_dotenv()
TOKEN = '7410652636:AAG0WuFcJ3rR7GKnxW32tfmefto2TnE5a7Q'

# Veritabanı bağlantısı
conn = sqlite3.connect('haus.db')
cursor = conn.cursor()

# AsyncOpenAI istemcisini oluşturma
client = AsyncOpenAI(api_key=os.getenv("api_key"))


# HAUS World web sitesinden veri almak için fonksiyon
def get_haus_info(url):
    try:
        response = requests.get(url)
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'html.parser')
            info = soup.get_text(separator=' ', strip=True)
            return info
        else:
            print(f"Error fetching data from {url}. Status code: {response.status_code}")
            return None
    except requests.exceptions.RequestException as e:
        print(f"Error fetching data from {url}: {str(e)}")
        return None


# Başlangıç komutu işleyicisi
async def start(update: Update, context: CallbackContext):
    await context.bot.send_message(chat_id=update.effective_chat.id,
                                   text='HAUS Centrifuge Technologies botuna hoş geldiniz!')


# Mesaj işleyicisi
async def reply_to_message(update: Update, context: CallbackContext):
    question = update.message.text
    # Veritabanından anahtar kelimeleri ve içerikleri çekme
    cursor.execute("SELECT KeyWords, Content FROM Haus")
    keyword_content_pairs = cursor.fetchall()

    # Kullanıcı sorusu ile eşleşen içeriği bulma
    found_answer = False
    for keywords, content in keyword_content_pairs:
        if any(keyword in question.lower() for keyword in keywords.split(',')):
            try:
                # OpenAI ile cevap almak için API kullanımı
                response = await client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=[
                        {"role": "system",
                         "content": f"You are a helpful assistant. Here is some information about HAUS Centrifuge Technologies: {content}"},
                        {"role": "user", "content": question}
                    ],
                    timeout=40,
                    temperature=1,
                    max_tokens=256,
                    top_p=1,
                    frequency_penalty=0,
                    presence_penalty=0
                )
                answer = response.choices[
                    0].message.content.strip() if response and response.choices else "Üzgünüm, cevap bulunamadı."
            except Exception as e:
                answer = f"Üzgünüm, bir hata oluştu: {str(e)}"

            await context.bot.send_message(chat_id=update.effective_chat.id, text=answer)
            found_answer = True
            break

    if not found_answer:
        urls = [
            'https://www.hausworld.com',
            'https://www.hausworld.com/corporate/about-us',
            'https://www.hausworld.com/corporate/contact-us',
            # Diğer HAUS World sitesi sayfaları buraya eklenebilir
        ]

        # HAUS World sitesinden bilgi al
        haus_info = ""
        for url in urls:
            info = get_haus_info(url)
            if info:
                haus_info += info + "\n\n"

        if haus_info:
            try:
                # OpenAI ile cevap almak için API kullanımı
                response = await client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=[
                        {"role": "system",
                         "content": f"You are a helpful assistant. Here is some information about HAUS Centrifuge Technologies: {haus_info}"},
                        {"role": "user", "content": question}
                    ],
                    timeout=40,
                    temperature=1,
                    max_tokens=256,
                    top_p=1,
                    frequency_penalty=0,
                    presence_penalty=0
                )
                answer = response.choices[
                    0].message.content.strip() if response and response.choices else "Üzgünüm, cevap bulunamadı."
            except Exception as e:
                answer = f"Üzgünüm, bir hata oluştu: {str(e)}"
        else:
            answer = "Üzgünüm, şu anda web sitesinden bilgi alamıyoruz. Lütfen daha sonra tekrar deneyin."

        await context.bot.send_message(chat_id=update.effective_chat.id, text=answer)


# Telegram botu oluşturma ve ayarlama
def main() -> None:
    application = ApplicationBuilder().token(TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, reply_to_message))

    application.run_polling()


if __name__ == '__main__':
    main()
