import requests
import uuid
import config
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


class GigaChatRestAPI:
    
    def __init__(self):
        self.credentials = config.GIGACHAT_CREDENTIALS
        self.scope = config.GIGACHAT_SCOPE
        self.base_url = "https://gigachat.devices.sberbank.ru/api/v1"
        self.access_token = None
    
    def get_token(self):
        url = "https://ngw.devices.sberbank.ru:9443/api/v2/oauth"
        headers = {
            'Authorization': f'Bearer {self.credentials}',
            'RqUID': str(uuid.uuid4()),
            'Content-Type': 'application/x-www-form-urlencoded'
        }
        data = {'scope': self.scope}
        
        try:
            response = requests.post(url, headers=headers, data=data, verify=False, timeout=30)
            response.raise_for_status()
            return response.json()['access_token']
        except Exception as e:
            print(f"Ошибка получения токена GigaChat: {e}")
            return None
    
    def chat(self, message, system_prompt=None):
        if not self.access_token:
            self.access_token = self.get_token()
            if not self.access_token:
                return "Ошибка: не удалось получить токен доступа GigaChat"
        
        url = f"{self.base_url}/chat/completions"
        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'Content-Type': 'application/json'
        }
        
        messages = []
        if system_prompt:
            messages.append({
                "role": "system",
                "content": system_prompt
            })
        
        messages.append({
            "role": "user",
            "content": message
        })
        
        data = {
            "model": "GigaChat",
            "messages": messages,
            "temperature": 0.7,
            "max_tokens": 1000
        }
        
        try:
            response = requests.post(url, headers=headers, json=data, verify=False, timeout=60)
            
            if response.status_code == 401:
                self.access_token = self.get_token()
                if self.access_token:
                    headers['Authorization'] = f'Bearer {self.access_token}'
                    response = requests.post(url, headers=headers, json=data, verify=False, timeout=60)
            
            response.raise_for_status()
            result = response.json()
            
            if 'choices' in result and len(result['choices']) > 0:
                return result['choices'][0]['message']['content']
            else:
                return "Ошибка: некорректный ответ от GigaChat"
                
        except Exception as e:
            print(f"Ошибка GigaChat API: {e}")
            return f"Ошибка генерации: {str(e)}"


gigachat_rest_service = GigaChatRestAPI()

