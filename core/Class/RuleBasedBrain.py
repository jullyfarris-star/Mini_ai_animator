import re
from typing import Optional


class RuleBasedBrain:
    """
    Розумніша rule-based логіка замість echo.
    Розпізнає намір (intent) і відповідає відповідною мовою.
    Не LLM — просто патерни + трохи евристики, але вже осмислено.
    """

    STOPWORDS = {
        "uk": {"я", "ти", "він", "вона", "воно", "ми", "ви", "вони", "це", "той", "цей",
               "і", "а", "але", "чи", "як", "що", "де", "коли", "чому", "не", "так", "ні",
               "для", "від", "до", "на", "по", "з", "у", "в", "за", "про", "мене", "тебе"},
        "en": {"i", "you", "he", "she", "it", "we", "they", "this", "that", "and", "or",
               "but", "how", "what", "where", "when", "why", "not", "yes", "no",
               "for", "from", "to", "on", "in", "at", "about", "me", "the", "a", "is"},
        "ko": set(),
    }

    PATTERNS = {
        "greeting": {
            "uk": [r"\bпривіт\b", r"\bвітаю\b", r"\bхай\b", r"\bдоброго\b", r"\bдобрий день\b"],
            "en": [r"\bhi\b", r"\bhello\b", r"\bhey\b", r"\bgood morning\b"],
            "ko": [r"안녕"],
        },
        "farewell": {
            "uk": [r"\bбувай\b", r"\bпока\b", r"\bдо зустрічі\b", r"\bвихід\b"],
            "en": [r"\bbye\b", r"\bgoodbye\b", r"\bsee you\b"],
            "ko": [r"안녕히"],
        },
        "identity": {
            "uk": [r"хто ти", r"як тебе звати", r"як тебе зват"],
            "en": [r"who are you", r"what.?s your name"],
            "ko": [r"누구"],
        },
        "capabilities": {
            "uk": [r"що ти вмієш", r"що вмієш", r"що ти можеш", r"допомож"],
            "en": [r"what can you do", r"help me", r"\bhelp\b"],
            "ko": [r"뭐 할 수"],
        },
        "status": {
            "uk": [r"як справи", r"який твій стан", r"статус"],
            "en": [r"how are you", r"what.?s your status", r"\bstatus\b"],
            "ko": [r"상태"],
        },
        "thanks": {
            "uk": [r"дяк", r"дякую"],
            "en": [r"\bthanks\b", r"\bthank you\b"],
            "ko": [r"고마"],
        },
        "search": {
            "uk": [r"знайди", r"пошук", r"бібліотек"],
            "en": [r"\bfind\b", r"\bsearch\b"],
            "ko": [r"찾"],
        },
    }

    REPLIES = {
        "greeting": {
            "uk": "Привіт! Я Куб. Чим можу допомогти?",
            "en": "Hi! I'm Cube. How can I help?",
            "ko": "안녕하세요! 저는 큐브입니다.",
        },
        "farewell": {
            "uk": "Бувай! Звертайся, якщо що.",
            "en": "Bye! Come back anytime.",
            "ko": "안녕히 가세요!",
        },
        "identity": {
            "uk": "Я Куб — гібридний AI-mini агент з пам'яттю, гаманцем токенів і запобіжниками.",
            "en": "I'm Cube — a hybrid AI-mini agent with memory, a token wallet, and safeguards.",
            "ko": "저는 큐브입니다.",
        },
        "capabilities": {
            "uk": "Я вмію: шукати в бібліотеці (data/), рахувати прості приклади, тримати контекст розмови і слідкувати за балансом токенів.",
            "en": "I can: search the library (data/), do simple math, keep conversation context, and track token balance.",
            "ko": "저는 도서관 검색, 간단한 계산을 할 수 있어요.",
        },
        "thanks": {
            "uk": "Нема за що! 🙂",
            "en": "You're welcome! 🙂",
            "ko": "천만에요!",
        },
        "no_search_results": {
            "uk": "Пошукав у бібліотеці, але нічого не знайшов.",
            "en": "I searched the library but found nothing.",
            "ko": "찾지 못했어요.",
        },
        "found": {
            "uk": "Знайшов у бібліотеці: {items}",
            "en": "Found in the library: {items}",
            "ko": "찾았어요: {items}",
        },
        "fallback": {
            "uk": "Почула тебе. Про що конкретно хочеш дізнатись — {hint}?",
            "en": "I heard you. What specifically about — {hint}?",
            "ko": "들었어요.",
        },
    }

    def detect_intent(self, text: str, lang: str) -> Optional[str]:
        lowered = text.lower()
        for intent, by_lang in self.PATTERNS.items():
            patterns = by_lang.get(lang, []) + by_lang.get("uk", [])
            for pat in patterns:
                if re.search(pat, lowered):
                    return intent
        return None

    def try_math(self, text: str) -> Optional[str]:
        """Проста арифметика: '2 + 2', 'скільки буде 5 * 3'"""
        match = re.search(r"(-?\d+(?:\.\d+)?)\s*([+\-*/])\s*(-?\d+(?:\.\d+)?)", text)
        if not match:
            return None
        a, op, b = match.groups()
        a, b = float(a), float(b)
        try:
            if op == "+":
                result = a + b
            elif op == "-":
                result = a - b
            elif op == "*":
                result = a * b
            elif op == "/":
                if b == 0:
                    return "На нуль ділити не можна 🙂"
                result = a / b
            else:
                return None
            if result == int(result):
                result = int(result)
            return f"{a} {op} {b} = {result}"
        except (ValueError, ZeroDivisionError):
            return None

    def extract_keywords(self, text: str, lang: str, limit: int = 3) -> list:
        words = re.findall(r"\w+", text.lower())
        stop = self.STOPWORDS.get(lang, set())
        keywords = [w for w in words if w not in stop and len(w) > 2]
        return keywords[:limit]

    def respond(self, text: str, lang: str, rag_module=None) -> str:
        lang = lang if lang in ("uk", "en", "ko") else "uk"

        intent = self.detect_intent(text, lang)

        if intent == "search" and rag_module is not None:
            found = rag_module.search(text)
            if found:
                return self.REPLIES["found"][lang].format(items=", ".join(found))
            return self.REPLIES["no_search_results"][lang]

        if intent and intent in self.REPLIES:
            return self.REPLIES[intent][lang]

        math_result = self.try_math(text)
        if math_result:
            return math_result

        keywords = self.extract_keywords(text, lang)
        hint = ", ".join(keywords) if keywords else text[:40]
        return self.REPLIES["fallback"][lang].format(hint=hint)



Схема для векторного сховища 

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
