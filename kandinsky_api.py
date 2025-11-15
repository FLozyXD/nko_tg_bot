import json
import time
import base64
import requests
import config


class KandinskyAPI:
    
    def __init__(self):
        self.URL = config.KANDINSKY_URL
        self.AUTH_HEADERS = {
            'X-Key': f'Key {config.KANDINSKY_API_KEY}',
            'X-Secret': f'Secret {config.KANDINSKY_SECRET_KEY}',
        }
    
    def get_pipeline(self):
        try:
            response = requests.get(
                self.URL + 'key/api/v1/pipelines', 
                headers=self.AUTH_HEADERS,
                timeout=10
            )
            response.raise_for_status()
            data = response.json()
            if not data or len(data) == 0:
                raise Exception("Не удалось получить список моделей")
            return data[0]['id']
        except requests.exceptions.RequestException as e:
            raise Exception(f"Ошибка подключения к Kandinsky API: {str(e)}")
    
    def generate(self, prompt, pipeline_id, images=1, width=1024, height=1024):
        try:
            params = {
                "type": "GENERATE",
                "numImages": images,
                "width": width,
                "height": height,
                "generateParams": {
                    "query": prompt
                }
            }
            
            files = {
                'pipeline_id': (None, str(pipeline_id)),
                'params': (None, json.dumps(params), 'application/json')
            }
            
            response = requests.post(
                self.URL + 'key/api/v1/pipeline/run', 
                headers=self.AUTH_HEADERS, 
                files=files,
                timeout=30
            )
            response.raise_for_status()
            data = response.json()
            
            if 'uuid' not in data:
                raise Exception(f"Некорректный ответ API: {data}")
            
            return data['uuid']
        except requests.exceptions.RequestException as e:
            raise Exception(f"Ошибка запроса генерации: {str(e)}")
    
    def check_generation(self, request_id, attempts=40, delay=3):
        while attempts > 0:
            try:
                response = requests.get(
                    self.URL + 'key/api/v1/pipeline/status/' + request_id, 
                    headers=self.AUTH_HEADERS,
                    timeout=10
                )
                response.raise_for_status()
                data = response.json()
                
                if data.get('status') == 'DONE':
                    return data.get('result', {})
                elif data.get('status') == 'FAIL':
                    error_desc = data.get('errorDescription', 'Неизвестная ошибка')
                    raise Exception(f"Генерация не удалась: {error_desc}")
                
                attempts -= 1
                time.sleep(delay)
            except requests.exceptions.RequestException as e:
                if attempts > 1:
                    attempts -= 1
                    time.sleep(delay)
                    continue
                else:
                    raise Exception(f"Ошибка проверки статуса: {str(e)}")
        
        raise Exception("Превышено время ожидания генерации (2 минуты)")
    
    def generate_image(self, prompt, width=1024, height=1024):
        try:
            print(f"[Kandinsky] Получение pipeline ID...")
            pipeline_id = self.get_pipeline()
            print(f"[Kandinsky] Pipeline ID: {pipeline_id}")
            
            print(f"[Kandinsky] Отправка запроса на генерацию...")
            uuid = self.generate(prompt, pipeline_id, images=1, width=width, height=height)
            print(f"[Kandinsky] UUID задания: {uuid}")
            
            print(f"[Kandinsky] Ожидание результата...")
            result = self.check_generation(uuid)
            
            if result.get('censored'):
                raise Exception("Изображение не прошло модерацию. Попробуйте изменить описание.")
            
            if 'files' not in result or len(result['files']) == 0:
                raise Exception("API не вернул изображение")
            
            print(f"[Kandinsky] Декодирование изображения...")
            image_base64 = result['files'][0]
            image_data = base64.b64decode(image_base64)
            print(f"[Kandinsky] Готово! Размер: {len(image_data)} байт")
            
            return image_data
            
        except Exception as e:
            print(f"[Kandinsky] Ошибка: {str(e)}")
            raise Exception(str(e))


kandinsky_service = KandinskyAPI()

