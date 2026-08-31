scripts/run_agent.py
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
from core.agent import AIMini

def main():
    agent = AIMini()
    print("\n" + "="*50)
    print("🤖 AI-Mini PRO (з трансформером + гібридним RAG)")
    print(f"💰 Токенів: {agent.wallet.balance()}")
    print("Команди: 'поповнити 10' — додати токени, '👍' або '👎' — оцінити відповідь")
    print("="*50 + "\n")
    
    while True:
        user = input("🧑 Ти: ").strip()
        if user.lower() in ("вихід", "exit"): 
            print("👋 Бувай!"); break
        if not user: continue
        
        # Поповнення токенів
        if user.startswith("поповнити"):
            try:
                amount = float(user.split()[1])
                agent.wallet.earn(amount, "manual")
                print(f"💰 +{amount} токенів. Баланс: {agent.wallet.balance()}")
                continue
            except: pass
        
        # Зворотний зв'язок
        if user in ("👍", "+1", "добре"):
            print(agent.feedback(True))
            continue
        if user in ("👎", "-1", "погано"):
            print(agent.feedback(False))
            continue
        
        # Звичайний запит
        reply = agent.process(user)
        print(f"🤖 AI: {reply}\n")
        print(f"📊 Стан: токени={agent.wallet.balance():.2f} | пам'ять={agent.status()['memory_chunks']} чанків")

if __name__ == "__main__":
    main()
