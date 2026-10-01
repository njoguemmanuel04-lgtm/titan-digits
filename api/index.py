import os
from flask import Flask, request
import telebot

BOT_TOKEN = os.environ.get("BOT_TOKEN", "")
bot = telebot.TeleBot(BOT_TOKEN) if BOT_TOKEN else None
app = Flask(__name__)

def titan_analyze(digits_list):
    freq = {}
    for d in digits_list:
        freq[d] = freq.get(d, 0) + 1
    sorted_freq = sorted(freq.items(), key=lambda x: x[1], reverse=True)
    hot = [str(k) for k,v in sorted_freq[:3]]
    cold = [str(k) for k,v in sorted_freq[-3:]]
    total = len(digits_list)
    even = sum(1 for d in digits_list if d % 2 == 0)
    odd = total - even
    last10 = ' '.join(map(str, digits_list[-10:]))

    text = f"🔥 TITAN V8.9 ANTI-1006\n\n"
    text += f"History: {total} digits\nLast 10: {last10}\n\n"
    text += f"Frequency:\n"
    for k,v in sorted_freq:
        text += f"{k}: {v} times\n"
    text += f"\nEven: {even} | Odd: {odd}\n"
    text += f"\nHOT: {', '.join(hot)}\nCOLD: {', '.join(cold)}\n"
    text += f"\n🎯 PREDICTION: {', '.join(hot)}\n"
    text += f"\nSend more digits!"
    return text

@bot.message_handler(commands=['start'])
def start(m):
    bot.reply_to(m, "🔥 Titan Digits Bot ONLINE!\n\nSend /digits")

@bot.message_handler(commands=['digits'])
def digits(m):
    bot.reply_to(m, "🔢 TITAN READY\nSend 20+ digits like:\n1 2 3 4 5 6 7 8 9 0 1 2 3")

@bot.message_handler(func=lambda m: True)
def all_msg(m):
    txt = m.text or ""
    digits = [int(c) for c in txt if c.isdigit()]
    if len(digits) >= 5:
        res = titan_analyze(digits)
        bot.reply_to(m, res)
    else:
        bot.reply_to(m, "Send digits please. Example: 1 2 3 4 5 6 7 8 9 0")

@app.route('/')
def home():
    return "TITAN ONLINE"

@app.route('/setwebhook')
def setwebhook():
    if not bot:
        return "BOT_TOKEN missing in Vercel"
    base = request.url_root.replace('http://', 'https://')
    url = base + 'webhook'
    bot.remove_webhook()
    bot.set_webhook(url=url)
    return f'{{"ok":true,"webhook":"{url}"}}'

@app.route('/webhook', methods=['POST'])
def webhook():
    if bot and request.is_json:
        update = telebot.types.Update.de_json(request.get_data().decode('utf-8'))
        bot.process_new_updates([update])
    return 'ok', 200
