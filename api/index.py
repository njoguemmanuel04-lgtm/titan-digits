import os
from flask import Flask, request
import telebot

BOT_TOKEN = os.environ.get("BOT_TOKEN", "")
bot = telebot.TeleBot(BOT_TOKEN) if BOT_TOKEN else None
app = Flask(__name__)

def titan_analyze(digits):
    from collections import Counter
    total = len(digits)
    c = Counter(digits)
    sorted_c = c.most_common()
    hot = [str(k) for k,v in sorted_c[:3]]
    cold = [str(k) for k,v in sorted_c[-3:]]
    even = sum(1 for d in digits if d % 2 == 0)
    odd = total - even
    last10 = ' '.join(map(str, digits[-10:]))
    # streak detection
    freq_text = "\n".join([f"{k}: {v} ({round(v/total*100,1)}%)" for k,v in sorted_c])

    return f"""🔥 TITAN V8.9 ANTI-1006
━━━━━━━━━━━━━━━━
📊 Total: {total} | Last 10: {last10}

📈 FREQUENCY:
{freq_text}

⚖️ Even: {even} | Odd: {odd}

🔥 HOT: {', '.join(hot)}
❄️ COLD: {', '.join(cold)}

🎯 PREDICTION: {', '.join(hot)}
🛡️ Anti-1006: ACTIVE
⚡ WARP + DIGIT EDGE

Send next digits to re-analyze!
"""

@bot.message_handler(commands=['start'])
def start(m):
    bot.reply_to(m, "🔥 Titan Digits Bot ONLINE!\n\n✅ Vercel: ACTIVE\n✅ Forever: NO SLEEP\n\nSend /digits")

@bot.message_handler(commands=['digits'])
def digits_cmd(m):
    bot.reply_to(m, "🔢 TITAN V8.9 READY\n\nSend 20+ digits separated by space:\n\nExample:\n1 5 8 2 9 0 3 4 7 1 2 5 8 9 0 3 1 4 6 7 8")

@bot.message_handler(func=lambda x: True)
def all_msg(m):
    txt = m.text or ""
    digits = [int(ch) for ch in txt if ch.isdigit()]
    if len(digits) >= 8:
        bot.reply_to(m, titan_analyze(digits))
    else:
        bot.reply_to(m, "Send digits please. Example: 1 2 3 4 5 6 7 8 9")

@app.route('/')
def home():
    return "🔥 TITAN V8.9 ONLINE - Go to /setwebhook"

@app.route('/setwebhook')
def sethook():
    base = request.url_root.replace('http://','https://')
    url = base + 'webhook'
    bot.remove_webhook()
    bot.set_webhook(url=url)
    return f'{{"ok":true,"webhook":"{url}"}}'

@app.route('/webhook', methods=['POST'])
def webhook():
    if bot and request.data:
        update = telebot.types.Update.de_json(request.data.decode('utf-8'))
        bot.process_new_updates([update])
    return 'ok', 200
