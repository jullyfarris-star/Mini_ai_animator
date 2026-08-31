# core/agent.py
import time
import json
from pathlib import Path

from .llm import LocalLLM
from .memory import HybridRAG
from .token_wallet import TokenWallet
from .learner import AdaptiveLearner
from .weight import WeightFormula  # твій клас
from .safeguards import SystemSafeguard  # твій клас

class AIMini:
    def __init__(self):
        self.memory = HybridRAG()
        self.llm = LocalLLM()  # Завантажує трансформер
        self.wallet = TokenWallet()
        self.learner = AdaptiveLearner()
        self.weight = WeightFormula()
        self.safeguard = SystemSafeguard()
        self.context = []  # історія діалогу
        self.last_reply = ""
        self.last_chunks = []

    def process(self, user_input: str) -> str:
        # 1. Перевірка токенів (кожен запит коштує 0.5)
        if not self.wallet.spend(0.5, f"query: {user_input[:30]}"):
            return "⛔ Недостатньо токенів. Поповни гаманець командою 'поповнити 10'."

        # 2. Гібридний пошук (RAG)
        rag_results = self.memory.search(user_input, top_k=5, alpha=0.6)
        self.last_chunks = rag_results
        context_str = "\n".join(f"[{i+1}] {r['content']}" for i, r in enumerate(rag_results)) if rag_results else "(немає даних)"

        # 3. Формула ваги (чи варто використовувати LLM або відповісти просто)
        action_data = {"complexity": len(user_input), "context_size": len(self.context)}
        if self.weight.calculate(action_data)["should_act"]:
            # Складний запит — використовуємо LLM
            prompt = f"Контекст з пам'яті:\n{context_str}\n\nЗапит користувача: {user_input}"
            reply = self.llm.generate(prompt, max_new_tokens=300)
        else:
            # Простий запит — швидка відповідь
            reply = f"Ось що я знайшов:\n{context_str}\n\nЯкщо хочеш детальніше — запитай розгорнуто."

        # 4. Зберігаємо в контекст
        self.context.append({"role": "user", "content": user_input})
        self.context.append({"role": "assistant", "content": reply})
        if len(self.context) > 10:
            self.context = self.context[-10:]
        self.last_reply = reply

        # 5. Записуємо подію в RAG (щоб агент "пам'ятав" діалог)
        self.memory.add_document(
            title=f"Chat_{int(time.time())}",
            source="conversation",
            chunks=[(0, f"User: {user_input}\nAI: {reply}", {"type": "dialogue"})]
        )
        return reply

    def feedback(self, is_positive: bool):
        """Зворотний зв'язок від користувача (👍 або 👎)"""
        if not self.last_chunks:
            return "Немає даних для оцінки."
        self.learner.store_experience(
            query=self.context[-2]["content"] if len(self.context) >= 2 else "",
            chunks=self.last_chunks,
            feedback=is_positive
        )
        # Оновлюємо ваги чанків
        self.learner.update_weights(self.memory)
        self.wallet.earn(2.0 if is_positive else 0.5, "feedback")  # нагорода за хороший фідбек
        return "👍 Дякую! Я запам'ятав це." if is_positive else "👎 Виправлюсь наступного разу."

    def status(self):
        return {
            "tokens": self.wallet.balance(),
            "context_len": len(self.context),
            "memory_chunks": self.memory.conn.execute("SELECT COUNT(*) FROM chunks").fetchone()[0],
            "faiss_size": self.memory.faiss_index.ntotal if self.memory.faiss_index else 0
        }
