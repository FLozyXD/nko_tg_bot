from gigachat import GigaChat
from gigachat.models import Chat, Messages, MessagesRole
import asyncio
from typing import Optional, Dict
import config


class GigaChatService:
    
    def __init__(self):
        self.credentials = config.GIGACHAT_CREDENTIALS
        self.verify_ssl = config.GIGACHAT_VERIFY_SSL_CERTS
        self.scope = config.GIGACHAT_SCOPE
        
        if not self.credentials:
            raise ValueError("GIGACHAT_CREDENTIALS не настроен в config.py!")
    
    def _get_client(self):
        return GigaChat(
            credentials=self.credentials,
            verify_ssl_certs=self.verify_ssl,
            scope=self.scope
        )
    
    async def generate_text(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self._generate_text_sync, prompt, system_prompt)
    
    def _generate_text_sync(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        try:
            with self._get_client() as giga:
                messages = []
                
                if system_prompt:
                    messages.append(
                        Messages(role=MessagesRole.SYSTEM, content=system_prompt)
                    )
                
                messages.append(
                    Messages(role=MessagesRole.USER, content=prompt)
                )
                
                response = giga.chat(Chat(messages=messages))
                return response.choices[0].message.content
        except Exception as e:
            print(f"Ошибка при генерации текста: {e}")
            return f"Произошла ошибка при генерации: {str(e)}"
    
    async def generate_post_from_idea(self, idea: str, nko_info: Optional[Dict] = None) -> str:
        system_prompt = self._build_system_prompt(nko_info)
        
        prompt = f"""Перепиши следующую идею в готовый пост для социальных сетей:

Идея: {idea}

Требования к посту:
- Текст должен быть без орфографических, грамматических и логических ошибок
- Добавь релевантные хештеги (2-3 штуки)
- Структурируй текст для лучшей читаемости
- Сделай текст вовлекающим и призывающим к действию
- Длина поста: 200-400 символов"""
        
        return await self.generate_text(prompt, system_prompt)
    
    async def generate_post_structured(self, event_data: Dict, nko_info: Optional[Dict] = None) -> str:
        system_prompt = self._build_system_prompt(nko_info)
        
        prompt = f"""Создай пост для социальных сетей о событии на основе следующей информации:

Название события: {event_data.get('event_name', 'Не указано')}
Дата: {event_data.get('date', 'Не указана')}
Место: {event_data.get('place', 'Не указано')}
Кто приглашен: {event_data.get('participants', 'Все желающие')}
Дополнительные детали: {event_data.get('details', '')}

Требования к посту:
- Четкая структура (заголовок, описание, призыв к действию)
- Без орфографических и грамматических ошибок
- Добавь релевантные хештеги (2-3 штуки)
- Сделай текст вовлекающим и информативным
- Длина: 250-500 символов"""
        
        return await self.generate_text(prompt, system_prompt)
    
    async def generate_post_from_example(self, example_posts: str, new_topic: str, nko_info: Optional[Dict] = None) -> str:
        system_prompt = self._build_system_prompt(nko_info)
        
        prompt = f"""Проанализируй стиль и структуру следующих примеров постов:

{example_posts}

Теперь создай новый пост на тему: {new_topic}

Требования:
- Используй тот же стиль и структуру, что в примерах
- Без ошибок
- Добавь релевантные хештеги
- Сохрани тональность и манеру изложения"""
        
        return await self.generate_text(prompt, system_prompt)
    
    async def edit_text(self, text: str) -> str:
        prompt = f"""Проверь следующий текст на наличие ошибок и предложи улучшения:

{text}

Выполни следующее:
1. Исправь все орфографические и грамматические ошибки
2. Улучши логику и структуру изложения
3. Укажи, какие ошибки были найдены и как их исправить
4. Предложи советы для улучшения текста

Формат ответа:
--- ИСПРАВЛЕННЫЙ ТЕКСТ ---
[исправленный текст]

--- НАЙДЕННЫЕ ОШИБКИ И ИСПРАВЛЕНИЯ ---
[список ошибок и исправлений]

--- СОВЕТЫ ПО УЛУЧШЕНИЮ ---
[советы]"""
        
        return await self.generate_text(prompt)
    
    async def generate_content_plan(self, period: str, frequency: str, nko_info: Optional[Dict] = None) -> str:
        system_prompt = self._build_system_prompt(nko_info)
        
        prompt = f"""Создай контент-план для Telegram-канала НКО на период: {period}
Частота публикаций: {frequency}

Требования к контент-плану:
1. Укажи конкретные даты для каждой публикации
2. Определи категорию/тип поста для каждого дня
3. Разнообразь типы контента (анонсы, новости, отчёты, призывы к действию, истории)
4. Учитывай специфику работы НКО
5. Сделай план сбалансированным и интересным для аудитории

Формат ответа:
ДАТА | ТИП ПОСТА | КРАТКОЕ ОПИСАНИЕ"""
        
        return await self.generate_text(prompt, system_prompt)
    
    async def generate_image_prompt(self, description: str) -> str:
        prompt = f"""Создай детальный промпт на русском языке для генерации изображения на основе следующего описания:

{description}

Промпт должен быть детальным и включать:
- Описание объектов и их расположения
- Стиль изображения
- Цветовую палитру
- Настроение и атмосферу
- Технические детали (освещение, композиция)

Сделай промпт подходящим для социально значимого контента НКО."""
        
        return await self.generate_text(prompt)
    
    def _build_system_prompt(self, nko_info: Optional[Dict] = None) -> str:
        if not nko_info:
            return """Ты - профессиональный SMM-специалист, который помогает некоммерческим организациям создавать качественный контент для социальных сетей. Твои тексты должны быть грамотными, вовлекающими и соответствовать целям НКО."""
        
        style = nko_info.get('nko_style', 'разговорный')
        name = nko_info.get('nko_name', 'НКО')
        description = nko_info.get('nko_description', '')
        audience = nko_info.get('nko_audience', 'широкая аудитория')
        
        return f"""Ты - профессиональный SMM-специалист организации "{name}". {description}

Целевая аудитория: {audience}
Стиль общения: {style}

Твоя задача - создавать качественный контент, который:
- Соответствует миссии и ценностям организации
- Написан в {style} стиле
- Адаптирован для аудитории: {audience}
- Грамотен и профессионален
- Вызывает доверие и желание поддержать НКО"""


gigachat_service = GigaChatService()
