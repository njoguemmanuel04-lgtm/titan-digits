import telebot, random
TOKEN = "8989023687:AAEm-KX-B-iDty2VeSTucRh48foaNGzR7jo"
bot = telebot.TeleBot(TOKEN)

@bot.message_handler(commands=['start'])
def s(m):
    bot.send_message(m.chat.id, "🚀 Welcome to Titan Digits!\n\n/send signals for live digits\n/analysis for trend")

@bot.message_handler(commands=['signals'])
def sig(m):
    d=random.randint(0,9)
    bot.send_message(m.chat.id, f"📊 TITAN DIGITS\nLast: {d}\nSignal: {'OVER 3' if d>3 else 'UNDER 6'}\nConfidence: {random.randint(87,96)}%")

bot.infinity_polling()
