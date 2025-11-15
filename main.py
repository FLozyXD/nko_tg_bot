from telebot.async_telebot import AsyncTeleBot
import asyncio
import db
import config
from handlers import start, nko_info, text_generation, image_generation, text_editor, content_plan


if not config.validate_config():
    print("\n⛔ Бот не может быть запущен без корректной конфигурации!")
    print("Пожалуйста, настройте файл config.py и перезапустите бота.\n")
    exit(1)


bot = AsyncTeleBot(config.TOKEN)


def register_all_handlers():
    start.register_handlers(bot)
    nko_info.register_handlers(bot)
    text_generation.register_handlers(bot)
    image_generation.register_handlers(bot)
    text_editor.register_handlers(bot)
    content_plan.register_handlers(bot)


async def main():
    try:
        try:
            await db.init_db()
            print("✅ База данных подключена")
        except Exception as e:
            print(f"⚠️  База данных недоступна: {e}")
            print("⚠️  Бот будет работать без сохранения данных об НКО")
        
        register_all_handlers()
        print("🤖 Бот запущен и готов к работе!")
        await bot.polling()
    finally:
        try:
            await db.close_db()
        except:
            pass


if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Бот остановлен вручную.")
