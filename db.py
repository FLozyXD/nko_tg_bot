import asyncpg
import os
from dotenv import load_dotenv

load_dotenv()

# Пул соединений будет храниться здесь
pool = asyncpg.create_pool()

async def init_db():
    """
    Инициализирует пул соединений с базой данных и создает таблицу, если её нет.
    """
    global pool
    # Получаем строку подключения из переменных окружения
    db_url = os.getenv('DATABASE_URL')
    if not db_url:
        raise Exception("DATABASE_URL не найден в .env файле")

    # Создаем пул соединений
    pool = await asyncpg.create_pool(db_url)
    
    # async with - безопасный способ получить соединение из пула
    async with pool.acquire() as connection:
        # Создаем таблицу, если она не существует.
        # BIGINT для user_id, так как ID в Telegram могут быть большими.
        # TEXT для текстовых полей.
        # PRIMARY KEY(user_id) - гарантирует уникальность пользователя.
        await connection.execute('''
            CREATE TABLE IF NOT EXISTS nko_profiles (
                user_id BIGINT PRIMARY KEY,
                nko_name TEXT,
                nko_description TEXT,
                nko_audience TEXT,
                nko_style TEXT,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
            )
        ''')
    print("Соединение с PostgreSQL установлено и таблица проверена.")

async def close_db():
    """Закрывает пул соединений."""
    if pool:
        await pool.close()
        print("Соединение с PostgreSQL закрыто.")

async def get_nko_info(user_id):
    """
    Получает информацию об НКО для конкретного пользователя.
    Возвращает запись (похожа на словарь) или None, если ничего не найдено.
    """
    async with pool.acquire() as connection:
        record = await connection.fetchrow(
            'SELECT * FROM nko_profiles WHERE user_id = $1',
            user_id
        )
        return record

async def save_or_update_nko_info(user_id, name, description, audience, style):
    """
    Сохраняет или обновляет информацию об НКО.
    Использует мощную конструкцию "UPSERT" (UPDATE or INSERT) из PostgreSQL.
    """
    async with pool.acquire() as connection:
        # ON CONFLICT (user_id) DO UPDATE - если запись с таким user_id уже есть,
        # то не вставлять новую, а обновить существующую.
        await connection.execute('''
            INSERT INTO nko_profiles (user_id, nko_name, nko_description, nko_audience, nko_style, updated_at)
            VALUES ($1, $2, $3, $4, $5, CURRENT_TIMESTAMP)
            ON CONFLICT (user_id) DO UPDATE SET
                nko_name = EXCLUDED.nko_name,
                nko_description = EXCLUDED.nko_description,
                nko_audience = EXCLUDED.nko_audience,
                nko_style = EXCLUDED.nko_style,
                updated_at = CURRENT_TIMESTAMP
        ''', user_id, name, description, audience, style)