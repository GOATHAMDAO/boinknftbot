"""
Тестовый скрипт для проверки работы API
"""
from api_client import PredictionMarketAPI
from config import WALLET_ADDRESS, MARKET_ID

def test_api():
    """Тестирует основные функции API"""
    print("Тестирование API клиента...")
    print(f"Кошелек: {WALLET_ADDRESS}")
    print(f"Маркет: {MARKET_ID}\n")
    
    api = PredictionMarketAPI()
    
    # Тест 1: Получение ставок маркета
    print("1. Получение ставок маркета...")
    try:
        market_bets = api.get_market_bets()
        print(f"   ✅ Успешно! Получено ставок: {len(market_bets)}")
        if market_bets:
            print(f"   Пример первой ставки: {market_bets[0]}")
    except Exception as e:
        print(f"   ❌ Ошибка: {e}")
    
    print()
    
    # Тест 2: Получение ставок пользователя
    print("2. Получение ставок пользователя...")
    try:
        user_bets = api.get_user_bets()
        print(f"   ✅ Успешно! Получено ставок: {len(user_bets)}")
        if user_bets:
            print(f"   Пример первой ставки: {user_bets[0]}")
    except Exception as e:
        print(f"   ❌ Ошибка: {e}")
    
    print()
    
    # Тест 3: Клейм дейлика
    print("3. Тест клейма дейлика...")
    try:
        result = api.claim_daily()
        print(f"   ✅ Успешно! Ответ: {result}")
    except Exception as e:
        print(f"   ❌ Ошибка: {e}")
    
    print()
    
    # Тест 4: Попытка сделать ставку (закомментировано для безопасности)
    print("4. Тест размещения ставки (закомментировано)...")
    print("   Для тестирования ставки раскомментируйте код ниже")
    # try:
    #     result = api.make_bet("YES", 0.01)
    #     print(f"   ✅ Успешно! Ответ: {result}")
    # except Exception as e:
    #     print(f"   ❌ Ошибка: {e}")
    
    print("\nТестирование завершено!")

if __name__ == "__main__":
    if not WALLET_ADDRESS:
        print("Ошибка: WALLET_ADDRESS не установлен в .env файле!")
        print("Создайте .env файл с настройками.")
    else:
        test_api()
