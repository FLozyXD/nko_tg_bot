import os
from dotenv import load_dotenv

load_dotenv()

TOKEN_DEFAULT = "8325177793:AAF6r1FsuhqHbHLYwS9_xKQpebjLr7vhZmk"
GIGACHAT_CREDENTIALS_DEFAULT = "MDE5YTg5MDktMzEzZi03ZjUwLThiNjEtYzNhNThlMzA2NWU3OmI2NDVlOGI1LWE5MjgtNDMyYy1iMWYzLTM2OGU3MThmMTA1Zg=="
GIGACHAT_VERIFY_SSL_CERTS_DEFAULT = False
GIGACHAT_SCOPE_DEFAULT = "GIGACHAT_API_PERS"
KANDINSKY_API_KEY_DEFAULT = "288A3EE51938355175C05BDA97B9BD8A"
KANDINSKY_SECRET_KEY_DEFAULT = "39D1CF89E40D0F4E2E1AE8853335EFB7"
KANDINSKY_URL_DEFAULT = "https://api-key.fusionbrain.ai/"

def get_config(key: str, default: str = ""):
    value = os.getenv(key)
    if value is None or value == "" or "your_" in value or "_here" in value:
        return default
    return value

TOKEN = get_config('TOKEN', TOKEN_DEFAULT)
GIGACHAT_CREDENTIALS = get_config('GIGACHAT_CREDENTIALS', GIGACHAT_CREDENTIALS_DEFAULT)
GIGACHAT_VERIFY_SSL_CERTS = get_config('GIGACHAT_VERIFY_SSL_CERTS', str(GIGACHAT_VERIFY_SSL_CERTS_DEFAULT)).lower() == 'true'
GIGACHAT_SCOPE = get_config('GIGACHAT_SCOPE', GIGACHAT_SCOPE_DEFAULT)
KANDINSKY_API_KEY = get_config('KANDINSKY_API_KEY', KANDINSKY_API_KEY_DEFAULT)
KANDINSKY_SECRET_KEY = get_config('KANDINSKY_SECRET_KEY', KANDINSKY_SECRET_KEY_DEFAULT)
KANDINSKY_URL = get_config('KANDINSKY_URL', KANDINSKY_URL_DEFAULT)

def validate_config():
    errors = []
    
    if not TOKEN or TOKEN == "":
        errors.append("⚠️ TOKEN не установлен! Получите его у @BotFather в Telegram")
    
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
    print(f"   • База данных: SQLite (локальный файл)")
    print()
    return True

