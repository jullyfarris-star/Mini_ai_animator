#!/usr/bin/env python3
"""
🤖 AIMini - Робочий точка входу
Запуск: python main.py
"""

import sys
from pathlib import Path
from core.agent import AIMini


def print_banner():
    """Красивий банер"""
    banner = """
    ╔════════════════════════════════════════╗
    ║      🤖 AI-МІНІ v0.1 🤖               ║
    ║   Мініатюрний АІ-агент з пам'яттю     ║
    ╚════════════════════════════════════════╝
    
    💡 Типи команд:
       • /привіт         - Привіт
       • /статус         - Показати статус агента
       • /пам'ять        - Показати відохраненні дані
       • /очистити       - Очистити контекст
       • /поповнити N    - Додати N токенів
       • /як_тебе_звати  - Дізнатися ім'я агента
       • /кінець         - Вихід
       
    👍 На кожну відповідь пишіть: /добре або /погано
    ════════════════════════════════════════════════
    """
    print(banner)


def format_status(agent: AIMini) -> str:
    """Красивий вивід статусу"""
    status = agent.status()
    return f"""
📊 СТАТУС АГЕНТА:
   💰 Токени: {status['tokens']:.1f}
   💭 Контекст: {status['context_len']} повідомлень
   📚 Пам'ять: {status['memory_chunks']} чанків
   🔍 FAISS індекс: {status['faiss_size']} ембедінгів
    """


def handle_command(agent: AIMini, user_input: str) -> tuple:
    """
    Обробити спеціальні команди
    Повертає: (is_command, response)
    """
    cmd = user_input.lower().strip()
    
    if cmd == "/статус":
        return True, format_status(agent)
    
    elif cmd == "/привіт":
        return True, "Привіт! 👋 Я AI-Міні, твій персональний помічник. Чим я можу допомогти?"
    
    elif cmd == "/як_тебе_звати":
        return True, "Мене звуть AI-Міні (або просто Міні). Приємно познайомитись! 😊"
    
    elif cmd == "/пам'ять":
        status = agent.status()
        if status['memory_chunks'] == 0:
            return True, "📭 Пам'ять порожня. Спілкуємось, щоб я щось запам'ятав!"
        else:
            return True, f"📚 У моїй пам'яті {status['memory_chunks']} фактів. Запитай що-небудь, і я пошукаю!"
    
    elif cmd == "/очистити":
        agent.context = []
        return True, "✨ Контекст очищено. Починаємо спочатку!"
    
    elif cmd.startswith("/поповнити "):
        try:
            amount = float(cmd.split()[-1])
            agent.wallet.earn(amount, "manual_refill")
            return True, f"💸 Додано {amount} токенів! Новий баланс: {agent.wallet.balance():.1f}"
        except:
            return True, "❌ Помилка: /поповнити <число>"
    
    elif cmd == "/добре":
        return True, agent.feedback(is_positive=True)
    
    elif cmd == "/погано":
        return True, agent.feedback(is_positive=False)
    
    elif cmd in ["/кінець", "/вихід", "/exit", "quit"]:
        return True, "KІНЕЦЬ_ПРОГРАМИ"
    
    return False, ""


def interactive_mode():
    """Інтерактивний режим"""
    print_banner()
    
    try:
        print("⏳ Завантажую агента...")
        agent = AIMini()
        print("✅ Агент готовий!\n")
    except Exception as e:
        print(f"❌ Помилка завантаження: {e}")
        print("💡 Переконайся, що у тебе встановлені всі залежності:")
        print("   pip install -r requirements.txt")
        sys.exit(1)
    
    print("Пиши свої повідомлення (або /кінець для виходу):\n")
    
    while True:
        try:
            user_input = input("👤 Ти: ").strip()
            
            if not user_input:
                continue
            
            # Перевірити команду
            is_cmd, response = handle_command(agent, user_input)
            
            if is_cmd:
                if response == "KІНЕЦЬ_ПРОГРАМИ":
                    print("\n👋 До побачення! Дякую за спілкування!")
                    break
                print(f"🤖 Агент: {response}\n")
            else:
                # Нормальний запит
                print("\n⏳ Думаю...\n")
                response = agent.process(user_input)
                print(f"🤖 Агент: {response}\n")
                print("👉 Чи відповідь була корисною? (/добре або /погано)\n")
        
        except KeyboardInterrupt:
            print("\n\n👋 Перервано користувачем. До побачення!")
            break
        except Exception as e:
            print(f"❌ Помилка: {e}")
            print("💡 Спробуй ще раз або напиши /кінець\n")


def demo_mode():
    """Демо режим (автоматичні тести)"""
    print_banner()
    print("🎬 ДЕМО РЕЖИМ\n")
    
    try:
        print("⏳ Завантажую агента...")
        agent = AIMini()
        print("✅ Агент готовий!\n")
    except Exception as e:
        print(f"❌ Помилка: {e}")
        sys.exit(1)
    
    # Тестові запити
    test_queries = [
        "Привіт, як тебе звати?",
        "Скажи мені щось про себе",
        "Пам'ятай: я люблю Python",
        "Що ти знаєш про Python?",
    ]
    
    print("=" * 50)
    for i, query in enumerate(test_queries, 1):
        print(f"\n📝 Запит {i}: {query}")
        print("-" * 50)
        response = agent.process(query)
        print(f"🤖 Відповідь: {response}")
        print(f"📊 Статус: {agent.wallet.balance():.1f} токенів, {len(agent.context)} повідомлень")
    
    print("\n" + "=" * 50)
    print(format_status(agent))


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="🤖 AI-Міні - Мініатюрний АІ-агент")
    parser.add_argument(
        "--mode",
        choices=["interactive", "demo"],
        default="interactive",
        help="Режим запуску (interactive або demo)"
    )
    
    args = parser.parse_args()
    
    if args.mode == "demo":
        demo_mode()
    else:
        interactive_mode()
