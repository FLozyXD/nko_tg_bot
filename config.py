"""Конфигурация бота.

Все секреты читаются только из переменных окружения / файла .env.
Значений по умолчанию для токенов нет — при отсутствии переменных бот
завершится с понятной ошибкой.
"""

import os

from dotenv import load_dotenv

load_dotenv()


def get_config(key: str, default: str = "") -> str:
    value = os.getenv(key)
    if value is None or value == "" or "your_" in value or "_here" in value:
        return default
    return value


TOKEN = get_config("TOKEN")
GIGACHAT_CREDENTIALS = get_config("GIGACHAT_CREDENTIALS")
GIGACHAT_VERIFY_SSL_CERTS = (
    get_config("GIGACHAT_VERIFY_SSL_CERTS", "false").lower() == "true"
)
GIGACHAT_SCOPE = get_config("GIGACHAT_SCOPE", "GIGACHAT_API_PERS")
KANDINSKY_API_KEY = get_config("KANDINSKY_API_KEY")
KANDINSKY_SECRET_KEY = get_config("KANDINSKY_SECRET_KEY")
KANDINSKY_URL = get_config("KANDINSKY_URL", "https://api-key.fusionbrain.ai/")


def validate_config() -> bool:
    errors = []

    if not TOKEN:
        errors.append("TOKEN не установлен. Получите его у @BotFather в Telegram")

    if not GIGACHAT_CREDENTIALS:
        errors.append(
            "GIGACHAT_CREDENTIALS не установлен. Скопируйте Authorization key "
            "из личного кабинета GigaChat"
        )

    if errors:
        print("\n" + "=" * 60)
        print("ОШИБКА КОНФИГУРАЦИИ:")
        print("=" * 60)
        for error in errors:
            print(f"  - {error}")
        print("\nСоздайте файл .env по образцу .env.example и заполните его.")
        print("=" * 60 + "\n")
        return False

    print("Конфигурация успешно загружена")
    print(f"  Telegram Bot: {'настроен' if TOKEN else 'НЕ настроен'}")
    print(f"  Kandinsky API: {'настроен' if KANDINSKY_API_KEY else 'НЕ настроен'}")
    print("  База данных: SQLite (локальный файл)")
    print()
    return True
