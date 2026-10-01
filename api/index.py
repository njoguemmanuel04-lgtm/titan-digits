import os
from flask import Flask, request
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
import asyncio
import requests

TOKEN = os.environ.get("BOT_TOKEN")
app = Flask(__name__)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🔥 TITAN Digit Edge Pro Online! Send me digits, I analyze with Titan!")

application = Application.builder().token(TOKEN).build()
application.add_handler(CommandHandler("start", start))

@app.route("/", methods=["GET"])
def home():
    return "TITAN Bot Alive - Go to /setwebhook to activate"

@app.route(f"/{TOKEN}", methods=["POST"])
def webhook():
    update = Update.de_json(request.get_json(force=True), application.bot)
    asyncio.run(application.process_update(update))
    return "ok"

@app.route("/setwebhook", methods=["GET"])
def setwebhook():
    url = f"https://api.telegram.org/bot{TOKEN}/setWebhook?url=https://titan-digits.vercel.app/{TOKEN}"
    r = requests.get(url)
    return r.text
