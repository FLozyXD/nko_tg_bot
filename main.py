from dotenv import load_dotenv
import os
from telebot import types, TeleBot

load_dotenv()

bot = TeleBot(str(os.getenv('TOKEN')))

# показать кнопки главного меню
def show_main_menu(chat_id, text="Выберите действие:"):
    """Отправляет главное меню с кнопками."""
    markup = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    btn1 = types.KeyboardButton("Генерация текста")
    btn2 = types.KeyboardButton("Генерация картинки")
    btn3 = types.KeyboardButton("Редактор текста")
    btn4 = types.KeyboardButton("Создание контент-плана")
    btn5 = types.KeyboardButton("Информация о вашей НКО")
    markup.add(btn1, btn2, btn3, btn4, btn5)
    bot.send_message(chat_id, text, reply_markup=markup)

# обработчик команды /start
@bot.message_handler(commands=['start'])
def send_welcome(message):
    """Отправляет приветственное сообщение при старте."""
    welcome_text = (
        "Здравствуйте! Я бот-генератор контента для НКО.\n\n" \
        "Я помогу вам создавать тексты постов, идеи для визуалов и контент-планы. " \
        "Чтобы контент был более точным, рекомендую сначала заполнить информацию о вашей организации, нажав на кнопку 'Информация о вашей НКО'." \
    )
    show_main_menu(message.chat.id, welcome_text)

if __name__ == '__main__':
    print("Бот запущен...")
    bot.polling()