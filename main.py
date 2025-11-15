from dotenv import load_dotenv
import os
from telebot.async_telebot import AsyncTeleBot
from telebot import types
import asyncio
import db

load_dotenv()

bot = AsyncTeleBot(str(os.getenv('TOKEN')))

user_data_collector = {} # временное хранилище для сбора данных

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
    if message.from_user.id in user_data_collector:
        del user_data_collector[message.from_user.id]
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

# Шаг 1: Нажатие на кнопку "Информация о вашей НКО"
@bot.message_handler(func=lambda message: message.text == "Информация о вашей НКО")
async def start_nko_info_collection(message):
    user_id = message.from_user.id
    
    existing_data = await db.get_nko_info(user_id)
    if existing_data:
        info_text = (
            f"У меня уже есть информация о вашей организации:\n\n"
            f"**Название:** {existing_data['nko_name']}\n"
            f"**Описание:** {existing_data['nko_description']}\n"
            f"**Аудитория:** {existing_data['nko_audience']}\n"
            f"**Стиль:** {existing_data['nko_style']}\n\n"
            f"Хотите обновить информацию?"
        )
        markup = types.InlineKeyboardMarkup()
        markup.add(
            types.InlineKeyboardButton("Да, обновить", callback_data="update_nko_info"),
            types.InlineKeyboardButton("Нет, назад", callback_data="cancel_nko_update")
        )
        await bot.send_message(message.chat.id, info_text, reply_markup=markup, parse_mode="Markdown")
    else:
        await bot.send_message(message.chat.id, "Похоже, вы здесь впервые. Давайте заполним информацию о вашей НКО.")
        await start_info_steps(message.chat.id, message.from_user.id)

# Обработчик Inline-кнопок "Да/Нет"
@bot.callback_query_handler(func=lambda call: call.data in ["update_nko_info", "cancel_nko_update"])
async def handle_nko_update_callback(call: types.CallbackQuery):
    await bot.answer_callback_query(call.id)
    await bot.delete_message(call.message.chat.id, call.message.message_id)
    if call.data == "update_nko_info":
        await start_info_steps(call.message.chat.id, call.from_user.id)
    else:
        await show_employee_menu(call.message.chat.id, "Хорошо, возвращаю вас в меню.")

# Функция, которая запускает пошаговый опрос
async def start_info_steps(chat_id, user_id):
    # Устанавливаем начальное состояние (шаг) для пользователя
    user_data_collector[user_id] = {'step': 'awaiting_name'}
    await bot.send_message(chat_id, "Шаг 1/4: Введите название вашей НКО:")

# ЕДИНЫЙ ОБРАБОТЧИК для всех шагов сбора информации
@bot.message_handler(func=lambda message: message.from_user.id in user_data_collector)
async def user_info_handler(message):
    user_id = message.from_user.id
    current_step = user_data_collector[user_id].get('step')

    if current_step == 'awaiting_name':
        # Сохраняем имя и переходим к следующему шагу
        user_data_collector[user_id]['name'] = message.text
        user_data_collector[user_id]['step'] = 'awaiting_description'
        await bot.send_message(message.chat.id, "Шаг 2/4: Кратко опишите, чем занимается организация:")

    elif current_step == 'awaiting_description':
        # Сохраняем описание и переходим к следующему шагу
        user_data_collector[user_id]['description'] = message.text
        user_data_collector[user_id]['step'] = 'awaiting_audience'
        await bot.send_message(message.chat.id, "Шаг 3/4: Опишите вашу целевую аудиторию (для кого посты?):")

    elif current_step == 'awaiting_audience':
        # Сохраняем аудиторию и переходим к последнему шагу
        user_data_collector[user_id]['audience'] = message.text
        user_data_collector[user_id]['step'] = 'awaiting_style'
        markup = types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
        markup.add("Разговорный", "Официально-деловой", "Художественный")
        await bot.send_message(message.chat.id, "Шаг 4/4: Выберите основной стиль общения:", reply_markup=markup)

    elif current_step == 'awaiting_style':
        # Сохраняем стиль, записываем всё в БД и выходим из режима сбора
        user_data_collector[user_id]['style'] = message.text
        data = user_data_collector[user_id]
        
        try:
            await db.save_or_update_nko_info(
                user_id=user_id,
                name=data['name'],
                description=data['description'],
                audience=data['audience'],
                style=data['style']
            )
            await bot.send_message(message.chat.id, "✅ Отлично! Информация сохранена в базе данных.")
            
        except Exception as e:
            print(f"Ошибка при сохранении в БД: {e}")
            await bot.send_message(message.chat.id, "❌ Произошла ошибка при сохранении данных. Попробуйте позже.")
            
        finally:
            # Важно: удаляем пользователя из словаря-сборщика, чтобы этот handler на него больше не срабатывал
            del user_data_collector[user_id]
            await show_employee_menu(message.chat.id) # Возвращаем в главное меню


# === ЗАПУСК И ОСТАНОВКА БОТА ===

async def main():
    """Главная функция для запуска и остановки бота и БД."""
    try:
        await db.init_db()
        print("Бот запущен...")
        await bot.polling()
    finally:
        await db.close_db()

if __name__ == '__main__':
    # Используем try-except, чтобы корректно закрыть соединение с БД
    # даже при остановке бота через Ctrl+C
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Бот остановлен вручную.")