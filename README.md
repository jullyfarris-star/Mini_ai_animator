1- загальна структура 

ai-mini/
├── config/
│   ├── cube_dna.json          # базова конфігурація
│   └── safeguards_config.json # налаштування запобіжників
├── core/
│   ├── __init__.py
│   ├── agent.py               # головний клас AIMini
│   ├── memory.py              # SQLite + векторний пошук (RAG)
│   ├── black_box.py           # чорна скриня + формула
│   ├── weight.py              # формула ваги
│   ├── safeguards.py          # запобіжники (локальні + системні)
│   ├── initiative.py          # ініціатива (сам може писати)
│   ├── language.py            # мовна підтримка
│   ├── photo_learner.py       # навчання по фото
│   ├── billiard.py            # фізичний двигун більярду
│   └── network_grid.py        # сітка (для майбутньої нейромережі)
├── data/
│   ├── vector_store/
│   │   └── ai_mini.db         # SQLite з ембедінгами
│   ├── learned/               # збережені знання з фото
│   └── token_wallet.json      # гаманець токенів
├── scripts/
│   ├── seed_data.py           # наповнення RAG
│   ├── run_agent.py           # запуск агента
│   └── test_agent.py          # тести
└── requirements.txt

requiremnts.txt

sentence-transformers==2.2.2
numpy



ai-mini/
├── config/cube_dna.json
├── core/
│   ├── agent.py          # оновлений
│   ├── llm.py            # НОВИЙ: підключення трансформера
│   ├── memory.py         # ОНОВЛЕНИЙ: гібридний RAG (Vector + BM25)
│   ├── token_wallet.py   # ТВІЙ: гаманець токенів
│   ├── learner.py        # НОВИЙ: самонавчання на фідбеку
│   ├── weight.py         # твій (формула)
│   ├── safeguards.py     # твій (запобіжники)
│   └── ...
├── data/...
└── requirements.txt      # оновлений

1. Структура папок

mkdir -p ai-mini/{config,core,data/vector_store,scripts}


2. Файли, які треба створити

requirements.txt


sentence-transformers==2.2.2
numpy
tqdm


data/vector_store/schema.sql

CREATE TABLE IF NOT EXISTS documents (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT,
    source TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS chunks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    document_id INTEGER REFERENCES documents(id),
    content TEXT NOT NULL,
    chunk_index INTEGER,
    embedding BLOB,
    metadata TEXT
);

CREATE TABLE IF NOT EXISTS model_config (
    id INTEGER PRIMARY KEY,
    model_name TEXT NOT NULL,
    dimensions INTEGER NOT NULL,
    active BOOLEAN DEFAULT 1
);

INSERT OR IGNORE INTO model_config (id, model_name, dimensions, active)
VALUES (1, 'all-MiniLM-L6-v2', 384, 1);



core/__init__.py — порожній файл

core/embedding_store.py

import sqlite3
import numpy as np
from sentence_transformers import SentenceTransformer
from typing import List, Tuple, Optional

def float32_to_blob(floats):
    return floats.astype(np.float32).tobytes()

def blob_to_float32(blob, dims):
    return np.frombuffer(blob, dtype=np.float32).reshape(-1, dims)

class EmbeddingStore:
    def __init__(self, db_path, model_name="all-MiniLM-L6-v2"):
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self.model = SentenceTransformer(model_name)
        cfg = self.conn.execute("SELECT dimensions FROM model_config WHERE active=1 LIMIT 1").fetchone()
        self.dimensions = cfg[0] if cfg else 384

    def add_document(self, title, source, chunks):
        cur = self.conn.cursor()
        cur.execute("INSERT INTO documents (title, source) VALUES (?, ?)", (title, source))
        doc_id = cur.lastrowid
        for idx, content, metadata in chunks:
            emb = self.model.encode(content, convert_to_numpy=True)
            cur.execute(
                "INSERT INTO chunks (document_id, content, chunk_index, embedding, metadata) VALUES (?, ?, ?, ?, ?)",
                (doc_id, content, idx, float32_to_blob(emb), metadata)
            )
        self.conn.commit()
        return doc_id

    def similarity_search(self, query, top_k=5):
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
        embs = np.vstack([blob_to_float32(b, self.dimensions) for b in blobs])
        qn = q_emb / (np.linalg.norm(q_emb) + 1e-10)
        embs_n = embs / (np.linalg.norm(embs, axis=1, keepdims=True) + 1e-10)
        sims = (embs_n @ qn).reshape(-1)
        top_idx = np.argsort(-sims)[:top_k]
        return [{"chunk_id": ids[i], "content": contents[i], "score": float(sims[i]), "metadata": metas[i]} for i in top_idx]

