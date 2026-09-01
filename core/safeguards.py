import time
import json

class Safeguards:
    def __init__(self, config_path: str = "config/safeguards_config.json"):
        self.config = self._load_config(config_path)
        self.error_count = 0
        self.last_reset = time.time()
        self.token_overflow = False
    
    def _load_config(self, path: str) -> dict:
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except FileNotFoundError:
            return {
                "max_context_size": 10,
                "max_recursion_depth": 5,
                "rate_limit_seconds": 1.0,
                "max_errors_before_sleep": 3,
                "sleep_duration_seconds": 30,
                "token_balance_min": 0,
                "token_balance_max": 1000
            }
    
    def check_context_overflow(self, context_size: int) -> bool:
        """Якщо контекст занадто великий — повертає True"""
        return context_size > self.config["max_context_size"]
    
    def check_recursion(self, depth: int) -> bool:
        """Запобігає зацикленню"""
        return depth > self.config["max_recursion_depth"]
    
    def check_rate_limit(self, last_call_time: float) -> bool:
        """Не дає спамити себе"""
        return (time.time() - last_call_time) < self.config["rate_limit_seconds"]
    
    def check_errors(self) -> bool:
        """Якщо забагато помилок поспіль — відправляє в сон"""
        now = time.time()
        if now - self.last_reset > 60:
            self.error_count = 0
            self.last_reset = now
            return False
        
        if self.error_count >= self.config["max_errors_before_sleep"]:
            print(f"😴 Запобіжник: перевантаження помилками. Сон на {self.config['sleep_duration_seconds']}с")
            time.sleep(self.config["sleep_duration_seconds"])
            self.error_count = 0
            self.last_reset = time.time()
            return True
        return False
    
    def report_error(self):
        """Лічильник помилок"""
        self.error_count += 1
    
    def check_token_balance(self, balance: int) -> bool:
        """Перевіряє, чи баланс токенів у межах норми"""
        if balance < self.config["token_balance_min"] or balance > self.config["token_balance_max"]:
            self.token_overflow = True
            return False
        return True



Потім підключаємо запобіжники до ядра AI-mini. Додаємо в __init__:

self.safeguards = Safeguards()

І вставляємо перевірки в process().

def process(self, user_input: str) -> str:
    # запобіжник: перевірка помилок
    if self.safeguards.check_errors():
        return "Я відпочиваю після навантаження. Зачекай трохи."
    
    # запобіжник: перевірка контексту
    if self.safeguards.check_context_overflow(len(self.context)):
        self.context = self.context[-5:]  # обрізаємо
        print("⚠️ Контекст обрізано запобіжником")
    
    # запобіжник: перевірка rate limit
    if self.safeguards.check_rate_limit(self.last_active):
        return "Зачекай секунду, я ще не готовий."
    
    # далі звичайна логіка
    self.last_active = time.time()
    self.context.append({"role": "user", "content": user_input})
    response = self._generate_response(user_input)
    self.context.append({"role": "assistant", "content": response})
    
    return response

