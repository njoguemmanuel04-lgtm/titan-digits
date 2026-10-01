import os
from flask import Flask, request
import telebot
from telebot import types

BOT_TOKEN = os.environ.get("BOT_TOKEN")
if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN not set in Vercel Environment Variables")

bot = telebot.TeleBot(BOT_TOKEN)
app = Flask(__name__)

# TITAN V8.9 Logic
def titan_analyze(digits_list):
    if not digits_list:
        return "❌ No digits found."

    # Count frequency
    freq = {}
    for d in digits_list:
        freq[d] = freq.get(d, 0) + 1

    # Hot, Cold, Due
    sorted_freq = sorted(freq.items(), key=lambda x: x[1], reverse=True)
    hot = [str(k) for k,v in sorted_freq[:3]]
    cold = [str(k) for k,v in sorted_freq[-3:]]

    total = len(digits_list)
    even = sum(1 for d in digits_list if d % 2 == 0)
    odd = total - even

    # Simple prediction logic
    prediction = hot # For now predict hot numbers
    confidence = round((freq[int(hot[0])] / total * 100) if hot else 0, 1)

    response = f"""🔥 **TITAN V8.9 ANTI-1006 ANALYSIS**

📊 **History:** {total} digits
🔢 Last 10: {' '.join(map(str, digits_list[-10:]))}

📈 **Frequency:**
"""
    for k,v in sorted_freq:
        response += f"{k}: {v} times ({round(v/total*100,1)}%)\n"

    response += f"""
⚖️ Even: {even} | Odd: {odd}

🔥 **HOT:** {', '.join(hot)}
❄️ **COLD:** {', '.join(cold)}

🎯 **TITAN PREDICTION:** {', '.join(prediction)}
📍 Confidence: {confidence}%
⚡ Mode: WARP + DIGIT EDGE

Send more digits to re-analyze!
"""
    return response

@bot.message_handler(commands=['start'])
def start(message):
    bot.reply_to(message, "🔥 Titan Digits Bot ONLINE!\n\nSend /digits to get digits\n\nThen send your history like:\n1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0")

@bot.message_handler(commands=['digits'])
def digits_cmd(message):
    bot.reply_to(message, "🔢 **TITAN READY**\n\nSend your last 20+ digits separated by space, e.g:\n\n`1 2 3 5 8 9 0 2 4 5 6 7 8 1 2 3 4 5 6 7`\n\nI will analyze with V8.9 ANTI-1006", parse_mode="Markdown")

@bot.message_handler(func=lambda m: True)
def handle_all(message):
    text = message.text.strip()
    # Try to extract digits 0-9 from text
    digits = []
    for ch in text.replace(',', ' ').split():
        if ch.isdigit():
            for c in ch:
                if c.isdigit():
                    digits.append(int(c))
        elif ch.strip().isdigit():
            digits.append(int(ch.strip()))

    # If user sent "1 2 3 4" format
    if len(digits) < 5:
        # Try another parse - just all digits in message
        digits = [int(c) for c in text if c.isdigit()]

    if len(digits) >= 5:
        result = titan_analyze(digits)
        bot.reply_to(message, result, parse_mode="Markdown")
    else:
        if text.lower() not in ['start', '/start', '/digits', 'start']:
            bot.reply_to(message, "Send /digits first, then send digits like:\n\n1 2 3 4 5 6 7 8 9 0 1 2 3")

# Flask routes for Vercel
@app.route('/')
def home():
    return "🔥 TITAN V8.9 ANTI-1006 - Bot is ONLINE - Go to /setwebhook to activate"

@app.route('/setwebhook')
def set_webhook():
    url = request.url_root.replace('http://', 'https://')
    webhook_url = url + 'webhook'
    # Remove old webhook and set new
    bot.remove_webhook()
    bot.set_webhook(url=webhook_url)
    return f'{{"ok":true,"result":true,"description":"Webhook was set to {webhook_url}"}}'

@app.route('/webhook', methods=['POST'])
def webhook():
    if request.headers.get('content-type') == 'application/json':
        json_string = request.get_data().decode('utf-8')
        update = telebot.types.Update.de_json(json_string)
        bot.process_new_updates([update])
        return 'ok', 200
    else:
        return 'ok', 200

# For local testing
if __name__ == '__main__':
    app.run()
