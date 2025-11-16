from telebot import types
from utils.keyboards import get_role_selection_keyboard, get_employee_menu_keyboard, get_volunteer_menu_keyboard
from utils.states import cancel_user_tasks


async def show_employee_menu(bot, chat_id, text="Вы в меню для сотрудников. Выберите действие:"):
    markup = get_employee_menu_keyboard()
    await bot.send_message(chat_id, text, reply_markup=markup)


async def show_volunteer_menu(bot, chat_id, text="Вы в меню для волонтеров. Выберите действие:"):
    markup = get_volunteer_menu_keyboard()
    await bot.send_message(chat_id, text, reply_markup=markup)


def register_handlers(bot):
    
    @bot.message_handler(commands=['start'])
    async def send_welcome(message):
        user_id = message.from_user.id
        # Очищаем все состояния при старте
        cancel_user_tasks(user_id)
        
        markup = get_role_selection_keyboard()
        await bot.send_message(
            message.chat.id,
            "Здравствуйте! Я бот-помощник для НКО.\n\n"
            "Пожалуйста, выберите вашу роль, чтобы я мог предложить подходящие функции.",
            reply_markup=markup
        )

    @bot.message_handler(func=lambda message: message.text == "🔙 Сменить роль")
    async def change_role(message):
        user_id = message.from_user.id
        # Очищаем все состояния при смене роли
        cancel_user_tasks(user_id)
        
        markup = get_role_selection_keyboard()
        await bot.send_message(
            message.chat.id,
            "Выберите вашу роль:",
            reply_markup=markup
        )

    @bot.message_handler(func=lambda message: message.text in ["Я сотрудник НКО", "Я волонтёр"])
    async def select_role(message):
        user_id = message.from_user.id
        # Очищаем все состояния при выборе роли
        cancel_user_tasks(user_id)
        
        if message.text == "Я сотрудник НКО":
            await show_employee_menu(bot, message.chat.id)
        elif message.text == "Я волонтёр":
            await show_volunteer_menu(bot, message.chat.id)

    @bot.callback_query_handler(func=lambda call: call.data == "back_to_menu")
    async def back_to_menu_handler(call: types.CallbackQuery):
        await bot.answer_callback_query(call.id)
        await bot.delete_message(call.message.chat.id, call.message.message_id)
        await show_employee_menu(bot, call.message.chat.id)

