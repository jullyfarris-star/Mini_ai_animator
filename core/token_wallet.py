# core/token_wallet.py
import json, time, os

class TokenWallet:
    def __init__(self, path: str = "data/token_wallet.json"):
        self.path = path
        self.data = self._load()
    
    def _load(self) -> dict:
        if os.path.exists(self.path):
            with open(self.path, "r") as f: return json.load(f)
        return {"balance": 100.0, "reserved": 0.0, "history": []}
    
    def _save(self):
        with open(self.path, "w") as f: json.dump(self.data, f, indent=2)
    
    def spend(self, amount: float, reason: str) -> bool:
        if self.data["balance"] - self.data["reserved"] < amount: return False
        self.data["balance"] -= amount
        self.data["history"].append({"type": "spend", "amount": amount, "reason": reason, "time": time.time()})
        self._save()
        return True
    
    def earn(self, amount: float, reason: str):
        self.data["balance"] += amount
        self.data["history"].append({"type": "earn", "amount": amount, "reason": reason, "time": time.time()})
        self._save()
    
    def balance(self) -> float: return self.data["balance"]


