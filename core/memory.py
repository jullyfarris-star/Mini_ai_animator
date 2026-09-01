# core/memory.py
import sqlite3
import json
import numpy as np
from pathlib import Path
from sentence_transformers import SentenceTransformer
from rank_bm25 import BM25Okapi
import faiss
from typing import List, Dict, Tuple

class HybridRAG:
    def __init__(self, db_path: str = "data/vector_store/ai_mini.db"):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(str(self.db_path), check_same_thread=False)
        self.embed_model = SentenceTransformer("all-MiniLM-L6-v2")
        self.dim = 384
        self._init_tables()
        self._load_or_build_index()  # faiss індекс для швидкості
        self.bm25_index = None
        self._build_bm25_index()

    def _init_tables(self):
        c = self.conn.cursor()
        c.execute("""
            CREATE TABLE IF NOT EXISTS documents (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT, source TEXT, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        c.execute("""
            CREATE TABLE IF NOT EXISTS chunks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                document_id INTEGER,
                content TEXT NOT NULL,
                chunk_index INTEGER,
                embedding BLOB,
                metadata TEXT,
                relevance_score REAL DEFAULT 1.0   -- для самонавчання
            )
        """)
        self.conn.commit()

    def _load_or_build_index(self):
        # Завантажуємо всі ембедінги
        rows = self.conn.execute("SELECT id, embedding FROM chunks").fetchall()
        if not rows:
            self.faiss_index = None
            self.chunk_ids = []
            return
        
        ids, embs = [], []
        for rid, blob in rows:
            ids.append(rid)
            embs.append(np.frombuffer(blob, dtype=np.float32))
        embs = np.vstack(embs).astype(np.float32)
        # Нормалізація для косинусної схожості (inner product)
        faiss.normalize_L2(embs)
        
        self.faiss_index = faiss.IndexFlatIP(self.dim)  # IP = Inner Product (косинус)
        self.faiss_index.add(embs)
        self.chunk_ids = ids
        self._all_embeddings = embs

    def _build_bm25_index(self):
        rows = self.conn.execute("SELECT id, content FROM chunks").fetchall()
        if not rows:
            self.bm25_index = None
            self.bm25_ids = []
            return
        tokenized = [content.lower().split() for _, content in rows]
        self.bm25_index = BM25Okapi(tokenized)
        self.bm25_ids = [rid for rid, _ in rows]

    def add_document(self, title: str, source: str, chunks: List[Tuple[int, str, dict]]):
        cur = self.conn.cursor()
        cur.execute("INSERT INTO documents (title, source) VALUES (?, ?)", (title, source))
        doc_id = cur.lastrowid
        for idx, content, meta in chunks:
            emb = self.embed_model.encode(content, convert_to_numpy=True).astype(np.float32)
            cur.execute(
                "INSERT INTO chunks (document_id, content, chunk_index, embedding, metadata) VALUES (?, ?, ?, ?, ?)",
                (doc_id, content, idx, emb.tobytes(), json.dumps(meta) if meta else None)
            )
        self.conn.commit()
        # Перебудова індексів (для MVP — просто перезавантажуємо)
        self._load_or_build_index()
        self._build_bm25_index()

    def search(self, query: str, top_k: int = 5, alpha: float = 0.5) -> List[Dict]:
        """
        Гібридний пошук: поєднує векторний пошук і BM25.
        alpha — вага для векторів (1 - alpha для BM25).
        """
        # 1. Векторний пошук (FAISS)
        if self.faiss_index is None or self.faiss_index.ntotal == 0:
            vec_scores = []
        else:
            q_emb = self.embed_model.encode(query, convert_to_numpy=True).astype(np.float32)
            faiss.normalize_L2(q_emb.reshape(1, -1))
            distances, indices = self.faiss_index.search(q_emb.reshape(1, -1), min(top_k*3, self.faiss_index.ntotal))
            vec_scores = {self.chunk_ids[i]: float(distances[0][idx]) for idx, i in enumerate(indices[0])}

        # 2. Пошук BM25
        if self.bm25_index is None or not self.bm25_ids:
            bm25_scores = {}
        else:
            tokenized_query = query.lower().split()
            scores = self.bm25_index.get_scores(tokenized_query)
            # Нормалізуємо від 0 до 1
            if scores:
                max_s = max(scores)
                bm25_scores = {rid: (s / max_s) for rid, s in zip(self.bm25_ids, scores) if s > 0}
            else:
                bm25_scores = {}

        # 3. Reciprocal Rank Fusion (RRF)
        # Об'єднуємо всі унікальні ID
        all_ids = set(vec_scores.keys()) | set(bm25_scores.keys())
        if not all_ids:
            return []
        
        # Ранжуємо кожен список окремо
        vec_ranked = sorted(vec_scores.items(), key=lambda x: x[1], reverse=True)
        bm25_ranked = sorted(bm25_scores.items(), key=lambda x: x[1], reverse=True)
        
        # Словник позицій
        vec_pos = {rid: i+1 for i, (rid, _) in enumerate(vec_ranked)}
        bm25_pos = {rid: i+1 for i, (rid, _) in enumerate(bm25_ranked)}
        
        # RRF: score = sum(1 / (k + rank))
        k = 60
        fused = {}
        for rid in all_ids:
            v_score = 1 / (k + vec_pos.get(rid, 1000))
            b_score = 1 / (k + bm25_pos.get(rid, 1000))
            fused[rid] = (alpha * v_score) + ((1 - alpha) * b_score)
        
        # Сортуємо за fused score
        sorted_ids = sorted(fused.items(), key=lambda x: x[1], reverse=True)[:top_k]
        
        # 4. Витягуємо дані з БД
        result = []
        for rid, score in sorted_ids:
            row = self.conn.execute("SELECT content, metadata, relevance_score FROM chunks WHERE id=?", (rid,)).fetchone()
            if row:
                result.append({
                    "chunk_id": rid,
                    "content": row[0],
                    "metadata": json.loads(row[1]) if row[1] else {},
                    "hybrid_score": score,
                    "relevance_score": row[2]  # для самонавчання
                })
        return result

    def update_relevance(self, chunk_id: int, delta: float):
        """Оновлює вагу чанка (для самонавчання)"""
        self.conn.execute("UPDATE chunks SET relevance_score = relevance_score + ? WHERE id=?", (delta, chunk_id))
        self.conn.commit()

