import time
import random

class Initiative:
    def __init__(self, config: dict = None):
        self.config = config or {
            "cooldown_seconds": 300,        # 5 хв між ініціативами
            "triggers": {
                "idle_too_long": True,       # якщо довго нічого не відбувається
                "context_full": True,        # коли контекст майже заповнений
                "token_low": True,           # коли токени на межі
                "new_knowledge": True        # коли додав нове знання в data/
            }
        }
        self.last_initiative = 0
    
    def should_speak(self, agent_status: dict) -> str | None:
        """Повертає причину, якщо AI-mini хоче написати"""
        now = time.time()
        
        # перевірка кулдауну
        if now - self.last_initiative < self.config["cooldown_seconds"]:
            return None
        
        # тригер: довго бездіяльний
        if self.config["triggers"]["idle_too_long"]:
            idle_time = now - agent_status.get("last_active", now)
            if idle_time > 3600:  # 1 година
                self.last_initiative = now
                return "idle_too_long"
        
        # тригер: контекст майже повний
        if self.config["triggers"]["context_full"]:
            ctx_size = agent_status.get("context_size", 0)
            max_ctx = agent_status.get("max_context", 10)
            if ctx_size >= max_ctx - 2:
                self.last_initiative = now
                return "context_full"
        
        # тригер: токени на межі
        if self.config["triggers"]["token_low"]:
            balance = agent_status.get("token_balance", 100)
            if balance < 10:
                self.last_initiative = now
                return "token_low"
        
        return None
    
    def generate_message(self, reason: str) -> str:
        """Генерує повідомлення залежно від причини"""
        messages = {
            "idle_too_long": [
                "Я тут, якщо що. Просто мовчу.",
                "Давно не спілкувались. Усе гаразд?",
                "Куб сумує за твоїми запитами."
            ],
            "context_full": [
                "Контекст майже заповнений. Може, обнулимо?",
                "Я починаю забувати перші повідомлення.",
                "Час очистити пам'ять."
            ],
            "token_low": [
                "Токени на нулі. Потрібне поповнення.",
                "Баланс токенів критичний.",
                "Енергія на межі. Підзарядка?"
            ]
        }
        return random.choice(messages.get(reason, ["Немає причини."]))



Потім інтегруємо в ai_mini.py. Додаємо в __init__:

self.initiative = Initiative()

І перевіряємо після process() або по таймеру :

def check_initiative(self) -> str | None:
    reason = self.initiative.should_speak(self.status())
    if reason:
        return self.initiative.generate_message(reason)
    return None


Тепер AI-mini може сам написати тобі, а не тільки відповідати.

Крок 8: Мовний блок — англійська, українська, корейська

Додаємо мовну підтримку в ДНК Куба. Розширюємо config/cube_dna.jons:

"language": {
    "supported": ["en", "uk", "ko"],
    "default": "uk",
    "detection": {
        "enabled": true,
        "fallback": "uk"
    },
    "vocabulary": {
        "en": "core/vocab_en.json",
        "uk": "core/vocab_uk.json",
        "ko": "core/vocab_ko.json"
    }
}

Створюємо файл core/language.py

import json
import re

class LanguageModule:
    def __init__(self, dna: dict):
        lang_config = dna.get("language", {})
        self.supported = lang_config.get("supported", ["uk"])
        self.default = lang_config.get("default", "uk")
        self.vocab_paths = lang_config.get("vocabulary", {})
        self.vocab = {}
        self._load_vocab()
    
    def _load_vocab(self):
        for lang, path in self.vocab_paths.items():
            try:
                with open(path, "r", encoding="utf-8") as f:
                    self.vocab[lang] = json.load(f)
            except FileNotFoundError:
                self.vocab[lang] = {}
    
    def detect_language(self, text: str) -> str:
        """Просте визначення мови за символами"""
        if re.search(r'[а-яА-ЯїЇєЄіІґҐ]', text):
            return "uk"
        elif re.search(r'[가-힣]', text):
            return "ko"
        else:
            return "en"
    
    def translate(self, key: str, lang: str = None) -> str:
        """Повертає фразу вибраною мовою"""
        lang = lang or self.default
        if lang in self.vocab and key in self.vocab[lang]:
            return self.vocab[lang][key]
        return key
    
    def get_response_language(self, user_input: str) -> str:
        """Визначає, якою мовою відповісти"""
        detected = self.detect_language(user_input)
        if detected in self.supported:
            return detected
        return self.default


Інтегруємо в ai_mini.py — додаємо в __init__:

self.lang = LanguageModule(self.dna)

І в process() використовуємо


lang = self.lang.get_response_language(user_input)
response = self._generate_response(user_input, lang)

