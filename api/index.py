import os
from flask import Flask, request
import telebot
from collections import Counter

BOT_TOKEN = os.environ.get("BOT_TOKEN", "")
bot = telebot.TeleBot(BOT_TOKEN) if BOT_TOKEN else None
app = Flask(__name__)

def titan_kingpin(digits):
    total = len(digits)
    c = Counter(digits)
    sorted_c = c.most_common()

    hot = [str(k) for k,v in sorted_c[:3]]
    cold = [str(k) for k,v in sorted_c[-3:]]

    last10 = digits[-10:]
    last = digits[-1]

    even = sum(1 for d in digits if d % 2 == 0)
    over = sum(1 for d in digits if d >= 5)
    warp_even = sum(1 for d in last10 if d % 2 == 0)
    warp_over = sum(1 for d in last10 if d >= 5)

    # MATCHES / DIFFERS KINGPIN LOGIC
    # Most frequent = best for MATCHES, least frequent = best for DIFFERS
    matches_pick = sorted_c[0][0] # most frequent
    matches_percent = round(sorted_c[0][1]/total*100,1)

    differs_pick = sorted_c[-1][0] # least frequent = rarely appears, so DIFFERS wins most
    differs_percent = round(100 - (sorted_c[-1][1]/total*100),1)

    # WARP detection for MATCHES/DIFFERS
    last10_counter = Counter(last10)
    warp_hot = last10_counter.most_common(1)[0][0] if last10 else matches_pick

    # Anti-1006
    anti = "ACTIVE ✅"
    if digits[-3:] in [[0,0,6],[1,0,0],[1,0,0,6]]:
        anti = "⚠️ 1006 PATTERN - WAIT 2 TICKS!"

    # Confidence
    conf_matches = matches_percent + (10 if warp_hot == matches_pick else 0)
    conf_differs = differs_percent

    freq = "\n".join([f"{k}: {v} ({round(v/total*100,1)}%)" for k,v in sorted_c])

    return f"""🔥 TITAN V9.2 KINGPIN
👑 MATCHES / DIFFERS MODE
━━━━━━━━━━━━━━━━━━
📊 Total: {total} | Last: {last} | Last10: {' '.join(map(str,last10))}

📊 FREQ:
{freq}

🔥 HOT: {', '.join(hot)}
❄️ COLD: {', '.join(cold)}

━━━━━━━━━━━━━━━━━━
👑 KINGPIN PICKS:

🎯 MATCHES: {matches_pick}
   Hit Rate: {matches_percent}% | WARP: {'🔥' if warp_hot==matches_pick else '⚖️'}
   Play: MATCHES {matches_pick} -> Stake HIGH if last was not {matches_pick}

🛡️ DIFFERS: {differs_pick}
   Win Rate: {differs_percent}% (since {differs_pick} rarely comes)
   Play: DIFFERS {differs_pick} -> SAFEST KINGPIN!
   WARP Safe: {'✅ YES' if differs_pick not in last10[-3:] else '⚠️ Wait'}

⚖️ Even/Odd: {'EVEN' if warp_even>=6 else 'ODD'} ({warp_even}/10)
📈 Over/Under: {'OVER 4' if warp_over>=6 else 'UNDER 4'} ({warp_over}/10)

🛡️ Anti-1006: {anti}
💰 KINGPIN: Play DIFFERS {differs_pick} for SAFE | MATCHES {matches_pick} for RISKY

⚡ WARP + MATCHES/DIFFERS EDGE ACTIVE
"""

@bot.message_handler(commands=['start'])
def start(m):
    bot.reply_to(m, "🔥 TITAN V9.2 KINGPIN ONLINE!\n\n👑 MATCHES / DIFFERS MODE ACTIVE\n🔢 /digits to analyze\n\nSend digits!")

@bot.message_handler(commands=['digits'])
def digits_cmd(m):
    bot.reply_to(m, "🔢 KINGPIN READY!\n\nSend 20+ digits:\nExample: 1 5 8 2 9 0 3 4 7 1 2 5 8 9 0 3 1 4\n\nI will give MATCHES & DIFFERS pick!")

@bot.message_handler(func=lambda x: True)
def all_msg(m):
    txt = m.text or ""
    digits = [int(ch) for ch in txt if ch.isdigit()]
    if len(digits) >= 8:
        bot.reply_to(m, titan_kingpin(digits))
    else:
        bot.reply_to(m, "Send 8+ digits for MATCHES/DIFFERS Kingpin!")

@app.route('/')
def home():
    return "🔥 TITAN V9.2 KINGPIN MATCHES/DIFFERS ONLINE"

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
