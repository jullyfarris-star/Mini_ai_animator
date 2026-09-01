# core/learner.py
import json
import random
from collections import deque

class AdaptiveLearner:
    def __init__(self, memory_size: int = 100):
        self.experience_buffer = deque(maxlen=memory_size)  # (query, chunks_used, feedback)
        self.prompt_template = """
Ти — AI-Міні. Ось контекст із пам'яті:
{context}

Користувач: {query}
Відповідь (твоя попередня): {last_reply}
Зворотний зв'язок: {feedback}
Якщо {feedback} позитивний — продовжуй у тому ж дусі. Якщо негативний — виправся.
Нова відповідь:
"""
    
    def store_experience(self, query: str, chunks: list, feedback: bool):
        """Зберігає досвід: chunks — список id чанків, feedback — True (👍) або False (👎)"""
        self.experience_buffer.append({
            "query": query,
            "chunk_ids": [c["chunk_id"] for c in chunks],
            "feedback": feedback
        })
        # Зберігаємо в файл для довготривалої пам'яті
        with open("data/learning_log.json", "a") as f:
            json.dump({"time": time.time(), "query": query, "feedback": feedback}, f)
            f.write("\n")

    def update_weights(self, memory_bank):
        """Оновлює ваги чанків на основі збереженого досвіду"""
        for exp in self.experience_buffer:
            delta = 0.5 if exp["feedback"] else -0.3
            for cid in exp["chunk_ids"]:
                memory_bank.update_relevance(cid, delta)
        # Очищаємо буфер після оновлення
        self.experience_buffer.clear()

    def improve_prompt(self, query: str, context: str, last_reply: str, feedback: bool):
        """Генерує покращений промпт для наступного разу (мета-навчання)"""
        feedback_text = "позитивний (👍)" if feedback else "негативний (👎)"
        return self.prompt_template.format(
            context=context,
            query=query,
            last_reply=last_reply,
            feedback=feedback_text
        )

