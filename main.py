from dotenv import load_dotenv
import os
from telebot.async_telebot import AsyncTeleBot
from telebot import types
import asyncio

load_dotenv()

bot = AsyncTeleBot(str(os.getenv('TOKEN')))

# меню для сотрудников
async def show_employee_menu(chat_id, text="Вы в меню для сотрудников. Выберите действие:"):
    """Отправляет меню с функциями для сотрудников НКО."""
    markup = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    btn1 = types.KeyboardButton("Новое мероприятие")
    btn2 = types.KeyboardButton("Создать контент")
    btn3 = types.KeyboardButton("Создать тест для волонтеров")
    btn4 = types.KeyboardButton("Новый сценарий")
    btn5 = types.KeyboardButton("Создать инструкцию для волонтеров")
    btn6 = types.KeyboardButton("Информация о вашей НКО")
    btn7 = types.KeyboardButton("🔙 Сменить роль")
    markup.add(btn1, btn2, btn3, btn4, btn5, btn6, btn7)
    await bot.send_message(chat_id, text, reply_markup=markup)

# меню для волонтеров
async def show_volunteer_menu(chat_id, text="Вы в меню для волонтеров. Выберите действие:"):
    """Отправляет меню с функциями для волонтеров."""
    markup = types.ReplyKeyboardMarkup(row_width=1, resize_keyboard=True)
    btn1 = types.KeyboardButton("Информация по мероприятию")
    btn2 = types.KeyboardButton("Тест для подтверждения компетенций")
    btn3 = types.KeyboardButton("Выбор мероприятия (будущие)")
    btn4 = types.KeyboardButton("🔙 Сменить роль")
    markup.add(btn1, btn2, btn3, btn4)
    await bot.send_message(chat_id, text, reply_markup=markup)


# старт бота
@bot.message_handler(commands=['start'])
async def send_welcome(message):
    """Отправляет приветствие и предлагает выбрать роль."""
    
    # Создаем кнопки для выбора роли
    markup = types.ReplyKeyboardMarkup(row_width=1, resize_keyboard=True)
    btn_employee = types.KeyboardButton("Я сотрудник НКО")
    btn_volunteer = types.KeyboardButton("Я волонтёр")
    markup.add(btn_employee, btn_volunteer)
    
    await bot.send_message(
        message.chat.id,
        "Здравствуйте! Я бот-помощник для НКО.\n\n"
        "Пожалуйста, выберите вашу роль, чтобы я мог предложить подходящие функции.",
        reply_markup=markup
    )


# обработчик для кнопки "Сменить роль"
@bot.message_handler(func=lambda message: message.text == "🔙 Сменить роль")
async def change_role(message):
    """Позволяет пользователю вернуться к выбору роли."""
    await send_welcome(message)

# обработчик выбора роли
@bot.message_handler(func=lambda message: message.text in ["Я сотрудник НКО", "Я волонтёр"])
async def select_role(message):
    if message.text == "Я сотрудник НКО":
        await show_employee_menu(message.chat.id)
    elif message.text == "Я волонтёр":
        await show_volunteer_menu(message.chat.id)


if __name__ == '__main__':
    print("Бот запущен...")
    asyncio.run(bot.polling())