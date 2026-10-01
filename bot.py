import os
from threading import Thread
from flask import Flask
import requests
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters

# --- Keep Render Alive (IMPORTANT for Web Service) ---
app = Flask('')
@app.route('/')
def home():
    return "Titan Digits Bot is Live!"

def run_web():
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)

Thread(target=run_web, daemon=True).start()

# --- Bot Config ---
BOT_TOKEN = os.environ.get("BOT_TOKEN")  # Set this in Render Environment Variables

# --- Commands ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🔥 Welcome to TITAN DIGITS 🔥\n\n"
        "Your 24/7 Aviator Signals Bot.\n\n"
        "Commands:\n"
        "/start - Start bot\n"
        "/predict - Get next prediction\n"
        "/help - Help\n\n"
        "Bot is LIVE on Render!"
    )

async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "How to use:\n"
        "1. Send /predict\n"
        "2. Wait for signal\n"
        "3. Bet wisely!\n\n"
        "Website: https://titan-digits.vercel.app"
    )

async def predict(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Replace with your real prediction logic
    await update.message.reply_text(
        "📊 TITAN ANALYSIS...\n\n"
        "⏳ Next Round: 1.5x - 2.8x (Safe)\n"
        "💰 Confidence: 89%\n\n"
        "⚠️ Play 1x only, then wait!"
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Send /predict to get signal 🚀")

# --- Run Bot ---
if __name__ == "__main__":
    if not BOT_TOKEN:
        print("ERROR: BOT_TOKEN not set in Environment Variables!")
    else:
        print("Starting Titan Digits Bot...")
        app_bot = ApplicationBuilder().token(BOT_TOKEN).build()
        app_bot.add_handler(CommandHandler("start", start))
        app_bot.add_handler(CommandHandler("help", help_cmd))
        app_bot.add_handler(CommandHandler("predict", predict))
        app_bot.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
        app_bot.run_polling()
