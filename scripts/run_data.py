scripts/seed_data.py

import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from core.embedding_store import EmbeddingStore

DB = os.path.join("data", "vector_store", "ai_mini.db")

def chunk_text(text, size=300, overlap=50):
    tokens = text.split()
    chunks = []
    i = 0
    idx = 0
    while i < len(tokens):
        chunk = " ".join(tokens[i:i+size])
        chunks.append((idx, chunk, None))
        idx += 1
        i += size - overlap
    return chunks

if __name__ == "__main__":
    os.makedirs(os.path.dirname(DB), exist_ok=True)
    store = EmbeddingStore(DB)
    doc1 = "АІміні — це легкий AI-помічник. Він працює на гібридній логіці та використовує RAG для пошуку інформації."
    chunks1 = chunk_text(doc1, size=50, overlap=10)
    store.add_document("Про АІміні", "seed", chunks1)

    doc2 = "Для пошуку використовується косинусна схожість між ембедінгами запиту та чанків."
    chunks2 = chunk_text(doc2, size=50, overlap=10)
    store.add_document("Як працює пошук", "seed", chunks2)

    print("✅ Seed завершено. Додано 2 документи.")



scripts/run.py

import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from core.embedding_store import EmbeddingStore

DB = os.path.join("data", "vector_store", "ai_mini.db")

if __name__ == "__main__":
    store = EmbeddingStore(DB)
    print("🔍 RAG пошук. Напиши 'exit' щоб вийти.")
    while True:
        q = input("Запит: ").strip()
        if q.lower() in ("exit", "quit", "q"):
            break
        results = store.similarity_search(q, top_k=3)
        for r in results:
            print(f"\n📄 Чанк #{r['chunk_id']} | Схожість: {r['score']:.4f}")
            print(r['content'])
        print("---")


3. Запуск

cd ai-mini
python -m venv .venv
source .venv/bin/activate  # або .venv\Scripts\activate
pip install -r requirements.txt

# Ініціалізація БД
sqlite3 data/vector_store/ai_mini.db < data/vector_store/schema.sql

# Наповнення
python scripts/seed_data.py

# Запуск пошуку
python scripts/run.py

Це все. Буквально 5 файлів + термінал — і в тебе готовий RAG на SQLite.

Хочеш, я можу:
• Додати тести (scripts/test_agent.py)
• Написати README.md
• Показати, як додати sqlite-vec (справжній векторний індекс у SQL)
• Перейти до core/agent.py — логіки самого агента?



Ось тобі єдиний файл, який можна запустити одразу:


# ai_mini.py — міні AI-агент з пам'яттю (RAG на SQLite)

import sqlite3
import json
import numpy as np
from pathlib import Path

DB_PATH = "memory.db"

# ---------- SQLite пам'ять ----------
def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS memory (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            content TEXT NOT NULL,
            embedding BLOB,
            created_at TEXT DEFAULT (datetime('now'))
        )
    """)
    conn.commit()
    conn.close()

def save_to_memory(text):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    # простий ембеддинг — частотний вектор слів
    vec = np.zeros(50)
    words = text.lower().split()[:50]
    for i, w in enumerate(words):
        vec[i % 50] += hash(w) % 100 / 100.0
    c.execute("INSERT INTO memory (content, embedding) VALUES (?, ?)",
              (text, vec.tobytes()))
    conn.commit()
    conn.close()
    print(f"  💾 Збережено в пам'ять: {text[:50]}...")

def search_memory(query, top_k=3):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT id, content, embedding FROM memory")
    rows = c.fetchall()
    conn.close()

    if not rows:
        return []

    q_vec = np.zeros(50)
    words = query.lower().split()[:50]
    for i, w in enumerate(words):
        q_vec[i % 50] += hash(w) % 100 / 100.0

    scored = []
    for rid, content, emb_bytes in rows:
        d_vec = np.frombuffer(emb_bytes, dtype=np.float64).copy()
        # косинусна схожість
        dot = np.dot(q_vec, d_vec)
        norm = np.linalg.norm(q_vec) * np.linalg.norm(d_vec)
        sim = dot / norm if norm > 0 else 0
        scored.append((sim, content))

    scored.sort(reverse=True, key=lambda x: x[0])
    return [content for _, content in scored[:top_k]]

# ---------- AI "мізки" ----------
class MiniAI:
    def __init__(self):
        self.name = "AI-Міні"
        init_db()

    def think(self, user_input):
        # 1. Пошук у пам'яті
        memories = search_memory(user_input)
        context = ""
        if memories:
            context = "Ось що я знаю з минулого:\n" + \
                      "\n".join(f"  • {m}" for m in memories)

        # 2. Проста логіка відповіді
        if "як тебе звати" in user_input.lower() or "хто ти" in user_input.lower():
            reply = f"Я {self.name}! 🤖"
        elif "привіт" in user_input.lower() or "хай" in user_input.lower():
            reply = "Привіт! Чим можу допомогти? 😊"
        elif "пам'ятай" in user_input.lower():
            # зберігаємо те, що після "пам'ятай"
            to_save = user_input.lower().split("пам'ятай", 1)[-1].strip()
            if to_save:
                save_to_memory(to_save)
                reply = f"Запам'ятала: {to_save}"
            else:
                reply = "А що саме запам'ятати?"
        elif "що ти пам'ятаєш" in user_input.lower() or "згадай" in user_input.lower():
            mems = search_memory("")
            if mems:
                reply = "Я пам'ятаю:\n" + "\n".join(f"  • {m}" for m in mems)
            else:
                reply = "Поки що нічого не пам'ятаю 🤷"
        else:
            reply = f"Цікаво. {context}\n\nЯ почула: '{user_input}'"

        return reply

# ---------- Запуск ----------
def main():
    ai = MiniAI()
    print(f"\n{'='*50}")
    print(f"  {ai.name} — RAG агент на SQLite")
    print(f"  Пам'ять: {DB_PATH}")
    print(f"{'='*50}")
    print("  Команди:")
    print("    'пам'ятай <текст>' — зберегти в пам'ять")
    print("    'що ти пам'ятаєш'   — показати пам'ять")
    print("    'вихід' / 'exit'    — вийти")
    print()

    while True:
        try:
            user = input("🧑 Ти: ").strip()
            if user.lower() in ("вихід", "exit", "quit"):
                print("👋 Бувай!")
                break
            if not user:
                continue

            reply = ai.think(user)
            print(f"🤖 AI: {reply}\n")

        except KeyboardInterrupt:
            print("\n👋 Бувай!")
            break

if __name__ == "__main__":
    main()

Як запустити:

1. Збережи це як ai_mini.py
2. У терміналі: pip install numpy
3. Запусти: python ai_mini.py

Що вміє:
• Зберігати інфо в SQLite по команді пам'ятай ...
• Шукати в пам'яті за схожістю (векторний пошук)
• Відповідати на прості запитання
• Все в одному файлі — нічого додатково створювати не треба

