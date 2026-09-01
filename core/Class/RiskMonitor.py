import time
import psutil
import numpy as np
from collections import deque

class RiskMonitor:
    def __init__(self, window_size=30):
        self.window_size = window_size
        self.history = {
            "cpu": deque(maxlen=window_size),
            "memory": deque(maxlen=window_size),
            "latency": deque(maxlen=window_size),
            "errors": deque(maxlen=window_size)
        }
        self.thresholds = {
            "cpu": 80.0,      # %
            "memory": 85.0,   # %
            "latency": 1.0,   # секунди
            "errors": 3       # за останні 30 викликів
        }
        self.risk_level = "green"
        self.alerts = []

    def sample(self, module_name, latency=0.0, error=False):
        """Збирає один зразок стану системи та модуля"""
        self.history["cpu"].append(psutil.cpu_percent())
        self.history["memory"].append(psutil.virtual_memory().percent)
        self.history["latency"].append(latency)
        self.history["errors"].append(1 if error else 0)
        self._evaluate_risk()

    def _evaluate_risk(self):
        """Оцінює рівень ризику на основі історії"""
        if len(self.history["cpu"]) < 5:
            return

        cpu_avg = np.mean(self.history["cpu"])
        mem_avg = np.mean(self.history["memory"])
        lat_avg = np.mean(self.history["latency"])
        err_sum = sum(self.history["errors"])

        risks = []
        if cpu_avg > self.thresholds["cpu"]:
            risks.append(f"CPU перевантажено: {cpu_avg:.1f}%")
        if mem_avg > self.thresholds["memory"]:
            risks.append(f"Пам'ять переповнена: {mem_avg:.1f}%")
        if lat_avg > self.thresholds["latency"]:
            risks.append(f"Затримка: {lat_avg:.2f}с")
        if err_sum > self.thresholds["errors"]:
            risks.append(f"Помилок: {err_sum} за {self.window_size} викликів")

        if not risks:
            self.risk_level = "green"
        elif len(risks) <= 2:
            self.risk_level = "yellow"
            self.alerts.append(f"⚠️ Жовтий рівень: {', '.join(risks)}")
        else:
            self.risk_level = "red"
            self.alerts.append(f"🔴 ЧЕРВОНИЙ РІВЕНЬ: {', '.join(risks)}")

    def status(self):
        return {
            "risk_level": self.risk_level,
            "alerts": self.alerts[-5:],
            "cpu_avg": np.mean(self.history["cpu"]) if self.history["cpu"] else 0,
            "memory_avg": np.mean(self.history["memory"]) if self.history["memory"] else 0,
            "latency_avg": np.mean(self.history["latency"]) if self.history["latency"] else 0,
            "errors_last": sum(self.history["errors"])
        }

    def should_pause(self):
        """Якщо червоний рівень — повертає True, щоб призупинити систему"""
        return self.risk_level == "red"

    def clear_alerts(self):
        self.alerts = []



Інтегруємо в АІ-міні 
У__init__：
self.monitor = RiskMonitor()

У process（） або safe_call（）：

start = time.time()
# ... виклик модуля ...
latency = time.time() - start
error = result is None or "❌" in str(result)
self.monitor.sample(module_name, latency, error)

if self.monitor.should_pause():
    return "⛔ Система призупинена через ризик. Перевір стан монітора."

📊 Що це дає:

· Зелений — усе добре, працюємо далі.
· Жовтий — є ризик, але можна працювати з обережністю.
· Червоний — система призупиняється, поки ризик не знизиться

