Таблиця документів
CREATE TABLE documents (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT,
    source TEXT,           -- звідки взято
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Чанки з ембедінгами
CREATE TABLE chunks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    document_id INTEGER REFERENCES documents(id),
    content TEXT NOT NULL,
    chunk_index INTEGER,   -- порядок у документі
    embedding BLOB,        -- вектор (float32 array)
    metadata TEXT          -- JSON з додатковою інфою
);

-- Індекс для векторного пошуку (sqlite-vec)
CREATE VIRTUAL TABLE vec_chunks USING vec0(
    chunk_id INTEGER,
    embedding float[384]   -- розмірність ембедінгу
);


Як шукати:

embedding = get_embedding("запит користувача")
results = conn.execute("""
    SELECT c.content, c.metadata, distance
    FROM vec_chunks v
    JOIN chunks c ON c.id = v.chunk_id
    WHERE v.embedding MATCH ?
    ORDER BY distance
    LIMIT 5
""", (embedding,))




Плюси SQL-підходу:
• не треба вчити окрему векторну БД
• легко робити гібридний пошук (вектори + SQL-фільтри)
• бекапи — звичайний дамп SQL
• менше залежностей у requirements.txt

