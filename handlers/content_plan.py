from telebot import types
from datetime import datetime, timedelta
import asyncio
import db
from gigachat_rest_api import gigachat_rest_service
from utils.states import content_plan_data
from utils.keyboards import get_content_plan_period_keyboard, get_content_plan_frequency_keyboard
from handlers.start import show_employee_menu


def build_system_prompt_cp(nko_info):
    if not nko_info:
        return "Ты - SMM-специалист для НКО. Создавай качественный контент-план."
    
    name = nko_info.get('nko_name', 'НКО')
    description = nko_info.get('nko_description', '')
    
    return f"""Ты - SMM-специалист организации "{name}". {description}
Создавай эффективный контент-план."""


def generate_content_plan_simple(period, frequency):
    plan = []
    today = datetime.now()
    
    days = 7 if period == "неделю" else 30
    
    freq_map = {
        "1 раз в неделю": 7,
        "2 раза в неделю": 3,
        "3 раза в неделю": 2,
        "2-3 раза в неделю": 3,
        "ежедневно": 1
    }
    
    interval = freq_map.get(frequency, 3)
    
    post_types = [
        ("📢 Анонс", "Предстоящее событие"),
        ("📰 Новости", "Новости организации"),
        ("✅ Отчёт", "Результаты работы"),
        ("🙏 Призыв", "Призыв к действию"),
        ("💬 История", "История благополучателя"),
        ("🎯 Цели", "Наши цели и задачи")
    ]
    
    result = "КОНТЕНТ-ПЛАН\n\n"
    idx = 0
    
    for i in range(0, days, interval):
        date = today + timedelta(days=i)
        post_type = post_types[idx % len(post_types)]
        result += f"📅 {date.strftime('%d.%m.%Y')} | {post_type[0]} | {post_type[1]}\n"
        idx += 1
    
    return result


FREQUENCY_MAP = {
    "cp_freq_1pw": "1 раз в неделю",
    "cp_freq_2pw": "2 раза в неделю",
    "cp_freq_3pw": "3 раза в неделю",
    "cp_freq_2-3pw": "2-3 раза в неделю",
    "cp_freq_daily": "ежедневно"
}


def register_handlers(bot):
    
    @bot.message_handler(func=lambda message: message.text == "📅 Контент-план")
    async def start_content_plan(message):
        user_id = message.from_user.id
        content_plan_data[user_id] = {'step': 'get_period'}
        
        markup = get_content_plan_period_keyboard()
        await bot.send_message(
            message.chat.id,
            "📅 *Создание контент-плана*\n\n"
            "На какой период создать контент-план?",
            parse_mode="Markdown",
            reply_markup=markup
        )

    @bot.callback_query_handler(func=lambda call: call.data.startswith("cp_period_"))
    async def handle_content_plan_period(call: types.CallbackQuery):
        await bot.answer_callback_query(call.id)
        await bot.delete_message(call.message.chat.id, call.message.message_id)
        
        user_id = call.from_user.id
        period = "неделю" if call.data == "cp_period_week" else "месяц"
        
        content_plan_data[user_id] = {'period': period, 'step': 'get_frequency'}
        
        markup = get_content_plan_frequency_keyboard(period)
        await bot.send_message(
            call.message.chat.id,
            f"📅 Контент-план на *{period}*\n\nКак часто планируете публиковать посты?",
            parse_mode="Markdown",
            reply_markup=markup
        )

    @bot.callback_query_handler(func=lambda call: call.data.startswith("cp_freq_"))
    async def handle_content_plan_frequency(call: types.CallbackQuery):
        await bot.answer_callback_query(call.id)
        await bot.delete_message(call.message.chat.id, call.message.message_id)
        
        user_id = call.from_user.id
        frequency = FREQUENCY_MAP.get(call.data, "2 раза в неделю")
        period = content_plan_data[user_id].get('period', 'неделю')
        
        nko_info = await db.get_nko_info(user_id)
        
        await bot.send_message(
            call.message.chat.id,
            "⏳ Генерирую контент-план через GigaChat AI..."
        )
        
        try:
            system_prompt = build_system_prompt_cp(nko_info)
            prompt = f"""Создай контент-план для Telegram-канала НКО на {period}.
Частота: {frequency}

Требования:
1. Конкретные даты
2. Категория/тип поста
3. Разнообразие (анонсы, новости, отчёты, истории)
4. Интересно для аудитории

Формат:
ДАТА | ТИП | ОПИСАНИЕ"""

            loop = asyncio.get_event_loop()
            content_plan = await loop.run_in_executor(
                None,
                gigachat_rest_service.chat,
                prompt,
                system_prompt
            )
            
            await bot.send_message(
                call.message.chat.id,
                f"📅 *Ваш контент-план*\n\n{content_plan}",
                parse_mode="Markdown"
            )
        except Exception as e:
            await bot.send_message(
                call.message.chat.id,
                f"❌ Произошла ошибка при генерации контент-плана: {str(e)}"
            )
        finally:
            if user_id in content_plan_data:
                del content_plan_data[user_id]
            await show_employee_menu(bot, call.message.chat.id, "Что-нибудь ещё?")

