from telebot import types


def get_role_selection_keyboard():
    markup = types.ReplyKeyboardMarkup(row_width=1, resize_keyboard=True)
    btn_employee = types.KeyboardButton("Я сотрудник НКО")
    btn_volunteer = types.KeyboardButton("Я волонтёр")
    markup.add(btn_employee, btn_volunteer)
    return markup


def get_employee_menu_keyboard():
    markup = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    btn1 = types.KeyboardButton("📝 Генерация текста")
    btn2 = types.KeyboardButton("🎨 Генерация картинки")
    btn3 = types.KeyboardButton("✏️ Редактор текста")
    btn4 = types.KeyboardButton("📅 Контент-план")
    btn5 = types.KeyboardButton("ℹ️ Информация о НКО")
    btn6 = types.KeyboardButton("🔙 Сменить роль")
    markup.add(btn1, btn2, btn3, btn4, btn5, btn6)
    return markup


def get_volunteer_menu_keyboard():
    markup = types.ReplyKeyboardMarkup(row_width=1, resize_keyboard=True)
    btn1 = types.KeyboardButton("Информация по мероприятию")
    btn2 = types.KeyboardButton("Тест для подтверждения компетенций")
    btn3 = types.KeyboardButton("Выбор мероприятия (будущие)")
    btn4 = types.KeyboardButton("🔙 Сменить роль")
    markup.add(btn1, btn2, btn3, btn4)
    return markup


def get_nko_update_inline_keyboard():
    markup = types.InlineKeyboardMarkup()
    markup.add(
        types.InlineKeyboardButton("Да, обновить", callback_data="update_nko_info"),
        types.InlineKeyboardButton("Нет, назад", callback_data="cancel_nko_update")
    )
    return markup


def get_style_keyboard():
    markup = types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
    markup.add("Разговорный", "Официально-деловой", "Художественный")
    return markup


def get_text_generation_modes_keyboard():
    markup = types.InlineKeyboardMarkup()
    markup.add(
        types.InlineKeyboardButton("Свободный текст", callback_data="text_gen_free"),
        types.InlineKeyboardButton("Структурированная форма", callback_data="text_gen_structured")
    )
    markup.add(
        types.InlineKeyboardButton("На основе примеров", callback_data="text_gen_examples")
    )
    markup.add(types.InlineKeyboardButton("🔙 Назад", callback_data="back_to_menu"))
    return markup


def get_content_plan_period_keyboard():
    markup = types.InlineKeyboardMarkup()
    markup.add(
        types.InlineKeyboardButton("Неделя", callback_data="cp_period_week"),
        types.InlineKeyboardButton("Месяц", callback_data="cp_period_month")
    )
    markup.add(types.InlineKeyboardButton("🔙 Назад", callback_data="back_to_menu"))
    return markup


def get_content_plan_frequency_keyboard(period):
    markup = types.InlineKeyboardMarkup()
    if period == "неделю":
        markup.add(
            types.InlineKeyboardButton("1 раз в неделю", callback_data="cp_freq_1pw"),
            types.InlineKeyboardButton("2 раза в неделю", callback_data="cp_freq_2pw")
        )
        markup.add(
            types.InlineKeyboardButton("3 раза в неделю", callback_data="cp_freq_3pw"),
            types.InlineKeyboardButton("Ежедневно", callback_data="cp_freq_daily")
        )
    else:
        markup.add(
            types.InlineKeyboardButton("2-3 раза в неделю", callback_data="cp_freq_2-3pw"),
            types.InlineKeyboardButton("Ежедневно", callback_data="cp_freq_daily")
        )
    return markup

