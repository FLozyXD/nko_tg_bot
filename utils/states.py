user_data_collector = {}
text_generation_data = {}
image_generation_data = {}
text_editor_data = {}
content_plan_data = {}

# Хранилище активных задач для отмены
active_tasks = {}


def cancel_user_tasks(user_id):
    """Отменяет все активные задачи пользователя и очищает его состояния."""
    # Отменяем активную задачу, если она есть
    if user_id in active_tasks:
        task = active_tasks[user_id]
        if not task.done():
            task.cancel()
        del active_tasks[user_id]
    
    # Очищаем все состояния пользователя
    if user_id in text_generation_data:
        del text_generation_data[user_id]
    if user_id in image_generation_data:
        del image_generation_data[user_id]
    if user_id in text_editor_data:
        del text_editor_data[user_id]
    if user_id in content_plan_data:
        del content_plan_data[user_id]

