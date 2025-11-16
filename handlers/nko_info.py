from telebot import types
import db
from utils.states import user_data_collector, cancel_user_tasks
from utils.keyboards import get_nko_update_inline_keyboard, get_style_keyboard
from handlers.start import show_employee_menu


async def start_info_steps(bot, chat_id, user_id):
    # Отменяем предыдущие задачи пользователя
    cancel_user_tasks(user_id)
    
    user_data_collector[user_id] = {'step': 'awaiting_name'}
    await bot.send_message(chat_id, "Шаг 1/4: Введите название вашей НКО:")


def register_handlers(bot):
    
    @bot.message_handler(func=lambda message: message.text == "ℹ️ Информация о НКО")
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
            markup = get_nko_update_inline_keyboard()
            await bot.send_message(message.chat.id, info_text, reply_markup=markup, parse_mode="Markdown")
        else:
            await bot.send_message(message.chat.id, "Похоже, вы здесь впервые. Давайте заполним информацию о вашей НКО.")
            await start_info_steps(bot, message.chat.id, message.from_user.id)

    @bot.callback_query_handler(func=lambda call: call.data in ["update_nko_info", "cancel_nko_update"])
    async def handle_nko_update_callback(call: types.CallbackQuery):
        await bot.answer_callback_query(call.id)
        await bot.delete_message(call.message.chat.id, call.message.message_id)
        if call.data == "update_nko_info":
            await start_info_steps(bot, call.message.chat.id, call.from_user.id)
        else:
            await show_employee_menu(bot, call.message.chat.id, "Хорошо, возвращаю вас в меню.")

    @bot.message_handler(func=lambda message: message.from_user.id in user_data_collector)
    async def user_info_handler(message):
        user_id = message.from_user.id
        current_step = user_data_collector[user_id].get('step')

        if current_step == 'awaiting_name':
            user_data_collector[user_id]['name'] = message.text
            user_data_collector[user_id]['step'] = 'awaiting_description'
            await bot.send_message(message.chat.id, "Шаг 2/4: Кратко опишите, чем занимается организация:")

        elif current_step == 'awaiting_description':
            user_data_collector[user_id]['description'] = message.text
            user_data_collector[user_id]['step'] = 'awaiting_audience'
            await bot.send_message(message.chat.id, "Шаг 3/4: Опишите вашу целевую аудиторию (для кого посты?):")

        elif current_step == 'awaiting_audience':
            user_data_collector[user_id]['audience'] = message.text
            user_data_collector[user_id]['step'] = 'awaiting_style'
            markup = get_style_keyboard()
            await bot.send_message(message.chat.id, "Шаг 4/4: Выберите основной стиль общения:", reply_markup=markup)

        elif current_step == 'awaiting_style':
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
                del user_data_collector[user_id]
                await show_employee_menu(bot, message.chat.id)

