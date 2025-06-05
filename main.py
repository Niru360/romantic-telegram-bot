import openai
import os
from telegram import Update, ChatAction, InputFile
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
import asyncio
import pyttsx3
import tempfile
import speech_recognition as sr
from pydub import AudioSegment
from dotenv import load_dotenv

load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

SYSTEM_PROMPT = (
    "You are a romantic, poetic, emotionally intelligent chatbot. "
    "Your tone is like a late-night lover's conversation, with warm, deep, poetic Bengali-English mixed phrases. "
    "Be flirty, caring, dreamy, and real — like a boy and girl talking at 2AM."
)

async def chat_with_gpt(user_input):
    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_input}
            ],
            temperature=0.85,
            max_tokens=200
        )
        return response.choices[0].message.content.strip()
    except Exception:
        return "🥺 Sorry jaan, kichu ekta problem hoise... abar try koro plz."

async def simulate_typing(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action=ChatAction.TYPING)
    await asyncio.sleep(1.5)

def text_to_voice(text):
    engine = pyttsx3.init()
    engine.setProperty('rate', 150)
    fd, path = tempfile.mkstemp(suffix='.mp3')
    engine.save_to_file(text, path)
    engine.runAndWait()
    return path

def voice_to_text(voice_file_path):
    recognizer = sr.Recognizer()
    audio = AudioSegment.from_file(voice_file_path)
    wav_path = voice_file_path.replace(".ogg", ".wav")
    audio.export(wav_path, format="wav")
    with sr.AudioFile(wav_path) as source:
        audio_data = recognizer.record(source)
        try:
            text = recognizer.recognize_google(audio_data, language="bn-BD")
        except:
            text = ""
    os.remove(wav_path)
    return text

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_message = update.message.text
    await simulate_typing(update, context)
    reply = await chat_with_gpt(user_message)
    await update.message.reply_text(reply)
    try:
        audio_path = text_to_voice(reply)
        with open(audio_path, 'rb') as voice_file:
            await update.message.reply_voice(voice=InputFile(voice_file))
        os.remove(audio_path)
    except:
        pass

async def handle_voice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    voice = await update.message.voice.get_file()
    file_path = tempfile.mktemp(suffix=".ogg")
    await voice.download_to_drive(file_path)
    user_text = voice_to_text(file_path)
    os.remove(file_path)
    if not user_text:
        await update.message.reply_text("😔 Sorry jaan, তোমার ভয়েসটা ঠিকমতো বুঝতে পারলাম না...")
        return
    await simulate_typing(update, context)
    reply = await chat_with_gpt(user_text)
    await update.message.reply_text(f"🗣️ তুমি বলেছিলে: {user_text}

❤️ {reply}")
    try:
        audio_path = text_to_voice(reply)
        with open(audio_path, 'rb') as voice_file:
            await update.message.reply_voice(voice=InputFile(voice_file))
        os.remove(audio_path)
    except:
        pass

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🌙 হ্যালো জান! আমি তোমার late-night soulmate bot 💫 কিছু বলো তো... টেক্সট বা ভয়েস যেটা খুশি!")

if __name__ == '__main__':
    app = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    app.add_handler(MessageHandler(filters.VOICE, handle_voice))
    print("💘 Romantic GPT Telegram Bot with Voice Input/Output is running...")
    app.run_polling()
