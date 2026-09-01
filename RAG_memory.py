RAG модуль памʼяті 

# core/memory.py
import sqlite3
import json
import numpy as np
from pathlib import Path
from sentence_transformers import SentenceTransformer

class MemoryBank:
    def __init__(self, db_path="data/vector_store/ai_mini.db"):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(str(self.db_path), check_same_thread=False)
        self.model = SentenceTransformer("all-MiniLM-L6-v2")
        self.dim = 384
        self._init_tables()

    def _init_tables(self):
        c = self.conn.cursor()
        c.execute("""
            CREATE TABLE IF NOT EXISTS documents (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT,
                source TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        c.execute("""
            CREATE TABLE IF NOT EXISTS chunks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                document_id INTEGER,
                content TEXT NOT NULL,
                chunk_index INTEGER,
                embedding BLOB,
                metadata TEXT
            )
        """)
        self.conn.commit()

    def add_document(self, title, source, chunks):
        """chunks: list of (chunk_index, content, metadata_dict)"""
        cur = self.conn.cursor()
        cur.execute("INSERT INTO documents (title, source) VALUES (?, ?)", (title, source))
        doc_id = cur.lastrowid
        for idx, content, meta in chunks:
            emb = self.model.encode(content, convert_to_numpy=True)
            cur.execute(
                "INSERT INTO chunks (document_id, content, chunk_index, embedding, metadata) VALUES (?, ?, ?, ?, ?)",
                (doc_id, content, idx, emb.tobytes(), json.dumps(meta) if meta else None)
            )
        self.conn.commit()
        return doc_id

    def search(self, query, top_k=5):
        q_emb = self.model.encode(query, convert_to_numpy=True)
        rows = self.conn.execute("SELECT id, content, embedding, metadata FROM chunks").fetchall()
        if not rows:
            return []
        ids, contents, blobs, metas = [], [], [], []
        for r in rows:
            ids.append(r[0])
            contents.append(r[1])
            blobs.append(r[2])
            metas.append(r[3])
        embs = np.vstack([np.frombuffer(b, dtype=np.float32) for b in blobs])
        # нормалізація
        qn = q_emb / (np.linalg.norm(q_emb) + 1e-10)
        embs_n = embs / (np.linalg.norm(embs, axis=1, keepdims=True) + 1e-10)
        sims = (embs_n @ qn).reshape(-1)
        top_idx = np.argsort(-sims)[:top_k]
        return [{"chunk_id": ids[i], "content": contents[i], "score": float(sims[i]), "metadata": metas[i]} for i in top_idx]

    def log(self, module, action, detail=None, success=True):
        # просте логування – можна додати окрему таблицю
        pass

    def get_recent(self, count=10):
        # повертає останні додані чанки (для демонстрації)
        rows = self.conn.execute("SELECT content FROM chunks ORDER BY id DESC LIMIT ?", (count,)).fetchall()
        return [type('Entry', (), {'content': r[0]}) for r in rows]




4 юуло 

5 запуск 

# scripts/run_agent.py
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.agent import AIMini

def main():
    agent = AIMini()
    print("\n🤖 AI-Mini запущено! Пиши 'вихід' для виходу.\n")
    while True:
        user = input("🧑 Ти: ").strip()
        if user.lower() in ("вихід", "exit", "quit"):
            print("👋 Бувай!")
            break
        if not user:
            continue
        reply = agent.process(user)
        print(f"🤖 AI: {reply}\n")

if __name__ == "__main__":
    main()



6. Наповнення RAG 

# scripts/seed_data.py
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.memory import MemoryBank

def chunk_text(text, chunk_size=200, overlap=50):
    words = text.split()
    chunks = []
    i = 0
    idx = 0
    while i < len(words):
        chunk = " ".join(words[i:i+chunk_size])
        chunks.append((idx, chunk, None))
        i += chunk_size - overlap
        idx += 1
    return chunks

def main():
    mb = MemoryBank()
    doc1 = "AI-Mini – це легкий агент з гібридною логікою. Він використовує RAG, пам'ять у SQLite, та модульну архітектуру."
    doc2 = "Запобіжники контролюють вильоти, а формула ваги вирішує, чи варто витрачати токени на відповідь."
    mb.add_document("Про AI-Mini", "seed", chunk_text(doc1))
    mb.add_document("Безпека", "seed", chunk_text(doc2))
    print("✅ База пам'яті наповнена прикладами.")

if __name__ == "__main__":
    main()

