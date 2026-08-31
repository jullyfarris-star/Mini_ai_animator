import json
import os
import re

class RAGModule:
    def __init__(self, data_path: str = "data/"):
        self.data_path = data_path
        self.index = self._build_index()
    
    def _build_index(self) -> dict:
        """Сканує /data і створює простий індекс: слово -> список файлів"""
        index = {}
        for root, _, files in os.walk(self.data_path):
            for file in files:
                if file.endswith(".json") or file.endswith(".txt"):
                    path = os.path.join(root, file)
                    with open(path, "r", encoding="utf-8") as f:
                        content = f.read()
                    words = set(re.findall(r'\w+', content.lower()))
                    for word in words:
                        if word not in index:
                            index[word] = []
                        index[word].append(path)
        return index
    
    def search(self, query: str, top_k: int = 3) -> list:
        """Повертає топ-k файлів, які містять слова із запиту"""
        words = re.findall(r'\w+', query.lower())
        scores = {}
        for word in words:
            for path in self.index.get(word, []):
                scores[path] = scores.get(path, 0) + 1
        sorted_paths = sorted(scores, key=scores.get, reverse=True)
        return sorted_paths[:top_k]
    
    def load_context(self, path: str) -> str:
        """Завантажує вміст файлу для передачі в AI-mini"""
        with open(path, "r", encoding="utf-8") as f:
            return f.read()

Потім інтегруємо це в ai_mini.py — додаємо рядок у __init__:
self.rag = RAGModule()

І в _generate_response — перевірку: якщо користувач питає про знання з бібліотеки, AI-mini робить запит у RAG і підставляє знайдений контекст.


Крок 5: Тестування та оптимізація

Створюємо файл scripts/test_runner.py:


from core.ai_mini import AIMini
from core.rag import RAGModule

# тест 1: запуск ядра
agent = AIMini()
assert agent.status()["state"] == "stable"
print("✅ Ядро запустилось")

# тест 2: обробка повідомлення
resp = agent.process("Привіт, Кубе")
print(f"✅ Відповідь: {resp}")

# тест 3: RAG-пошук
rag = RAGModule()
results = rag.search("токени")
print(f"✅ RAG знайшов: {results}")

# тест 4: перевірка контексту
assert len(agent.context) == 2
print("✅ Контекст зберігається")

print("🎉 Усі тести пройдено")




Ось Крок 6: Запобіжники (safeguards).

Створюємо файл core/safeguards. py

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

