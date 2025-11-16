from telebot import types
import asyncio
import db
from gigachat_rest_api import gigachat_rest_service
from utils.states import text_generation_data, cancel_user_tasks, active_tasks, image_generation_data, text_editor_data, content_plan_data
from utils.keyboards import get_text_generation_modes_keyboard
from handlers.start import show_employee_menu


def build_system_prompt(nko_info):
    if not nko_info:
        return """Ты - профессиональный SMM-специалист для НКО. Создавай грамотные, вовлекающие посты для социальных сетей. Обязательно добавляй релевантные хештеги."""
    
    name = nko_info.get('nko_name', 'НКО')
    description = nko_info.get('nko_description', '')
    style = nko_info.get('nko_style', 'разговорный')
    audience = nko_info.get('nko_audience', 'широкая аудитория')
    
    return f"""Ты - SMM-специалист организации "{name}". {description}
Стиль: {style}. Аудитория: {audience}.
Создавай вовлекающие посты с хештегами."""


def generate_simple_post(idea, nko_info=None):
    name = nko_info.get('nko_name', 'Мы') if nko_info else 'Мы'
    
    idea_lower = idea.lower()
    
    if 'акция' in idea_lower and 'сбор' in idea_lower:
        if 'вещи' in idea_lower or 'одежд' in idea_lower:
            post = f"🤝 *Акция по сбору вещей*\n\n"
            post += f"Друзья! {name} организуем акцию по сбору вещей для тех, кто в них нуждается.\n\n"
            
            if 'выходн' in idea_lower or 'субботу' in idea_lower or 'воскресенье' in idea_lower:
                post += f"📅 *Когда:* В эти выходные\n"
            
            post += f"📦 *Что можно принести:*\n"
            post += f"• Тёплую одежду\n"
            post += f"• Обувь\n"
            post += f"• Средства гигиены\n\n"
            post += f"💙 Ваша помощь важна! Каждая вещь согреет того, кто в ней нуждается.\n\n"
            post += f"#ПомощьБездомным #Акция #Благотворительность #Доброе_дело"
        else:
            post = f"📢 {name}\n\n{idea}\n\n#НКО #Акция #ПомощьЛюдям"
    elif 'мероприятие' in idea_lower or 'событие' in idea_lower:
        post = f"🎉 *Приглашаем на мероприятие!*\n\n{idea}\n\n"
        post += f"Будем рады видеть вас! 💫\n\n#НКО #Событие #Приглашаем"
    elif 'помощь' in idea_lower or 'поддержк' in idea_lower:
        post = f"🙏 *Нужна ваша помощь*\n\n{idea}\n\n"
        post += f"Вместе мы можем больше! 💪\n\n#НКО #Помощь #Поддержка #Вместе"
    else:
        post = f"📢 *{name}*\n\n{idea}\n\n"
        post += f"Давайте делать этот мир лучше вместе! ✨\n\n"
        post += f"#НКО #Социальнаяпомощь #ДелаемДобро"
    
    return post


def generate_event_post(event_data, nko_info=None):
    name = nko_info.get('nko_name', 'Наша организация') if nko_info else 'Наша организация'
    
    post = f"📅 {event_data.get('event_name', 'Событие')}\n\n"
    post += f"🕒 Дата: {event_data.get('date', 'Не указана')}\n"
    post += f"📍 Место: {event_data.get('place', 'Не указано')}\n"
    post += f"👥 Для кого: {event_data.get('participants', 'Все желающие')}\n"
    
    if event_data.get('details'):
        post += f"\nℹ️ {event_data['details']}\n"
    
    post += f"\n✨ {name} приглашает вас!\n\n"
    post += "#НКО #Событие #Приглашение"
    
    return post


