import aiosqlite
import json
from datetime import datetime, timedelta

DB_PATH = "nko_bot.db"
db = None


async def init_db():
    """Инициализация базы данных SQLite"""
    global db
    
    db = await aiosqlite.connect(DB_PATH)
    db.row_factory = aiosqlite.Row
    
    # Таблица профилей НКО
    await db.execute('''
        CREATE TABLE IF NOT EXISTS nko_profiles (
            user_id INTEGER PRIMARY KEY,
            nko_name TEXT,
            nko_description TEXT,
            nko_audience TEXT,
            nko_style TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Таблица мероприятий
    await db.execute('''
        CREATE TABLE IF NOT EXISTS events (
            event_id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            description TEXT,
            event_date TEXT,
            location TEXT,
            max_volunteers INTEGER,
            required_competences TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            status TEXT DEFAULT 'upcoming'
        )
    ''')
    
    # Таблица регистраций волонтёров на мероприятия
    await db.execute('''
        CREATE TABLE IF NOT EXISTS event_registrations (
            registration_id INTEGER PRIMARY KEY AUTOINCREMENT,
            event_id INTEGER,
            user_id INTEGER NOT NULL,
            registered_at TEXT DEFAULT CURRENT_TIMESTAMP,
            status TEXT DEFAULT 'registered',
            FOREIGN KEY (event_id) REFERENCES events(event_id),
            UNIQUE(event_id, user_id)
        )
    ''')
    
    # Таблица тестов
    await db.execute('''
        CREATE TABLE IF NOT EXISTS competence_tests (
            test_id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            description TEXT,
            competence_type TEXT NOT NULL,
            questions TEXT NOT NULL,
            passing_score INTEGER DEFAULT 80
        )
    ''')
    
    # Таблица результатов тестов
    await db.execute('''
        CREATE TABLE IF NOT EXISTS test_results (
            result_id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            test_id INTEGER,
            score INTEGER,
            passed INTEGER,
            completed_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (test_id) REFERENCES competence_tests(test_id)
        )
    ''')
    
    await db.commit()
    print("✅ База данных SQLite инициализирована")


async def close_db():
    """Закрытие соединения с БД"""
    if db:
        await db.close()
        print("Соединение с SQLite закрыто.")


# ============= Функции для работы с НКО =============

async def get_nko_info(user_id):
    """Получить информацию об НКО пользователя"""
    if db is None:
        return None
    try:
        async with db.execute(
            'SELECT * FROM nko_profiles WHERE user_id = ?',
            (user_id,)
        ) as cursor:
            row = await cursor.fetchone()
            return dict(row) if row else None
    except:
        return None


async def save_or_update_nko_info(user_id, name, description, audience, style):
    """Сохранить или обновить информацию об НКО"""
    if db is None:
        return
    try:
        await db.execute('''
            INSERT INTO nko_profiles (user_id, nko_name, nko_description, nko_audience, nko_style, updated_at)
            VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(user_id) DO UPDATE SET
                nko_name = excluded.nko_name,
                nko_description = excluded.nko_description,
                nko_audience = excluded.nko_audience,
                nko_style = excluded.nko_style,
                updated_at = CURRENT_TIMESTAMP
        ''', (user_id, name, description, audience, style))
        await db.commit()
    except:
        pass


# ============= Функции для работы с мероприятиями =============

async def get_upcoming_events(limit=20):
    """Получить список предстоящих мероприятий"""
    if db is None:
        return []
    try:
        async with db.execute('''
            SELECT e.*, 
                   COUNT(er.registration_id) as registered_count
            FROM events e
            LEFT JOIN event_registrations er ON e.event_id = er.event_id
            WHERE e.status = 'upcoming' AND e.event_date > datetime('now')
            GROUP BY e.event_id
            ORDER BY e.event_date
            LIMIT ?
        ''', (limit,)) as cursor:
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]
    except Exception as e:
        print(f"Ошибка получения мероприятий: {e}")
        return []


async def get_user_events(user_id):
    """Получить мероприятия, на которые зарегистрирован пользователь"""
    if db is None:
        return []
    try:
        async with db.execute('''
            SELECT e.*, er.registered_at, er.status as registration_status
            FROM events e
            JOIN event_registrations er ON e.event_id = er.event_id
            WHERE er.user_id = ?
            ORDER BY e.event_date DESC
        ''', (user_id,)) as cursor:
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]
    except:
        return []


async def register_for_event(user_id, event_id):
    """Зарегистрировать волонтёра на мероприятие"""
    if db is None:
        return False, "База данных недоступна"
    try:
        # Проверяем, есть ли еще места
        async with db.execute('''
            SELECT e.max_volunteers,
                   COUNT(er.registration_id) as registered_count
            FROM events e
            LEFT JOIN event_registrations er ON e.event_id = er.event_id
            WHERE e.event_id = ?
            GROUP BY e.event_id, e.max_volunteers
        ''', (event_id,)) as cursor:
            event = await cursor.fetchone()
        
        if not event:
            return False, "Мероприятие не найдено"
        
        max_vol = event['max_volunteers']
        if max_vol and event['registered_count'] >= max_vol:
            return False, "Все места заняты"
        
        # Регистрируем
        await db.execute('''
            INSERT INTO event_registrations (event_id, user_id)
            VALUES (?, ?)
        ''', (event_id, user_id))
        await db.commit()
        
        return True, "Вы успешно зарегистрированы!"
    except Exception as e:
        if 'UNIQUE' in str(e):
            return False, "Вы уже зарегистрированы на это мероприятие"
        return False, f"Ошибка регистрации: {e}"


async def unregister_from_event(user_id, event_id):
    """Отменить регистрацию на мероприятие"""
    if db is None:
        return False
    try:
        await db.execute('''
            DELETE FROM event_registrations
            WHERE event_id = ? AND user_id = ?
        ''', (event_id, user_id))
        await db.commit()
        return True
    except:
        return False


# ============= Функции для работы с тестами =============

async def get_all_tests():
    """Получить список всех доступных тестов"""
    if db is None:
        return []
    try:
        async with db.execute('''
            SELECT test_id, title, description, competence_type
            FROM competence_tests
            ORDER BY title
        ''') as cursor:
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]
    except:
        return []


async def get_test_by_id(test_id):
    """Получить полную информацию о тесте включая вопросы"""
    if db is None:
        return None
    try:
        async with db.execute('''
            SELECT * FROM competence_tests
            WHERE test_id = ?
        ''', (test_id,)) as cursor:
            row = await cursor.fetchone()
            if row:
                result = dict(row)
                result['questions'] = json.loads(result['questions'])
                return result
            return None
    except Exception as e:
        print(f"Ошибка получения теста: {e}")
        return None


async def save_test_result(user_id, test_id, score, passed):
    """Сохранить результат прохождения теста"""
    if db is None:
        return
    try:
        await db.execute('''
            INSERT INTO test_results (user_id, test_id, score, passed)
            VALUES (?, ?, ?, ?)
        ''', (user_id, test_id, score, 1 if passed else 0))
        await db.commit()
    except:
        pass


async def get_user_test_results(user_id, test_id=None):
    """Получить результаты тестов пользователя"""
    if db is None:
        return []
    try:
        if test_id:
            query = '''
                SELECT tr.*, ct.title, ct.competence_type
                FROM test_results tr
                JOIN competence_tests ct ON tr.test_id = ct.test_id
                WHERE tr.user_id = ? AND tr.test_id = ?
                ORDER BY tr.completed_at DESC
            '''
            params = (user_id, test_id)
        else:
            query = '''
                SELECT tr.*, ct.title, ct.competence_type
                FROM test_results tr
                JOIN competence_tests ct ON tr.test_id = ct.test_id
                WHERE tr.user_id = ?
                ORDER BY tr.completed_at DESC
            '''
            params = (user_id,)
        
        async with db.execute(query, params) as cursor:
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]
    except:
        return []


async def init_sample_data():
    """Инициализация примеров мероприятий и тестов"""
    if db is None:
        return
    
    try:
        # Проверяем, есть ли уже данные
        async with db.execute('SELECT COUNT(*) as cnt FROM events') as cursor:
            row = await cursor.fetchone()
            if row['cnt'] > 0:
                print("Примеры данных уже существуют")
                return
        
        print("Добавление примеров данных...")
        
        # Текущая дата для расчета будущих дат
        now = datetime.now()
        
        # Добавляем мероприятия
        events = [
            ('Помощь в доме престарелых', 
             'Волонтёры помогут пожилым людям с бытовыми делами, проведут развлекательные мероприятия и просто пообщаются', 
             (now + timedelta(days=27)).isoformat(), 
             'ул. Советская, 15, Дом престарелых "Забота"', 
             10, 
             json.dumps(['elderly_care', 'communication']),
             'upcoming'),
            
            ('Сбор вещей для бездомных', 
             'Организация и проведение акции по сбору одежды, обуви и предметов первой необходимости для людей без определенного места жительства', 
             (now + timedelta(days=34)).isoformat(), 
             'Центральная площадь, павильон №3', 
             15, 
             json.dumps(['organization', 'communication']),
             'upcoming'),
            
            ('Детский праздник в приюте', 
             'Проведение праздничных мероприятий, конкурсов и игр для детей в детском приюте. Подарки и угощения приветствуются!', 
             (now + timedelta(days=41)).isoformat(), 
             'Детский приют "Надежда", ул. Парковая, 28', 
             8, 
             json.dumps(['children_work', 'animation']),
             'upcoming'),
            
            ('Уборка городского парка', 
             'Субботник по уборке и благоустройству центрального парка. Работа в команде на свежем воздухе!', 
             (now + timedelta(days=30)).isoformat(), 
             'Центральный парк, вход со стороны ул. Ленина', 
             25, 
             json.dumps(['organization']),
             'upcoming'),
            
            ('Помощь в приюте для животных', 
             'Уход за бездомными животными: кормление, выгул, уборка вольеров. Любовь к животным обязательна!', 
             (now + timedelta(days=25)).isoformat(), 
             'Приют "Верный друг", Загородное шоссе, 45', 
             12, 
             json.dumps(['animal_care']),
             'upcoming'),
            
            ('Благотворительный концерт', 
             'Помощь в организации благотворительного концерта: встреча гостей, координация, техническая поддержка', 
             (now + timedelta(days=50)).isoformat(), 
             'Городской дворец культуры', 
             20, 
             json.dumps(['organization', 'event_management']),
             'upcoming'),
            
            ('Мастер-класс для детей из малоимущих семей', 
             'Проведение творческих мастер-классов по рисованию, лепке и рукоделию для детей', 
             (now + timedelta(days=38)).isoformat(), 
             'Социальный центр "Радуга", ул. Мира, 12', 
             6, 
             json.dumps(['children_work', 'creative_skills']),
             'upcoming'),
            
            ('Продуктовая помощь нуждающимся семьям', 
             'Сбор и раздача продуктовых наборов для малоимущих семей и пенсионеров', 
             (now + timedelta(days=32)).isoformat(), 
             'Социальный центр, ул. Гагарина, 8', 
             10, 
             json.dumps(['organization', 'communication']),
             'upcoming'),
        ]
        
        for event in events:
            await db.execute('''
                INSERT INTO events (title, description, event_date, location, max_volunteers, required_competences, status)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', event)
        
        # Добавляем тесты
        tests = [
            # Тест 1: Работа с пожилыми
            ('Работа с пожилыми людьми',
             'Тест на знание основ взаимодействия с пожилыми людьми и особенностей ухода',
             'elderly_care',
             json.dumps([
                {
                    "question": "Как правильно обращаться к пожилому человеку?",
                    "options": ["На 'ты', как к другу", "На 'вы', уважительно по имени-отчеству", "По имени без отчества", "Называть 'дедушка/бабушка'"],
                    "correct": 1
                },
                {
                    "question": "Что важно учитывать при общении с пожилыми людьми?",
                    "options": ["Говорить быстро и кратко", "Быть терпеливым, внимательным и говорить четко", "Избегать зрительного контакта", "Использовать много сложных терминов"],
                    "correct": 1
                },
                {
                    "question": "Если пожилой человек плохо слышит, что делать?",
                    "options": ["Кричать как можно громче", "Говорить четко, глядя в лицо, слегка громче обычного", "Игнорировать проблему", "Использовать только жесты"],
                    "correct": 1
                },
                {
                    "question": "Пожилой человек забыл, о чем говорил минуту назад. Ваши действия?",
                    "options": ["Сказать 'Вы уже это говорили'", "Терпеливо выслушать снова", "Перевести разговор на другую тему", "Уйти"],
                    "correct": 1
                },
                {
                    "question": "Как помочь пожилому человеку встать со стула?",
                    "options": ["Резко потянуть за руку", "Предложить опору, поддержать под локоть", "Подождать пока встанет сам", "Поднять под мышки"],
                    "correct": 1
                }
            ]),
             70),
            
            # Тест 2: Первая помощь
            ('Первая помощь',
             'Базовые знания оказания первой помощи при неотложных состояниях',
             'first_aid',
             json.dumps([
                {
                    "question": "Что делать при обмороке?",
                    "options": ["Посадить человека на стул", "Уложить на спину и приподнять ноги", "Сразу дать понюхать нашатырь", "Дать попить холодной воды"],
                    "correct": 1
                },
                {
                    "question": "Единый номер экстренных служб в России:",
                    "options": ["911", "112", "101", "102"],
                    "correct": 1
                },
                {
                    "question": "При сильном кровотечении из раны нужно:",
                    "options": ["Промыть рану проточной водой", "Наложить жгут выше раны", "Прижать рану чистой тканью и приподнять конечность", "Обработать йодом"],
                    "correct": 2
                },
                {
                    "question": "Признаки инсульта:",
                    "options": ["Боль в животе", "Асимметрия лица, нарушение речи, слабость в руке", "Кашель и насморк", "Головная боль"],
                    "correct": 1
                },
                {
                    "question": "При ожоге кипятком сразу нужно:",
                    "options": ["Смазать маслом", "Проколоть пузыри", "Охладить холодной водой 10-15 минут", "Приложить лед"],
                    "correct": 2
                }
            ]),
             80),
            
            # Тест 3: Работа с детьми
            ('Работа с детьми',
             'Основы взаимодействия с детьми разных возрастов и организации детских мероприятий',
             'children_work',
             json.dumps([
                {
                    "question": "Как лучше установить контакт с незнакомым ребенком?",
                    "options": ["Быть строгим и требовательным", "Присесть на его уровень, улыбнуться и представиться", "Игнорировать пока не подойдет сам", "Сразу взять на руки"],
                    "correct": 1
                },
                {
                    "question": "Если ребенок плачет, что делать?",
                    "options": ["Строго сказать 'не плачь'", "Быстро отвлечь игрушкой", "Выслушать, успокоить, выяснить причину", "Оставить одного, пока не успокоится"],
                    "correct": 2
                },
                {
                    "question": "При работе с группой детей важно:",
                    "options": ["Следить только за самыми активными", "Держать всех детей в поле зрения", "Дать полную свободу действий", "Не вмешиваться в их игры"],
                    "correct": 1
                },
                {
                    "question": "Ребенок отказывается участвовать в игре. Ваши действия?",
                    "options": ["Заставить участвовать", "Уважать его выбор, предложить наблюдать", "Ругать за непослушание", "Игнорировать его"],
                    "correct": 1
                },
                {
                    "question": "Как правильно хвалить ребенка?",
                    "options": ["Хвалить только результат", "Хвалить усилия и старания", "Не хвалить вообще", "Хвалить только при других детях"],
                    "correct": 1
                }
            ]),
             75),
            
            # Тест 4: Организация мероприятий
            ('Организация мероприятий',
             'Основы планирования и проведения благотворительных и социальных мероприятий',
             'event_management',
             json.dumps([
                {
                    "question": "Что важнее всего при планировании мероприятия?",
                    "options": ["Красивое оформление", "Четкий план и расписание", "Много угощений", "Дорогие подарки"],
                    "correct": 1
                },
                {
                    "question": "За сколько времени нужно начинать подготовку к мероприятию?",
                    "options": ["За день до события", "Минимум за 2-3 недели", "В день проведения", "За несколько часов"],
                    "correct": 1
                },
                {
                    "question": "Что делать, если участник команды не справляется со своей задачей?",
                    "options": ["Сделать все самому", "Предложить помощь и перераспределить обязанности", "Ругать его публично", "Игнорировать проблему"],
                    "correct": 1
                },
                {
                    "question": "Главная цель благотворительного мероприятия:",
                    "options": ["Показать себя", "Помочь нуждающимся", "Собрать больше денег", "Привлечь внимание СМИ"],
                    "correct": 1
                }
            ]),
             70),
            
            # Тест 5: Психологическая поддержка
            ('Психологическая поддержка',
             'Основы оказания эмоциональной поддержки людям в трудной жизненной ситуации',
             'psychological_support',
             json.dumps([
                {
                    "question": "Человек делится своей проблемой. Что лучше сказать?",
                    "options": ["'Да ладно, это ерунда'", "'Я понимаю, как тебе сейчас тяжело'", "'У меня было хуже'", "'Сам виноват'"],
                    "correct": 1
                },
                {
                    "question": "Активное слушание - это:",
                    "options": ["Молча слушать", "Слушать, задавать уточняющие вопросы, проявлять эмпатию", "Давать советы", "Рассказывать свои истории"],
                    "correct": 1
                },
                {
                    "question": "Если человек плачет при разговоре:",
                    "options": ["Сказать 'не плачь'", "Дать время, предложить салфетку, проявить понимание", "Сменить тему", "Уйти"],
                    "correct": 1
                },
                {
                    "question": "Главное правило при оказании психологической поддержки:",
                    "options": ["Дать совет", "Быть эмпатичным и не осуждать", "Рассказать о себе", "Развеселить человека"],
                    "correct": 1
                }
            ]),
             75),
        ]
        
        for test in tests:
            await db.execute('''
                INSERT INTO competence_tests (title, description, competence_type, questions, passing_score)
                VALUES (?, ?, ?, ?, ?)
            ''', test)
        
        await db.commit()
        print("✅ Примеры данных успешно добавлены!")
        print(f"   • Мероприятий: {len(events)}")
        print(f"   • Тестов: {len(tests)}")
        
    except Exception as e:
        print(f"❌ Ошибка при добавлении примеров: {e}")
        import traceback
        traceback.print_exc()
