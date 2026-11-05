# NKO Assistant — Telegram-бот для НКО

Ассистент для небольших некоммерческих организаций: помогает готовить тексты,
изображения и контент-план, а также ведёт запись волонтёров на мероприятия.

Проект вырос из хакатона и доведён до рабочего бота с базой SQLite,
интеграциями GigaChat и Kandinsky и покрытием основных пользовательских сценариев.

## Возможности

- **Генерация текстов** — свободный запрос, структурированная форма и режим
  с примерами (few-shot) для более предсказуемого стиля.
- **Генерация промптов для изображений** — подготовка описаний под Kandinsky.
- **Редактор текста** — переписывание, сокращение и корректировка готового текста.
- **Контент-план** — план публикаций для сообщества НКО.
- **Профиль организации** — название, описание, аудитория и стиль общения;
  данные используются как контекст генерации.
- **Волонтёры** — список мероприятий, регистрация и отмена записи с проверкой
  лимита участников, тесты компетенций и результаты.

## Стек

- Python 3.10+
- [pyTelegramBotAPI](https://github.com/eternnoir/pyTelegramBotAPI) — Telegram Bot API
- `aiosqlite` — асинхронная работа с SQLite
- GigaChat SDK и REST API — генерация текста
- Kandinsky / FusionBrain API — генерация изображений
- `python-dotenv` — конфигурация через `.env`

## Архитектура

```text
main.py                 точка входа, регистрация хендлеров
config.py               чтение и валидация конфигурации
db.py                   схема SQLite и функции доступа к данным
gigachat_api.py         обёртка над GigaChat SDK
gigachat_rest_api.py    альтернативный REST-клиент
kandinsky_api.py        клиент генерации изображений
handlers/
  start.py              приветствие и главное меню
  nko_info.py           профиль организации
  text_generation.py    генерация текстов (3 режима)
  image_generation.py   промпты и изображения
  text_editor.py        редактирование текста
  content_plan.py       контент-план
  volunteer.py          мероприятия и тесты
utils/
  keyboards.py          клавиатуры
  states.py             состояния диалогов
```

Данные хранятся в локальном файле `nko_bot.db` (создаётся автоматически).
При первом запуске `db.init_sample_data()` добавляет демонстрационные
мероприятия и тесты компетенций.

## Запуск

```bash
python -m venv .venv
# Windows: .venv\Scripts\activate
# Linux/macOS: source .venv/bin/activate
pip install -r requirements.txt
copy .env.example .env    # Windows
# cp .env.example .env    # Linux/macOS
```

Заполните `.env`:

| Переменная | Назначение |
|---|---|
| `TOKEN` | токен бота от [@BotFather](https://t.me/BotFather) |
| `GIGACHAT_CREDENTIALS` | Authorization key из личного кабинета GigaChat |
| `GIGACHAT_SCOPE` | `GIGACHAT_API_PERS` для физических лиц |
| `GIGACHAT_VERIFY_SSL_CERTS` | `true` в production, `false` — только для локальной отладки |
| `KANDINSKY_API_KEY`, `KANDINSKY_SECRET_KEY` | ключи FusionBrain |

Запуск:

```bash
python main.py
```

Для GigaChat может потребоваться добавить корневой сертификат Минцифры в
хранилище `certifi`. В репозитории сертификат не хранится; инструкция есть в
документации GigaChat.

## Безопасность

- В репозитории нет токенов и ключей: все секреты читаются из `.env`.
- Файл `.env`, база `nko_bot.db` и логи исключены через `.gitignore`.
- Перед публикацией удалите локальную базу, если в ней есть реальные данные.

## Статус

Учебно-хакатонный проект. Основные сценарии работают; для production
потребуются PostgreSQL вместо SQLite, очередь задач и мониторинг.

## Лицензия

MIT.
