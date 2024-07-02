import telebot
from main import print_out
from config import config

bot = telebot.TeleBot(config["tg_token"])

@bot.message_handler(commands=['start', 'help', 'test'])
def send_welcome(message):
    reply_text = "Hello " + message.from_user.first_name + ",\nWelcome to Weizenbierfreunde F3!"
    bot.reply_to(message, reply_text)

@bot.message_handler(func=lambda m: True)
def print_tg(message):
    to_print = "Telegram message from: " + message.from_user.first_name + "\n\n" + message.text
    reply_text = "Hello " + message.from_user.first_name + ",\nThanks, your message was sent to the printer!"
    print_out(to_print)
    bot.send_message(message.chat.id, reply_text)

bot.delete_webhook()
bot.infinity_polling()