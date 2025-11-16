from telebot import types
import db
import json
from datetime import datetime
from handlers.start import show_volunteer_menu
from utils.states import cancel_user_tasks

# Словарь для хранения состояния прохождения тестов
test_sessions = {}


def register_handlers(bot):
    
    # ============= Информация по мероприятиям =============
    
    @bot.message_handler(func=lambda message: message.text == "Информация по мероприятию")
    async def event_info(message):
        """Информация о мероприятиях волонтёра"""
        user_id = message.from_user.id
        cancel_user_tasks(user_id)
        
        events = await db.get_user_events(user_id)
        
        if not events:
            await bot.send_message(
                message.chat.id,
                "📋 *Ваши мероприятия*\n\n"
                "Вы пока не зарегистрированы ни на одно мероприятие.\n\n"
                "Используйте кнопку *'Выбор мероприятия'*, чтобы найти и зарегистрироваться на предстоящие события!",
                parse_mode="Markdown"
            )
            await show_volunteer_menu(bot, message.chat.id)
            return
        
        response = "📋 *Ваши мероприятия:*\n\n"
        
        for event in events:
            event_date = event['event_date']
            # В SQLite дата хранится как строка
            if event_date:
                try:
                    dt = datetime.fromisoformat(event_date)
                    date_str = dt.strftime("%d.%m.%Y %H:%M")
                except:
                    date_str = event_date
            else:
                date_str = "Не указана"
            status_emoji = "🟢" if event['status'] == 'upcoming' else "🔴"
            
            response += f"{status_emoji} *{event['title']}*\n"
            response += f"📅 Дата: {date_str}\n"
            response += f"📍 Место: {event['location']}\n"
            
            if event['description']:
                response += f"📝 {event['description']}\n"
            
            response += f"✅ Статус: {event['registration_status']}\n"
            response += "\n" + "─" * 30 + "\n\n"
        
        await bot.send_message(
            message.chat.id,
            response,
            parse_mode="Markdown"
        )
        await show_volunteer_menu(bot, message.chat.id)
    
    # ============= Выбор мероприятий =============
    
    @bot.message_handler(func=lambda message: message.text == "Выбор мероприятия (будущие)")
    async def select_future_event(message):
        """Показать предстоящие мероприятия"""
        user_id = message.from_user.id
        cancel_user_tasks(user_id)
        
        events = await db.get_upcoming_events()
        
        if not events:
            await bot.send_message(
                message.chat.id,
                "🗓 *Предстоящие мероприятия*\n\n"
                "К сожалению, сейчас нет запланированных мероприятий.\n"
                "Проверьте позже!",
                parse_mode="Markdown"
            )
            await show_volunteer_menu(bot, message.chat.id)
            return
        
        markup = types.InlineKeyboardMarkup()
        
        for event in events:
            available_spots = event['max_volunteers'] - event['registered_count'] if event['max_volunteers'] else "∞"
            button_text = f"📅 {event['title']} (мест: {available_spots})"
            markup.add(types.InlineKeyboardButton(
                button_text,
                callback_data=f"event_details_{event['event_id']}"
            ))
        
        markup.add(types.InlineKeyboardButton("🔙 Назад в меню", callback_data="back_to_volunteer_menu"))
        
        await bot.send_message(
            message.chat.id,
            "🗓 *Выберите мероприятие для подробной информации:*",
            parse_mode="Markdown",
            reply_markup=markup
        )
    
    @bot.callback_query_handler(func=lambda call: call.data.startswith("event_details_"))
    async def show_event_details(call: types.CallbackQuery):
        """Показать детали мероприятия"""
        try:
            # Сразу отвечаем на callback чтобы убрать "часики"
            await bot.answer_callback_query(call.id, "Загружаю информацию...")
            
            event_id = int(call.data.split("_")[2])
            events = await db.get_upcoming_events()
            event = next((e for e in events if e['event_id'] == event_id), None)
            
            if not event:
                await bot.send_message(call.message.chat.id, "❌ Мероприятие не найдено")
                return
            
            event_date = event['event_date']
            # В SQLite дата хранится как строка
            if event_date:
                try:
                    dt = datetime.fromisoformat(event_date)
                    date_str = dt.strftime("%d.%m.%Y %H:%M")
                except:
                    date_str = event_date
            else:
                date_str = "Не указана"
            
            available_spots = event['max_volunteers'] - event['registered_count'] if event['max_volunteers'] else "∞"
            
            # Формируем текст БЕЗ Markdown, чтобы избежать проблем с кавычками
            details = f"📅 {event['title']}\n\n"
            details += f"📝 {event['description']}\n\n"
            details += f"🕐 Дата: {date_str}\n"
            details += f"📍 Место: {event['location']}\n"
            details += f"👥 Свободных мест: {available_spots}\n"
            
            if event.get('required_competences'):
                # В SQLite это строка JSON
                try:
                    if isinstance(event['required_competences'], str):
                        competences = json.loads(event['required_competences'])
                    else:
                        competences = event['required_competences']
                    competences_str = ", ".join(competences)
                    details += f"🎯 Требуемые навыки: {competences_str}\n"
                except:
                    pass
            
            markup = types.InlineKeyboardMarkup()
            markup.add(types.InlineKeyboardButton(
                "✅ Записаться",
                callback_data=f"register_event_{event_id}"
            ))
            markup.add(types.InlineKeyboardButton(
                "🔙 Назад к списку",
                callback_data="back_to_events_list"
            ))
            
            await bot.edit_message_text(
                details,
                call.message.chat.id,
                call.message.message_id,
                reply_markup=markup
            )
        except Exception as e:
            print(f"Ошибка при показе деталей мероприятия: {e}")
            await bot.answer_callback_query(call.id, f"❌ Ошибка: {str(e)}", show_alert=True)
    
    @bot.callback_query_handler(func=lambda call: call.data.startswith("register_event_"))
    async def register_on_event(call: types.CallbackQuery):
        """Регистрация на мероприятие"""
        await bot.answer_callback_query(call.id)
        
        user_id = call.from_user.id
        event_id = int(call.data.split("_")[2])
        
        success, message = await db.register_for_event(user_id, event_id)
        
        if success:
            await bot.answer_callback_query(call.id, "✅ " + message, show_alert=True)
            # Возвращаемся к списку
            await bot.delete_message(call.message.chat.id, call.message.message_id)
            await show_volunteer_menu(bot, call.message.chat.id, "Вы успешно записались на мероприятие!")
        else:
            await bot.answer_callback_query(call.id, "❌ " + message, show_alert=True)
    
    @bot.callback_query_handler(func=lambda call: call.data == "back_to_events_list")
    async def back_to_events(call: types.CallbackQuery):
        """Вернуться к списку мероприятий"""
        await bot.answer_callback_query(call.id)
        await bot.delete_message(call.message.chat.id, call.message.message_id)
        
        # Создаем сообщение как будто нажали кнопку
        class FakeMessage:
            def __init__(self, chat_id, user_id):
                self.chat = types.Chat(chat_id, 'private')
                self.chat.id = chat_id
                self.from_user = types.User(user_id, False, 'User')
                self.text = "Выбор мероприятия (будущие)"
        
        fake_msg = FakeMessage(call.message.chat.id, call.from_user.id)
        await select_future_event(fake_msg)
    
    @bot.callback_query_handler(func=lambda call: call.data == "back_to_volunteer_menu")
    async def back_to_menu(call: types.CallbackQuery):
        """Вернуться в меню волонтёра"""
        await bot.answer_callback_query(call.id)
        await bot.delete_message(call.message.chat.id, call.message.message_id)
        await show_volunteer_menu(bot, call.message.chat.id)
    
    # ============= Тестирование =============
    
    @bot.message_handler(func=lambda message: message.text == "Тест для подтверждения компетенций")
    async def competence_test(message):
        """Показать список доступных тестов"""
        user_id = message.from_user.id
        cancel_user_tasks(user_id)
        
        tests = await db.get_all_tests()
        
        if not tests:
            await bot.send_message(
                message.chat.id,
                "📝 *Тесты для подтверждения компетенций*\n\n"
                "К сожалению, тесты пока не доступны.\n"
                "Проверьте позже!",
                parse_mode="Markdown"
            )
            await show_volunteer_menu(bot, message.chat.id)
            return
        
        # Получаем результаты пользователя
        user_results = await db.get_user_test_results(user_id)
        passed_tests = {r['test_id']: r for r in user_results if r['passed']}
        
        markup = types.InlineKeyboardMarkup()
        
        response = "📝 *Доступные тесты:*\n\n"
        
        for test in tests:
            if test['test_id'] in passed_tests:
                status = "✅ Пройден"
                score = passed_tests[test['test_id']]['score']
                response += f"✅ *{test['title']}* - результат: {score}%\n"
                button_text = f"📝 {test['title']} (пройден)"
            else:
                status = "❌ Не пройден"
                response += f"📝 *{test['title']}*\n"
                button_text = f"📝 {test['title']}"
            
            response += f"   _{test['description']}_\n\n"
            
            markup.add(types.InlineKeyboardButton(
                button_text,
                callback_data=f"start_test_{test['test_id']}"
            ))
        
        markup.add(types.InlineKeyboardButton("🔙 Назад в меню", callback_data="back_to_volunteer_menu"))
        
        await bot.send_message(
            message.chat.id,
            response,
            parse_mode="Markdown",
            reply_markup=markup
        )
    
    @bot.callback_query_handler(func=lambda call: call.data.startswith("start_test_"))
    async def start_test(call: types.CallbackQuery):
        """Начать прохождение теста"""
        await bot.answer_callback_query(call.id)
        
        user_id = call.from_user.id
        test_id = int(call.data.split("_")[2])
        
        test = await db.get_test_by_id(test_id)
        if not test:
            await bot.send_message(call.message.chat.id, "❌ Тест не найден")
            return
        
        # Инициализируем сессию теста
        test_sessions[user_id] = {
            'test_id': test_id,
            'questions': test['questions'],
            'current_question': 0,
            'correct_answers': 0,
            'passing_score': test['passing_score']
        }
        
        await bot.delete_message(call.message.chat.id, call.message.message_id)
        await send_question(bot, user_id, call.message.chat.id)
    
    async def send_question(bot, user_id, chat_id):
        """Отправить текущий вопрос теста"""
        session = test_sessions.get(user_id)
        if not session:
            return
        
        current_q = session['current_question']
        questions = session['questions']
        
        if current_q >= len(questions):
            # Тест завершён
            await finish_test(bot, user_id, chat_id)
            return
        
        question = questions[current_q]
        
        markup = types.InlineKeyboardMarkup()
        for i, option in enumerate(question['options']):
            markup.add(types.InlineKeyboardButton(
                option,
                callback_data=f"answer_{i}"
            ))
        
        await bot.send_message(
            chat_id,
            f"❓ *Вопрос {current_q + 1} из {len(questions)}:*\n\n"
            f"{question['question']}",
            parse_mode="Markdown",
            reply_markup=markup
        )
    
    @bot.callback_query_handler(func=lambda call: call.data.startswith("answer_"))
    async def process_answer(call: types.CallbackQuery):
        """Обработать ответ на вопрос теста"""
        await bot.answer_callback_query(call.id)
        
        user_id = call.from_user.id
        session = test_sessions.get(user_id)
        
        if not session:
            await bot.send_message(call.message.chat.id, "❌ Сессия теста не найдена")
            return
        
        answer_idx = int(call.data.split("_")[1])
        current_q = session['current_question']
        question = session['questions'][current_q]
        
        # Проверяем ответ
        is_correct = answer_idx == question['correct']
        if is_correct:
            session['correct_answers'] += 1
            await bot.answer_callback_query(call.id, "✅ Правильно!", show_alert=False)
        else:
            correct_option = question['options'][question['correct']]
            await bot.answer_callback_query(
                call.id, 
                f"❌ Неправильно. Правильный ответ: {correct_option}", 
                show_alert=True
            )
        
        # Переходим к следующему вопросу
        session['current_question'] += 1
        
        await bot.delete_message(call.message.chat.id, call.message.message_id)
        await send_question(bot, user_id, call.message.chat.id)
    
    async def finish_test(bot, user_id, chat_id):
        """Завершить тест и показать результаты"""
        session = test_sessions.get(user_id)
        if not session:
            return
        
        total_questions = len(session['questions'])
        correct = session['correct_answers']
        score = int((correct / total_questions) * 100)
        passed = score >= session['passing_score']
        
        # Сохраняем результат
        await db.save_test_result(user_id, session['test_id'], score, passed)
        
        if passed:
            result_text = (
                f"🎉 *Поздравляем!*\n\n"
                f"Вы успешно прошли тест!\n\n"
                f"✅ Правильных ответов: {correct} из {total_questions}\n"
                f"📊 Результат: *{score}%*\n"
                f"🎯 Проходной балл: {session['passing_score']}%\n\n"
                f"Компетенция подтверждена! ✨"
            )
        else:
            result_text = (
                f"📝 *Тест завершён*\n\n"
                f"К сожалению, тест не пройден.\n\n"
                f"❌ Правильных ответов: {correct} из {total_questions}\n"
                f"📊 Результат: *{score}%*\n"
                f"🎯 Проходной балл: {session['passing_score']}%\n\n"
                f"Вы можете попробовать ещё раз!"
            )
        
        # Удаляем сессию
        del test_sessions[user_id]
        
        await bot.send_message(chat_id, result_text, parse_mode="Markdown")
        await show_volunteer_menu(bot, chat_id)
