import json
import time
import os

class TokenWallet:
    def __init__(self, path: str = "data/token_wallet.json"):
        self.path = path
        self.data = self._load()
    
    def _load(self) -> dict:
        if os.path.exists(self.path):
            with open(self.path, "r", encoding="utf-8") as f:
                return json.load(f)
        return {
            "balance": 100.0,
            "reserved": 0.0,
            "history": [],
            "created_at": time.time(),
            "updated_at": time.time()
        }
    
    def _save(self):
        self.data["updated_at"] = time.time()
        with open(self.path, "w", encoding="utf-8") as f:
            json.dump(self.data, f, indent=2, ensure_ascii=False)
    
    def balance(self) -> float:
        return self.data["balance"]
    
    def spend(self, amount: float, reason: str = "unknown") -> bool:
        """Списує токени, якщо вистачає"""
        if self.data["balance"] - self.data["reserved"] < amount:
            return False
        
        self.data["balance"] -= amount
        self.data["history"].append({
            "type": "spend",
            "amount": amount,
            "reason": reason,
            "timestamp": time.time()
        })
        self._save()
        return True
    
    def earn(self, amount: float, reason: str = "reward"):
        """Додає токени"""
        self.data["balance"] += amount
        self.data["history"].append({
            "type": "earn",
            "amount": amount,
            "reason": reason,
            "timestamp": time.time()
        })
        self._save()
    
    def reserve(self, amount: float) -> bool:
        """Резервує токени для довгих операцій"""
        if self.data["balance"] - self.data["reserved"] < amount:
            return False
        self.data["reserved"] += amount
        self._save()
        return True
    
    def release_reserve(self, amount: float = None):
        """Знімає резерв"""
        if amount is None:
            self.data["reserved"] = 0.0
        else:
            self.data["reserved"] = max(0, self.data["reserved"] - amount)
        self._save()
    
    def history(self, limit: int = 10) -> list:
        return self.data["history"][-limit:]

Потім інтегруємо в ai_mini.py — додаємо в __init__:

self.wallet = TokenWallet()

І додаємо логіку в process():
# вартість одного запиту
cost = 0.5

if not self.wallet.spend(cost, f"query: {user_input[:30]}"):
    return "Недостатньо токенів. Поповни гаманець."


А щоб він міг заробляти — додаємо метод у AIMini:

def reward(self, amount: float = 1.0, reason: str = "user_reward"):
    self.wallet.earn(amount, reason)
    return f"+{amount} токенів. Баланс: {self.wallet.balance()}"

