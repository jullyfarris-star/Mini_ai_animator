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

