import asyncio
from gigachat_rest_api import gigachat_rest_service
from utils.states import text_editor_data, cancel_user_tasks, active_tasks, text_generation_data, image_generation_data, content_plan_data
from handlers.start import show_employee_menu
from telebot import types


def register_handlers(bot):
    
    @bot.message_handler(func=lambda message: message.text == "✏️ Редактор текста")
    async def start_text_editor(message):
        user_id = message.from_user.id
        
        # Отменяем предыдущие задачи пользователя
        cancel_user_tasks(user_id)
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        markup.add(types.KeyboardButton("🔙 Назад"))
        text_editor_data[user_id] = {'step': 'get_text'}
        
        await bot.send_message(
            message.chat.id,
            "✏️ *Редактор текста*\n\n"
            "Пришлите текст, который нужно проверить и отредактировать.\n\n"
            "Я проверю:\n"
            "• Орфографию и грамматику\n"
            "• Логику изложения\n"
            "• Читаемость текста\n"
            "• Дам советы по улучшению",
            parse_mode="Markdown",
            reply_markup=markup
        )

    @bot.message_handler(func=lambda message: message.text == "🔙 Назад")
    async def back_to_menu(message):
        cancel_user_tasks(message.from_user.id)
        await show_employee_menu(bot, message.chat.id)

    @bot.message_handler(func=lambda message: (
        message.from_user.id in text_editor_data and
        message.from_user.id not in text_generation_data and
        message.from_user.id not in image_generation_data and
        message.from_user.id not in content_plan_data and
        message.text != "🔙 Назад"
    ))
    async def process_text_editor(message):
        user_id = message.from_user.id
        text_to_edit = message.text
        
        status_msg = await bot.send_message(
            message.chat.id,
            "⏳ Проверяю текст через GigaChat AI..."
        )
        
        async def edit_task():
            try:
                prompt = f"""Проверь текст и улучши его:

{text_to_edit}

Выполни:
1. Исправь ошибки
2. Улучши структуру
3. Укажи найденные ошибки
4. Дай советы

Формат:
--- ИСПРАВЛЕННЫЙ ТЕКСТ ---
[текст]

--- ОШИБКИ И ИСПРАВЛЕНИЯ ---
[список]

--- СОВЕТЫ ---
[советы]"""

                loop = asyncio.get_event_loop()
                edited_result = await loop.run_in_executor(
                    None,
                    gigachat_rest_service.chat,
                    prompt,
                    None
                )
                
                await bot.delete_message(message.chat.id, status_msg.message_id)
                
                if len(edited_result) > 4000:
                    parts = [edited_result[i:i+4000] for i in range(0, len(edited_result), 4000)]
                    for i, part in enumerate(parts):
                        await bot.send_message(
                            message.chat.id,
                            f"✏️ *Результат редактирования (часть {i+1}/{len(parts)}):*\n\n{part}",
                            parse_mode="Markdown"
                        )
                else:
                    await bot.send_message(
                        message.chat.id,
                        f"✏️ *Результат редактирования:*\n\n{edited_result}",
                        parse_mode="Markdown"
                    )
            except asyncio.CancelledError:
                # Задача была отменена
                await bot.delete_message(message.chat.id, status_msg.message_id)
                await bot.send_message(
                    message.chat.id,
                    "❌ Редактирование текста отменено (запущена новая команда)."
                )
                raise
            except Exception as e:
                await bot.delete_message(message.chat.id, status_msg.message_id)
                await bot.send_message(
                    message.chat.id,
                    f"❌ Ошибка при редактировании: {str(e)}"
                )
            finally:
                if user_id in text_editor_data:
                    del text_editor_data[user_id]
                if user_id in active_tasks:
                    del active_tasks[user_id]
                await show_employee_menu(bot, message.chat.id, "Что-нибудь ещё?")
        
        # Создаём и сохраняем задачу
        task = asyncio.create_task(edit_task())
        active_tasks[user_id] = task

