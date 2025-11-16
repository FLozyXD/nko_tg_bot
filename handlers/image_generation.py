import asyncio
from io import BytesIO
from kandinsky_api import kandinsky_service
from utils.states import image_generation_data, cancel_user_tasks, active_tasks, text_generation_data, text_editor_data, content_plan_data
from handlers.start import show_employee_menu
from telebot import types


def register_handlers(bot):
    
    @bot.message_handler(func=lambda message: message.text == "🎨 Генерация картинки")
    async def start_image_generation(message):
        user_id = message.from_user.id
        
        # Отменяем предыдущие задачи пользователя
        cancel_user_tasks(user_id)
        
        image_generation_data[user_id] = {'step': 'get_description'}
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        markup.add(types.KeyboardButton("🔙 Назад"))

        await bot.send_message(
            message.chat.id,
            "🎨 *Генерация изображения*\n\n"
            "Опишите, какое изображение вы хотите получить.\n\n"
            "Например: _\"Волонтёры помогают пожилым людям, тёплая атмосфера, светлые тона\"_\n\n"
            "⚡ Генерация займёт 30-60 секунд.",
            parse_mode="Markdown",
            reply_markup=markup
        )

    @bot.message_handler(func=lambda message: message.text == "🔙 Назад")
    async def back_to_menu(message):
        await show_employee_menu(bot, message.chat.id)

    @bot.message_handler(func=lambda message: (
        message.from_user.id in image_generation_data and
        message.from_user.id not in text_generation_data and
        message.from_user.id not in text_editor_data and
        message.from_user.id not in content_plan_data and
        message.text != "🔙 Назад"
    ))
    async def process_image_generation(message):
        user_id = message.from_user.id
        description = message.text
        
        status_msg = await bot.send_message(
            message.chat.id,
            "⏳ Генерирую изображение через Kandinsky AI...\n"
            "Это может занять до 1 минуты. Пожалуйста, подождите."
        )
        
        async def generate_task():
            try:
                loop = asyncio.get_event_loop()
                image_data = await loop.run_in_executor(
                    None, 
                    kandinsky_service.generate_image, 
                    description, 
                    1024, 
                    1024
                )
                
                await bot.delete_message(message.chat.id, status_msg.message_id)
                
                photo = BytesIO(image_data)
                photo.name = 'generated_image.jpg'
                
                await bot.send_photo(
                    message.chat.id,
                    photo,
                    caption=f"🎨 *Готово!*\n\n_Промпт: {description}_",
                    parse_mode="Markdown"
                )
                
            except asyncio.CancelledError:
                # Задача была отменена
                await bot.delete_message(message.chat.id, status_msg.message_id)
                await bot.send_message(
                    message.chat.id,
                    "❌ Генерация картинки отменена (запущена новая команда)."
                )
                raise
            except Exception as e:
                await bot.delete_message(message.chat.id, status_msg.message_id)
                await bot.send_message(
                    message.chat.id,
                    f"❌ Ошибка при генерации изображения:\n{str(e)}\n\n"
                    f"Попробуйте изменить описание или повторить позже."
                )
            finally:
                if user_id in image_generation_data:
                    del image_generation_data[user_id]
                if user_id in active_tasks:
                    del active_tasks[user_id]
                await show_employee_menu(bot, message.chat.id, "Что-нибудь ещё?")
        
        # Создаём и сохраняем задачу
        task = asyncio.create_task(generate_task())
        active_tasks[user_id] = task

