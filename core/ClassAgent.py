# core/agent.py
import json
import time
from pathlib import Path
from typing import Optional

from .memory import MemoryBank
from .black_box import BlackBoxFormula, BlackBoxSafeguard
from .weight import WeightFormula
from .safeguards import SystemSafeguard
from .initiative import Initiative
from .language import LanguageModule
from .photo_learner import PhotoLearner
from .billiard import BilliardTable
from .network_grid import NetworkGrid

class AIMini:
    def __init__(self, config_path: str = "config/cube_dna.json"):
        self.config_path = Path(config_path)
        self.dna = self._load_dna()
        self._init_modules()
        self.context = []          # історія діалогу
        self.last_active = time.time()

    def _load_dna(self) -> dict:
        with open(self.config_path, "r", encoding="utf-8") as f:
            return json.load(f)

    def _init_modules(self):
        # Пам'ять (RAG)
        self.memory = MemoryBank(db_path="data/vector_store/ai_mini.db")
        # Ваги
        self.weight = WeightFormula()
        # Чорна скриня
        self.black_box = BlackBoxFormula(dim=2)
        self.bb_safeguard = BlackBoxSafeguard()
        # Системний запобіжник
        self.safeguard = SystemSafeguard()
        # Ініціатива
        self.initiative = Initiative()
        # Мовний модуль
        self.lang = LanguageModule(self.dna)
        # Фотонавчання
        self.photo = PhotoLearner()
        # Більярд
        self.billiard = BilliardTable()
        # Сітка (майбутня нейромережа)
        self.grid = NetworkGrid()
        if len(self.grid.status()["nodes"]) == 0:
            self.grid.grow("transformer")

    def process(self, user_input: str) -> str:
        # 1. Запобіжник: перевірка стану
        if not self.safeguard.check_before("agent"):
            return "⛔ Система заблокована. Запустіть heal() для відновлення."

        # 2. Визначення мови
        lang = self.lang.get_response_language(user_input)

        # 3. Пошук у пам'яті (RAG)
        mem_result = self.memory.search(user_input, top_k=3)
        context_str = ""
        if mem_result:
            context_str = "🔍 Згадую:\n" + "\n".join(f"  • {r['content']}" for r in mem_result)

        # 4. Формула ваги – чи варто витрачати токени?
        action_data = {
            "type": "query",
            "complexity": self._estimate_complexity(user_input),
            "is_novel": self._is_novel(user_input),
            "is_urgent": self._is_urgent(user_input),
            "context_size": len(self.context),
            "token_balance": 100.0  # поки що фіксовано
        }
        decision = self.weight.calculate(action_data)
        if not decision["should_act"]:
            return f"⚖️ Вага {decision['weight']} – замало для дії. Запитай щось вагоміше."

        # 5. Основний генератор відповіді (поки що простий)
        self.context.append({"role": "user", "content": user_input})
        reply = self._generate_response(user_input, context_str, lang)
        self.context.append({"role": "assistant", "content": reply})

        # 6. Записати подію в пам'ять (SQLite)
        self.memory.log("agent", "process", f"reply: {reply[:50]}...")

        # 7. Ініціатива (чи хоче агент щось сказати додатково)
        init_msg = self.initiative.should_speak(self.status())
        if init_msg:
            reply += f"\n\n(До речі: {init_msg})"

        return reply

    def _generate_response(self, user_input: str, context: str, lang: str) -> str:
        # Спрощена логіка – пізніше заміниш на LLM або шаблони
        lower = user_input.lower()
        if "як тебе звати" in lower:
            return "Я AI-Міні! Можна просто Міні 😊"
        elif "привіт" in lower:
            return "Привіт! Радий бачити тебе ✨"
        elif "пам'ятай" in lower:
            # зберігаємо текст у пам'ять (RAG)
            to_save = lower.split("пам'ятай", 1)[-1].strip()
            if to_save:
                self.memory.add_document("user_note", "chat", [(0, to_save, None)])
                return f"Запам'ятав: {to_save}"
            else:
                return "А що саме запам'ятати?"
        elif "що ти пам'ятаєш" in lower:
            mem = self.memory.get_recent(count=5)
            if mem:
                return "Я пам'ятаю:\n" + "\n".join(f"  • {m.content}" for m in mem)
            else:
                return "Поки що нічого не пам'ятаю 🤷"
        else:
            return f"{context}\n\nЯ почув: '{user_input}'"

    def _estimate_complexity(self, text: str) -> int:
        return 2 if len(text) < 20 else 5 if len(text) < 100 else 8

    def _is_novel(self, text: str) -> bool:
        words = set(text.lower().split())
        for entry in self.context:
            if entry["role"] == "user":
                if words & set(entry["content"].lower().split()):
                    return False
        return True

    def _is_urgent(self, text: str) -> bool:
        urgent = ["терміново", "швидко", "строк", "дедлайн", "urgent", "now", "срочно"]
        return any(w in text.lower() for w in urgent)

    def status(self) -> dict:
        return {
            "state": "stable",
            "context_size": len(self.context),
            "last_active": self.last_active,
            "dna_version": self.dna.get("cube_dna", {}).get("version", "0.1")
        }

    def heal(self):
        """Спроба автоматичного відновлення"""
        fixes = self.safeguard.auto_heal(self)
        return fixes