def register_handlers(bot):
    
    @bot.message_handler(func=lambda message: message.text == "📝 Генерация текста")
    async def start_text_generation(message):
        user_id = message.from_user.id
        
        # Отменяем предыдущие задачи пользователя
        cancel_user_tasks(user_id)
        
        markup = get_text_generation_modes_keyboard()
        await bot.send_message(
            message.chat.id,
            "📝 *Генерация текста для поста*\n\n"
            "Выберите режим генерации:\n\n"
            "• *Свободный текст* - вы вводите идею, я превращаю её в готовый пост\n"
            "• *Структурированная форма* - я задам вопросы о событии (дата, место и т.д.)\n"
            "• *На основе примеров* - вы даёте примеры постов, я создам новый в том же стиле",
            parse_mode="Markdown",
            reply_markup=markup
        )

    @bot.callback_query_handler(func=lambda call: call.data.startswith("text_gen_"))
    async def handle_text_generation_mode(call: types.CallbackQuery):
        await bot.answer_callback_query(call.id)
        await bot.delete_message(call.message.chat.id, call.message.message_id)
        
        user_id = call.from_user.id
        
        if call.data == "text_gen_free":
            text_generation_data[user_id] = {'mode': 'free'}
            await bot.send_message(
                call.message.chat.id,
                "✍️ Отлично! Опишите вашу идею для поста в свободной форме.\n\n"
                "Например: _\"Хотим рассказать про акцию сбора вещей для бездомных, которая пройдёт в эти выходные\"_",
                parse_mode="Markdown"
            )
        
        elif call.data == "text_gen_structured":
            text_generation_data[user_id] = {'mode': 'structured', 'step': 'event_name'}
            await bot.send_message(
                call.message.chat.id,
                "📋 Отлично! Давайте заполним информацию о событии.\n\n"
                "*Шаг 1/5:* Как называется событие?",
                parse_mode="Markdown"
            )
        
        elif call.data == "text_gen_examples":
            text_generation_data[user_id] = {'mode': 'examples', 'step': 'get_examples'}
            await bot.send_message(
                call.message.chat.id,
                "📚 Отлично! Пришлите мне 1-3 примера ваших готовых постов.\n\n"
                "Можете прислать их одним сообщением или несколькими подряд. "
                "Когда закончите, напишите *ГОТОВО*.",
                parse_mode="Markdown"
            )

    @bot.message_handler(func=lambda message: (
        message.from_user.id in text_generation_data and
        message.from_user.id not in image_generation_data and
        message.from_user.id not in text_editor_data and
        message.from_user.id not in content_plan_data
    ))
    async def process_text_generation(message):
        user_id = message.from_user.id
        data = text_generation_data[user_id]
        mode = data.get('mode')
        
        if mode == 'free':
            idea = message.text
            nko_info = await db.get_nko_info(user_id)
            
            status_msg = await bot.send_message(message.chat.id, "⏳ Генерирую пост через GigaChat AI...")
            
            async def generate_task():
                try:
                    system_prompt = build_system_prompt(nko_info)
                    prompt = f"""Перепиши следующую идею в готовый пост для социальных сетей НКО:

{idea}

Требования:
- Без орфографических и грамматических ошибок
- Добавь 2-3 релевантных хештега
- Структурируй текст для читаемости
- Сделай вовлекающим с призывом к действию
- Длина: 200-400 символов"""

                    loop = asyncio.get_event_loop()
                    post = await loop.run_in_executor(
                        None,
                        gigachat_rest_service.chat,
                        prompt,
                        system_prompt
                    )
                    
                    await bot.delete_message(message.chat.id, status_msg.message_id)
                    await bot.send_message(
                        message.chat.id,
                        f"✅ *Готовый пост:*\n\n{post}",
                        parse_mode="Markdown"
                    )
                except asyncio.CancelledError:
                    # Задача была отменена
                    await bot.delete_message(message.chat.id, status_msg.message_id)
                    await bot.send_message(
                        message.chat.id,
                        "❌ Генерация текста отменена (запущена новая команда)."
                    )
                    raise
                except Exception as e:
                    await bot.delete_message(message.chat.id, status_msg.message_id)
                    await bot.send_message(
                        message.chat.id,
                        f"❌ Ошибка при генерации: {str(e)}"
                    )
                finally:
                    if user_id in text_generation_data:
                        del text_generation_data[user_id]
                    if user_id in active_tasks:
                        del active_tasks[user_id]
                    await show_employee_menu(bot, message.chat.id, "Что-нибудь ещё?")
            
            # Создаём и сохраняем задачу
            task = asyncio.create_task(generate_task())
            active_tasks[user_id] = task
        
        elif mode == 'structured':
            step = data.get('step')
            
            if step == 'event_name':
                data['event_name'] = message.text
                data['step'] = 'date'
                await bot.send_message(message.chat.id, "*Шаг 2/5:* Когда состоится событие? (дата и время)", parse_mode="Markdown")
            
            elif step == 'date':
                data['date'] = message.text
                data['step'] = 'place'
                await bot.send_message(message.chat.id, "*Шаг 3/5:* Где пройдёт событие? (место/адрес)", parse_mode="Markdown")
            
            elif step == 'place':
                data['place'] = message.text
                data['step'] = 'participants'
                await bot.send_message(message.chat.id, "*Шаг 4/5:* Кто приглашён? (целевая аудитория)", parse_mode="Markdown")
            
            elif step == 'participants':
                data['participants'] = message.text
                data['step'] = 'details'
                await bot.send_message(
                    message.chat.id,
                    "*Шаг 5/5:* Дополнительные детали (необязательно, можно пропустить, написав \"пропустить\")",
                    parse_mode="Markdown"
                )
            
            elif step == 'details':
                data['details'] = message.text if message.text.lower() != 'пропустить' else ''
                
                nko_info = await db.get_nko_info(user_id)
                status_msg = await bot.send_message(message.chat.id, "⏳ Создаю пост через GigaChat AI...")
                
                async def generate_task():
                    try:
                        event_data = {
                            'event_name': data.get('event_name'),
                            'date': data.get('date'),
                            'place': data.get('place'),
                            'participants': data.get('participants'),
                            'details': data.get('details', '')
                        }
                        
                        system_prompt = build_system_prompt(nko_info)
                        prompt = f"""Создай пост для соцсетей о событии:

Название: {event_data.get('event_name')}
Дата: {event_data.get('date')}
Место: {event_data.get('place')}
Для кого: {event_data.get('participants')}
Детали: {event_data.get('details')}

Требования:
- Четкая структура
- Без ошибок
- 2-3 хештега
- Вовлекающий текст
- 250-500 символов"""

                        loop = asyncio.get_event_loop()
                        post = await loop.run_in_executor(
                            None,
                            gigachat_rest_service.chat,
                            prompt,
                            system_prompt
                        )
                        
                        await bot.delete_message(message.chat.id, status_msg.message_id)
                        await bot.send_message(
                            message.chat.id,
                            f"✅ *Готовый пост:*\n\n{post}",
                            parse_mode="Markdown"
                        )
                    except asyncio.CancelledError:
                        # Задача была отменена
                        await bot.delete_message(message.chat.id, status_msg.message_id)
                        await bot.send_message(
                            message.chat.id,
                            "❌ Генерация текста отменена (запущена новая команда)."
                        )
                        raise
                    except Exception as e:
                        await bot.delete_message(message.chat.id, status_msg.message_id)
                        await bot.send_message(
                            message.chat.id,
                            f"❌ Ошибка при генерации: {str(e)}"
                        )
                    finally:
                        if user_id in text_generation_data:
                            del text_generation_data[user_id]
                        if user_id in active_tasks:
                            del active_tasks[user_id]
                        await show_employee_menu(bot, message.chat.id, "Что-нибудь ещё?")
                
                # Создаём и сохраняем задачу
                task = asyncio.create_task(generate_task())
                active_tasks[user_id] = task
        
        elif mode == 'examples':
            if message.text.upper() == 'ГОТОВО':
                examples = data.get('examples', '')
                
                if not examples:
                    await bot.send_message(message.chat.id, "❌ Вы не прислали ни одного примера. Попробуйте ещё раз.")
                    del text_generation_data[user_id]
                    await show_employee_menu(bot, message.chat.id)
                    return
                
                data['step'] = 'get_topic'
                await bot.send_message(
                    message.chat.id,
                    "Отлично! Теперь укажите тему для нового поста.\n\n"
                    "Например: _\"Новая программа помощи семьям\"_",
                    parse_mode="Markdown"
                )
            
            elif data.get('step') == 'get_examples':
                if 'examples' not in data:
                    data['examples'] = ''
                data['examples'] += message.text + '\n\n---\n\n'
                await bot.send_message(
                    message.chat.id,
                    "✅ Пример принят! Можете прислать ещё или написать *ГОТОВО*.",
                    parse_mode="Markdown"
                )
            
            elif data.get('step') == 'get_topic':
                new_topic = message.text
                examples = data.get('examples', '')
                nko_info = await db.get_nko_info(user_id)
                
                status_msg = await bot.send_message(message.chat.id, "⏳ Создаю пост через GigaChat AI...")
                
                async def generate_task():
                    try:
                        system_prompt = build_system_prompt(nko_info)
                        prompt = f"""Проанализируй стиль этих постов:

{examples}

Создай новый пост на тему: {new_topic}

Используй тот же стиль, добавь хештеги."""

                        loop = asyncio.get_event_loop()
                        post = await loop.run_in_executor(
                            None,
                            gigachat_rest_service.chat,
                            prompt,
                            system_prompt
                        )
                        
                        await bot.delete_message(message.chat.id, status_msg.message_id)
                        await bot.send_message(
                            message.chat.id,
                            f"✅ *Готовый пост:*\n\n{post}",
                            parse_mode="Markdown"
                        )
                    except asyncio.CancelledError:
                        # Задача была отменена
                        await bot.delete_message(message.chat.id, status_msg.message_id)
                        await bot.send_message(
                            message.chat.id,
                            "❌ Генерация текста отменена (запущена новая команда)."
                        )
                        raise
                    except Exception as e:
                        await bot.delete_message(message.chat.id, status_msg.message_id)
                        await bot.send_message(
                            message.chat.id,
                            f"❌ Ошибка при генерации: {str(e)}"
                        )
                    finally:
                        if user_id in text_generation_data:
                            del text_generation_data[user_id]
                        if user_id in active_tasks:
                            del active_tasks[user_id]
                        await show_employee_menu(bot, message.chat.id, "Что-нибудь ещё?")
                
                # Создаём и сохраняем задачу
                task = asyncio.create_task(generate_task())
                active_tasks[user_id] = task

