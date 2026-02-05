"""
Конфигурация для автоматической торговли на предикшн маркете
"""
import os
from dotenv import load_dotenv

load_dotenv()

# API настройки
API_BASE_URL = "https://inkpredict.vercel.app/api"
MARKET_ID = 109

# Настройки кошелька
# Кошельки теперь загружаются из файла wallets.txt / private_keys.txt
# WALLET_ADDRESS больше не используется, оставлено для обратной совместимости
WALLET_ADDRESS = os.getenv("WALLET_ADDRESS", "")

# Настройки торговли
MIN_BET_AMOUNT = float(os.getenv("MIN_BET_AMOUNT", "0.01"))  # Минимальная сумма ставки
MAX_BET_AMOUNT = float(os.getenv("MAX_BET_AMOUNT", "1.0"))  # Максимальная сумма ставки
MIN_BETS_COUNT = int(os.getenv("MIN_BETS_COUNT", "1"))  # Минимальное количество ставок за итерацию
MAX_BETS_COUNT = int(os.getenv("MAX_BETS_COUNT", "3"))  # Максимальное количество ставок за итерацию
MIN_BET_INTERVAL_SECONDS = int(os.getenv("MIN_BET_INTERVAL_SECONDS", "50"))  # Минимальный интервал между итерациями в секундах
MAX_BET_INTERVAL_SECONDS = int(os.getenv("MAX_BET_INTERVAL_SECONDS", "70"))  # Максимальный интервал между итерациями в секундах
RANDOM_MARKETS = os.getenv("RANDOM_MARKETS", "true").lower() == "true"  # Выбирать рандомные маркеты

# Настройки реферальной системы
# Реферальный код зашит в код
REFERRAL_CODE = "BA08NOBF"  # Реферальный код для регистрации новых аккаунтов

# Настройки логирования
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
