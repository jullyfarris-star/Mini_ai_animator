"""
AIMini - Основний клас АІ-агента
Об'єднує: пам'ять (RAG), LLM, токени, ваги, запобіжники
"""
import time
import json
from pathlib import Path
from typing import Dict, List, Optional

from .memory import HybridRAG
from .llm import LocalLLM
from .token_wallet import TokenWallet
from .learner import AdaptiveLearner
from .weight import WeightFormula
from .safeguards import SystemSafeguard


class AIMini:
    """
    Основний клас АІ-Міні агента.
    
    Функціонал:
    - Гібридна пам'ять (RAG: Vector + BM25)
    - Локальний LLM (трансформер)
    - Управління токенами
    - Формула ваги дій
    - Адаптивне навчання
    - Системні запобіжники
    """
    
    def __init__(self, config_path: Optional[str] = None, model_name: str = "Qwen/Qwen2-1.5B-Instruct"):
        """
        Ініціалізація AIMini
        
        Args:
            config_path: Шлях до config/cube_dna.json (опціонально)
            model_name: Назва LLM моделі
        """
        self.config = self._load_config(config_path) if config_path else {}
        
        # Основні модулі
        self.memory = HybridRAG()
        self.llm = LocalLLM(model_name=model_name)
        self.wallet = TokenWallet()
        self.learner = AdaptiveLearner()
        self.weight = WeightFormula()
        self.safeguard = SystemSafeguard()
        
        # Стан
        self.context: List[Dict] = []  # історія діалогу
        self.last_reply = ""
        self.last_chunks = []
        self.last_active = time.time()
    
    def _load_config(self, config_path: str) -> Dict:
        """Завантажити конфіг DNA"""
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"⚠️ Не вдалось завантажити конфіг {config_path}: {e}")
            return {}
    
    def process(self, user_input: str) -> str:
        """
        Основний метод обробки запиту користувача
        
        Процес:
        1. Перевірка токенів
        2. Пошук у пам'яті (RAG)
        3. Розрахунок ваги дії (чи варто витрачати LLM?)
        4. Генерація відповіді
        5. Збереження в пам'ять
        6. Зворотний зв'язок
        """
        self.last_active = time.time()
        
        # 1. Перевірка токенів (кожен запит коштує 0.5)
        if not self.wallet.spend(0.5, f"query: {user_input[:30]}"):
            return "⛔ Недостатньо токенів. Поповни гаманець командою '/поповнити 10'."
        
        # 2. Гібридний пошук (RAG)
        rag_results = self.memory.search(user_input, top_k=5, alpha=0.6)
        self.last_chunks = rag_results
        context_str = "\n".join(
            f"[{i+1}] {r['content'][:100]}" 
            for i, r in enumerate(rag_results)
        ) if rag_results else "(немає даних у пам'яті)"
        
        # 3. Формула ваги (чи варто використовувати LLM?)
        action_data = {
            "complexity": self._estimate_complexity(user_input),
            "is_novel": self._is_novel(user_input),
            "is_urgent": self._is_urgent(user_input),
            "context_size": len(self.context),
            "token_balance": self.wallet.balance(),
            "token_cost": 0.5
        }
        
        decision = self.weight.calculate(action_data)
        
        if not decision["should_act"]:
            reply = f"⚖️ Вага {decision['weight']} – замало для дії. Запитай щось вагоміше.\n\n📌 Пам'ять:\n{context_str}"
        else:
            # 4. Використовуємо LLM для складних запитів
            prompt = f"Контекст з пам'яті:\n{context_str}\n\nЗапит: {user_input}"
            reply = self.llm.generate(prompt, max_new_tokens=300)
        
        # 5. Зберігаємо в контекст
        self.context.append({"role": "user", "content": user_input})
        self.context.append({"role": "assistant", "content": reply})
        if len(self.context) > 20:  # Не більше 20 повідомлень
            self.context = self.context[-20:]
        self.last_reply = reply
        
        # 6. Записуємо подію в RAG (щоб агент пам'ятав діалог)
        self.memory.add_document(
            title=f"Chat_{int(time.time())}",
            source="conversation",
            chunks=[(0, f"User: {user_input}\nAI: {reply}", {"type": "dialogue"})]
        )
        
        return reply
    
    def feedback(self, is_positive: bool) -> str:
        """
        Зворотний зв'язок від користувача (👍 або 👎)
        Агент вчиться на прикладах
        """
        if not self.last_chunks:
            return "Немає даних для оцінки."
        
        # Записуємо досвід
        self.learner.store_experience(
            query=self.context[-2]["content"] if len(self.context) >= 2 else "",
            chunks=self.last_chunks,
            feedback=is_positive
        )
        
        # Оновлюємо ваги чанків у пам'яті
        self.learner.update_weights(self.memory)
        
        # Нагорода за фідбек
        reward = 2.0 if is_positive else 0.5
        self.wallet.earn(reward, "feedback")
        
        return f"👍 Дякую! Я запам'ятав це." if is_positive else "👎 Виправлюсь наступного разу."
    
    def status(self) -> Dict:
        """Отримати статус агента"""
        try:
            memory_chunks = self.memory.conn.execute("SELECT COUNT(*) FROM chunks").fetchone()[0]
        except:
            memory_chunks = 0
        
        return {
            "tokens": self.wallet.balance(),
            "context_len": len(self.context),
            "memory_chunks": memory_chunks,
            "faiss_size": self.memory.faiss_index.ntotal if self.memory.faiss_index else 0,
            "last_active": self.last_active,
            "uptime": time.time() - self.last_active
        }
    
    # === Допоміжні методи ===
    
    def _estimate_complexity(self, text: str) -> int:
        """Оцінити складність запиту (1-10)"""
        length = len(text)
        if length < 20:
            return 2
        elif length < 100:
            return 5
        else:
            return 8
    
    def _is_novel(self, text: str) -> bool:
        """Перевірити, чи новий запит"""
        keywords = set(text.lower().split())
        for entry in self.context:
            if entry["role"] == "user":
                prev_keywords = set(entry["content"].lower().split())
                if keywords & prev_keywords:  # Якщо є спільні слова
                    return False
        return True
    
    def _is_urgent(self, text: str) -> bool:
        """Перевірити терміновість запиту"""
        urgent_words = ["терміново", "швидко", "строк", "дедлайн", "urgent", "now", "срочно", "АСАП"]
        return any(word in text.lower() for word in urgent_words)
