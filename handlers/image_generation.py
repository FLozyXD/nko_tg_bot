import asyncio
from io import BytesIO
from kandinsky_api import kandinsky_service
from utils.states import image_generation_data
from handlers.start import show_employee_menu


def register_handlers(bot):
    
    @bot.message_handler(func=lambda message: message.text == "🎨 Генерация картинки")
    async def start_image_generation(message):
        user_id = message.from_user.id
        image_generation_data[user_id] = {'step': 'get_description'}
        
        await bot.send_message(
            message.chat.id,
            "🎨 *Генерация изображения*\n\n"
            "Опишите, какое изображение вы хотите получить.\n\n"
            "Например: _\"Волонтёры помогают пожилым людям, тёплая атмосфера, светлые тона\"_\n\n"
            "⚡ Генерация займёт 30-60 секунд.",
            parse_mode="Markdown"
        )

    @bot.message_handler(func=lambda message: message.from_user.id in image_generation_data)
    async def process_image_generation(message):
        user_id = message.from_user.id
        description = message.text
        
        status_msg = await bot.send_message(
            message.chat.id,
            "⏳ Генерирую изображение через Kandinsky AI...\n"
            "Это может занять до 1 минуты. Пожалуйста, подождите."
        )
        
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
            
        except Exception as e:
            await bot.delete_message(message.chat.id, status_msg.message_id)
            await bot.send_message(
                message.chat.id,
                f"❌ Ошибка при генерации изображения:\n{str(e)}\n\n"
                f"Попробуйте изменить описание или повторить позже."
            )
        finally:
            del image_generation_data[user_id]
            await show_employee_menu(bot, message.chat.id, "Что-нибудь ещё?")

