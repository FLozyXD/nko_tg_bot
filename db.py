import asyncpg
import config

pool = None

async def init_db():
    global pool
    db_url = config.DATABASE_URL
    if not db_url:
        raise Exception("DATABASE_URL не настроен в config.py")

    pool = await asyncpg.create_pool(db_url)
    
    async with pool.acquire() as connection:
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
    if pool:
        await pool.close()
        print("Соединение с PostgreSQL закрыто.")

async def get_nko_info(user_id):
    if pool is None:
        return None
    try:
        async with pool.acquire() as connection:
            record = await connection.fetchrow(
                'SELECT * FROM nko_profiles WHERE user_id = $1',
                user_id
            )
            return record
    except:
        return None

async def save_or_update_nko_info(user_id, name, description, audience, style):
    if pool is None:
        return
    try:
        async with pool.acquire() as connection:
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
    except:
        pass