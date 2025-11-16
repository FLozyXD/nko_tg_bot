import os
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv('TOKEN')
DATABASE_URL = os.getenv('DATABASE_URL')
GIGACHAT_CREDENTIALS = os.getenv('GIGACHAT_CREDENTIALS')
GIGACHAT_VERIFY_SSL_CERTS = os.getenv('GIGACHAT_VERIFY_SSL_CERTS')
GIGACHAT_SCOPE = os.getenv('GIGACHAT_SCOPE')
KANDINSKY_API_KEY = os.getenv('KANDINSKY_API_KEY')
KANDINSKY_SECRET_KEY = os.getenv('KANDINSKY_SECRET_KEY')
KANDINSKY_URL = os.getenv('KANDINSKY_URL')

def validate_config():
    errors = []
    
    if not TOKEN or TOKEN == "":
        errors.append("⚠️ TOKEN не установлен! Получите его у @BotFather в Telegram")
    
    if not DATABASE_URL:
        errors.append("⚠️ DATABASE_URL не установлен!")
    
    
    if errors:
        print("\n" + "="*60)
        print("❌ ОШИБКА КОНФИГУРАЦИИ:")
        print("="*60)
        for error in errors:
            print(f"  {error}")
        print("\n📝 ИНСТРУКЦИЯ:")
        print("  1. Откройте файл config.py")
        print("  2. Найдите переменную TOKEN_DEFAULT")
        print("  3. Вставьте туда токен от @BotFather")
        print("  4. Сохраните и перезапустите бота")
        print("="*60 + "\n")
        return False
    
    print("✅ Конфигурация успешно загружена!")
    print(f"   • Telegram Bot: {'настроен' if TOKEN else 'НЕ настроен'}")
    print(f"   • Kandinsky API: {'настроен ✨' if KANDINSKY_API_KEY else 'НЕ настроен'}")
    print(f"   • База данных: {'настроена' if DATABASE_URL else 'НЕ настроена'}")
    print()
    return True

