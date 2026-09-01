import time
import json
import os
import traceback

class SystemSafeguard:
    """
    Глобальний запобіжник для AI-mini.
    Ловить вильоти, перевіряє стан модулів, блокує проблемні.
    """
    def __init__(self, log_path: str = "data/safeguard_log.json"):
        self.log_path = log_path
        self.log = self._load_log()
        self.module_health = {}
        self.crash_count = 0
        self.max_crashes = 5
        self.locked_modules = set()
    
    def _load_log(self) -> list:
        if os.path.exists(self.log_path):
            with open(self.log_path, "r", encoding="utf-8") as f:
                return json.load(f)
        return []
    
    def _save_log(self):
        with open(self.log_path, "w", encoding="utf-8") as f:
            json.dump(self.log, f, indent=2, ensure_ascii=False)
    
    def register_module(self, name: str, module):
        """Реєструє модуль для моніторингу"""
        self.module_health[name] = {
            "status": "ok",
            "calls": 0,
            "errors": 0,
            "last_error": None,
            "last_ok": time.time()
        }
    
    def check_before(self, module_name: str) -> bool:
        """Перевіряє перед викликом модуля"""
        if module_name in self.locked_modules:
            return False
        
        health = self.module_health.get(module_name)
        if health and health["status"] == "locked":
            return False
        
        return True
    
    def report_success(self, module_name: str):
        """Звіт про успішний виклик"""
        if module_name in self.module_health:
            self.module_health[module_name]["calls"] += 1
            self.module_health[module_name]["last_ok"] = time.time()
            self.module_health[module_name]["status"] = "ok"
    
    def report_error(self, module_name: str, error: str):
        """Звіт про помилку"""
        if module_name not in self.module_health:
            self.register_module(module_name, None)
        
        health = self.module_health[module_name]
        health["errors"] += 1
        health["last_error"] = error
        health["status"] = "error"
        
        self.crash_count += 1
        
        # логуємо
        entry = {
            "time": time.time(),
            "module": module_name,
            "error": error,
            "crash_count": self.crash_count
        }
        self.log.append(entry)
        self._save_log()
        
        # якщо забагато помилок — блокуємо модуль
        if health["errors"] >= 3:
            self.locked_modules.add(module_name)
            health["status"] = "locked"
            return f"⚠️ Модуль {module_name} заблоковано після {health['errors']} помилок"
        
        return f"⚠️ Помилка в {module_name}: {error}"
    
    def check_all(self, agent) -> dict:
        """Перевіряє всі модулі агента"""
        report = {
            "timestamp": time.time(),
            "modules": {},
            "locked": list(self.locked_modules),
            "crashes": self.crash_count
        }
        
        # перевіряємо кожен модуль
        checks = [
            ("wallet", lambda a: a.wallet.balance() if hasattr(a, 'wallet') else None),
            ("grid", lambda a: a.grid.status() if hasattr(a, 'grid') else None),
            ("black_box", lambda a: a.black_box.Z if hasattr(a, 'black_box') else None),
            ("bb_safeguard", lambda a: a.bb_safeguard.violations if hasattr(a, 'bb_safeguard') else None),
            ("weight", lambda a: a.weight.config if hasattr(a, 'weight') else None),
            ("billiard", lambda a: len(a.billiard.balls) if hasattr(a, 'billiard') else None),
            ("photo_learner", lambda a: "ok" if hasattr(a, 'photo_learner') else None),
        ]
        
        for name, check in checks:
            try:
                result = check(agent)
                if result is not None:
                    report["modules"][name] = {"status": "ok", "value": str(result)}
                else:
                    report["modules"][name] = {"status": "missing"}
            except Exception as e:
                report["modules"][name] = {"status": "error", "error": str(e)}
        
        return report
    
    def auto_heal(self, agent) -> list:
        """Спроба автоматично виправити проблеми"""
        fixes = []
        
        # 1. Якщо заблоковано чорну скриню — скидаємо
        if "black_box" in self.locked_modules:
            if hasattr(agent, 'bb_safeguard'):
                agent.bb_safeguard.reset()
                self.locked_modules.discard("black_box")
                fixes.append("Скинуто запобіжник чорної скрині")
        
        # 2. Якщо більярд завис — очищаємо кулі
        if "billiard" in self.locked_modules:
            if hasattr(agent, 'billiard'):
                agent.billiard.balls = []
                self.locked_modules.discard("billiard")
                fixes.append("Очищено кулі більярду")
        
        # 3. Якщо photo_learner — просто перезапускаємо
        if "photo_learner" in self.locked_modules:
            self.locked_modules.discard("photo_learner")
            fixes.append("PhotoLearner розблоковано")
        
        return fixes
    
    def status(self) -> str:
        """Короткий звіт про стан системи"""
        lines = ["🛡️ Стан запобіжника:"]
        lines.append(f"   Вильотів: {self.crash_count}")
        lines.append(f"   Заблоковано модулів: {len(self.locked_modules)}")
        if self.locked_modules:
            lines.append(f"   Заблоковано: {', '.join(self.locked_modules)}")
        lines.append(f"   Записів у лозі: {len(self.log)}")
        return "\n".join(lines)


Потім інтегруємо в ai_mini.py. Додаємо в __init__:

self.safeguard = SystemSafeguard()

# реєструємо всі модулі
self.safeguard.register_module("wallet", self.wallet)
self.safeguard.register_module("grid", self.grid)
self.safeguard.register_module("black_box", self.black_box)
self.safeguard.register_module("bb_safeguard", self.bb_safeguard)
self.safeguard.register_module("weight", self.weight)
self.safeguard.register_module("billiard", self.billiard)
self.safeguard.register_module("photo_learner", self.photo_learner)



І додаємо метод для безпечного виклику будь-якого модуля:


def safe_call(self, module_name: str, func, *args, **kwargs):
    """Безпечний виклик модуля з перевіркою"""
    if not self.safeguard.check_before(module_name):
        return f"⛔ Модуль {module_name} заблоковано. Використай heal() для відновлення."
    
    try:
        result = func(*args, **kwargs)
        self.safeguard.report_success(module_name)
        return result
    except Exception as e:
        error_msg = f"{type(e).__name__}: {str(e)}"
        self.safeguard.report_error(module_name, error_msg)
        return f"❌ {error_msg}"

Як це працює:

1. Перед кожним викликом модуля — check_before()
2. Якщо модуль заблокований — одразу відмова
3. Якщо виліт — report_error() логує і рахує
4. Після 3 помилок — модуль блокується
5. auto_heal() намагається виправити проблеми
6. check_all() — повна діагностика всієї системи




