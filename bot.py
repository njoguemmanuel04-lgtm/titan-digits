import os
import threading
from flask import Flask
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, MessageHandler, filters

BOT_TOKEN = os.getenv("BOT_TOKEN")

# Flask for Render
flask_app = Flask(__name__)
@flask_app.route('/')
def home():
    return "Titan Digits Bot Live!"

def run_flask():
    port = int(os.environ.get("PORT", 10000))
    flask_app.run(host='0.0.0.0', port=port)

# Telegram handlers
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🔥 Titan Digits Bot ONLINE!\nSend /digits to get digits")

async def digits(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Your Titan Digits Logic here - Bot is working!")

if __name__ == "__main__":
    if not BOT_TOKEN:
        raise ValueError("BOT_TOKEN missing!")
    threading.Thread(target=run_flask, daemon=True).start()
    
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("digits", digits))
    print("Starting Titan Digits Bot...")
    app.run_polling()
