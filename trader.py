"""
Основной модуль для автоматической торговли на предикшн маркете
"""
import time
import random
import logging
from datetime import datetime
from typing import Optional, List
from colorama import init, Fore, Style
from api_client import PredictionMarketAPI
from wallet_manager import WalletManager, WalletProxy
from config import (
    MIN_BET_AMOUNT, MAX_BET_AMOUNT, MIN_BETS_COUNT, MAX_BETS_COUNT,
    MIN_BET_INTERVAL_SECONDS, MAX_BET_INTERVAL_SECONDS, MARKET_ID, RANDOM_MARKETS
)

# Инициализация colorama для Windows
init(autoreset=True)

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('trader.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)


class WalletTrader:
    """Трейдер для одного кошелька"""
    
    def __init__(self, wallet_proxy: WalletProxy, available_markets: List[int]):
        self.wallet_proxy = wallet_proxy
        self.wallet_address = wallet_proxy.wallet_address
        self.proxy = wallet_proxy.proxy
        self.available_markets = available_markets
        
        # Создаем API клиенты с прокси и приватным ключом
        self.api = PredictionMarketAPI(self.wallet_address, self.wallet_proxy.private_key, self.proxy)
        
        self.last_bet_time = 0
        self.last_stats_update = 0
        self.user_stats = None  # Статистика с сервера (XP и т.д.)
        self.stats = {
            'total_bets': 0,
            'successful_bets': 0,
            'failed_bets': 0,
            'daily_claims': 0,
        }
    
    def print_status(self, message: str, status: str = "INFO"):
        """Красивый вывод статуса в консоль"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        wallet_short = self.wallet_address[:10] + "..."
        
        # Эмодзи и символы для разных статусов
        icons = {
            "INFO": "ℹ️",
            "SUCCESS": "✅",
            "WARNING": "⚠️",
            "ERROR": "❌"
        }
        
        colors = {
            "INFO": Fore.CYAN,
            "SUCCESS": Fore.GREEN,
            "WARNING": Fore.YELLOW,
            "ERROR": Fore.RED
        }
        
        icon = icons.get(status, "•")
        color = colors.get(status, Fore.WHITE)
        
        # Красивое форматирование с рамкой
        formatted_message = f"{color}┃ {icon} [{timestamp}] [{wallet_short}] {message}{Style.RESET_ALL}"
        print(formatted_message)
        logger.info(f"[{self.wallet_address}] {message}")
    
    def get_random_market(self) -> int:
        """Получает рандомный доступный маркет"""
        if not RANDOM_MARKETS:
            return MARKET_ID
        
        if self.available_markets:
            return random.choice(self.available_markets)
        return MARKET_ID
    
    def analyze_market(self, market_id: int) -> Optional[str]:
        """Анализирует маркет и возвращает рекомендуемый исход"""
        try:
            bets = self.api.get_market_bets(market_id)
            
            if not bets:
                return random.choice(["YES", "NO"])
            
            yes_amount = sum(float(bet.get('amount', 0)) for bet in bets if bet.get('outcome', '').upper() == 'YES')
            no_amount = sum(float(bet.get('amount', 0)) for bet in bets if bet.get('outcome', '').upper() == 'NO')
            
            if yes_amount > no_amount:
                return "NO"
            elif no_amount > yes_amount:
                return "YES"
            else:
                return random.choice(["YES", "NO"])
                
        except Exception as e:
            self.print_status(f"Ошибка при анализе маркета {market_id}: {e}", "ERROR")
            return random.choice(["YES", "NO"])
    
    def make_bet_with_strategy(self, amount: float = None, skip_interval_check: bool = False) -> bool:
        """
        Делает ставку используя стратегию
        
        Args:
            amount: Сумма ставки (если None, выбирается случайно)
            skip_interval_check: Если True, пропускает проверку интервала (для множественных ставок в одной итерации)
        """
        if amount is None:
            amount = round(random.uniform(MIN_BET_AMOUNT, MAX_BET_AMOUNT), 2)
        
        market_id = self.get_random_market()
        
        # Проверяем интервал между ставками (только если не пропущена проверка)
        current_time = time.time()
        if not skip_interval_check and current_time - self.last_bet_time < MIN_BET_INTERVAL_SECONDS:
            return False
        
        # Анализируем маркет или выбираем случайно
        if random.random() < 0.7:
            outcome = self.analyze_market(market_id)
        else:
            outcome = random.choice(["YES", "NO"])
        
        if not outcome:
            outcome = random.choice(["YES", "NO"])
        
        try:
            self.print_status(f"Ставка: маркет {market_id}, {outcome}, сумма: {amount}", "INFO")
            result = self.api.make_bet(outcome, amount, market_id)
            
            self.last_bet_time = current_time
            self.stats['total_bets'] += 1
            self.stats['successful_bets'] += 1
            
            self.print_status(f"Ставка успешно размещена!", "SUCCESS")
            return True
            
        except Exception as e:
            self.stats['total_bets'] += 1
            self.stats['failed_bets'] += 1
            self.print_status(f"Ошибка при размещении ставки: {e}", "ERROR")
            return False
    
    def claim_daily_reward(self) -> bool:
        """Клеймит ежедневную награду"""
        try:
            self.print_status("Клейм ежедневной награды...", "INFO")
            result = self.api.claim_daily()
            
            self.stats['daily_claims'] += 1
            self.print_status(f"Ежедневная награда получена!", "SUCCESS")
            return True
            
        except Exception as e:
            error_msg = str(e).lower()
            if "already" in error_msg or "уже" in error_msg:
                self.print_status("Ежедневная награда уже собрана", "WARNING")
            else:
                self.print_status(f"Ошибка при клейме дейлика: {e}", "ERROR")
            return False
    
    def update_user_stats(self) -> bool:
        """
        Обновляет статистику пользователя с сервера (XP и т.д.)
        
        Returns:
            True если успешно, False иначе
        """
        try:
            stats = self.api.get_user_stats()
            self.user_stats = stats
            self.last_stats_update = time.time()
            
            # Извлекаем XP если есть
            xp = stats.get('xp', stats.get('XP', stats.get('experience', 0)))
            level = stats.get('level', stats.get('Level', 0))
            
            self.print_status(f"Статистика: XP={xp}, Level={level}", "INFO")
            return True
            
        except Exception as e:
            self.print_status(f"Ошибка при получении статистики: {e}", "ERROR")
            return False
    
class AutoTrader:
    """Главный класс для управления несколькими кошельками"""
    
    def __init__(self):
        # Загружаем кошельки и прокси
        wm = WalletManager()
        self.wallet_proxies = wm.get_wallet_proxies()
        
        if not self.wallet_proxies:
            raise ValueError("Не найдено ни одного кошелька в файле wallets.txt!")
        
        # Обновляем список доступных маркетов (используем первый кошелек для проверки)
        self.available_markets = [MARKET_ID]
        if RANDOM_MARKETS:
            self.print_status("Поиск доступных маркетов...", "INFO")
            first_api = PredictionMarketAPI(self.wallet_proxies[0].wallet_address, self.wallet_proxies[0].proxy)
            # Проверяем только несколько маркетов для скорости
            for market_id in range(1, 50):
                if first_api.is_market_available(market_id):
                    self.available_markets.append(market_id)
                if len(self.available_markets) >= 20:
                    break
        
        # Создаем трейдеров для каждого кошелька
        self.traders = [
            WalletTrader(wp, self.available_markets) 
            for wp in self.wallet_proxies
        ]
        
        self.global_stats = {
            'total_bets': 0,
            'successful_bets': 0,
            'failed_bets': 0,
            'daily_claims': 0,
        }
    
    def print_status(self, message: str, status: str = "INFO"):
        """Красивый вывод статуса в консоль"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        
        # Эмодзи и символы для разных статусов
        icons = {
            "INFO": "ℹ️",
            "SUCCESS": "✅",
            "WARNING": "⚠️",
            "ERROR": "❌"
        }
        
        colors = {
            "INFO": Fore.CYAN,
            "SUCCESS": Fore.GREEN,
            "WARNING": Fore.YELLOW,
            "ERROR": Fore.RED
        }
        
        icon = icons.get(status, "•")
        color = colors.get(status, Fore.WHITE)
        
        # Красивое форматирование с рамкой
        formatted_message = f"{color}┃ {icon} [{timestamp}] [GLOBAL] {message}{Style.RESET_ALL}"
        print(formatted_message)
        logger.info(f"[GLOBAL] {message}")
    
    def print_stats(self):
        """Выводит общую статистику"""
        # Собираем статистику со всех трейдеров
        total_bets = sum(t.stats['total_bets'] for t in self.traders)
        successful_bets = sum(t.stats['successful_bets'] for t in self.traders)
        failed_bets = sum(t.stats['failed_bets'] for t in self.traders)
        daily_claims = sum(t.stats['daily_claims'] for t in self.traders)
        print(f"\n{Fore.MAGENTA}{'╔' + '═'*58 + '╗'}{Style.RESET_ALL}")
        print(f"{Fore.MAGENTA}║{'📊 ОБЩАЯ СТАТИСТИКА':^58}║{Style.RESET_ALL}")
        print(f"{Fore.MAGENTA}{'╠' + '═'*58 + '╣'}{Style.RESET_ALL}")
        print(f"{Fore.MAGENTA}║{'Активных кошельков:':<35} {Fore.YELLOW}{len(self.traders):>21}{Style.RESET_ALL}{Fore.MAGENTA}║{Style.RESET_ALL}")
        print(f"{Fore.MAGENTA}║{'Всего ставок:':<35} {Fore.CYAN}{total_bets:>21}{Style.RESET_ALL}{Fore.MAGENTA}║{Style.RESET_ALL}")
        print(f"{Fore.MAGENTA}║{'Успешных:':<35} {Fore.GREEN}{successful_bets:>21}{Style.RESET_ALL}{Fore.MAGENTA}║{Style.RESET_ALL}")
        print(f"{Fore.MAGENTA}║{'Неудачных:':<35} {Fore.RED}{failed_bets:>21}{Style.RESET_ALL}{Fore.MAGENTA}║{Style.RESET_ALL}")
        print(f"{Fore.MAGENTA}║{'Клеймов дейлика:':<35} {Fore.CYAN}{daily_claims:>21}{Style.RESET_ALL}{Fore.MAGENTA}║{Style.RESET_ALL}")
        print(f"{Fore.MAGENTA}║{'Доступных маркетов:':<35} {Fore.YELLOW}{len(self.available_markets):>21}{Style.RESET_ALL}{Fore.MAGENTA}║{Style.RESET_ALL}")
        
        # Выводим статистику по каждому кошельку (XP и т.д.)
        if self.traders:
            print(f"{Fore.MAGENTA}{'╠' + '═'*58 + '╣'}{Style.RESET_ALL}")
            print(f"{Fore.MAGENTA}║{'💼 СТАТИСТИКА КОШЕЛЬКОВ:':^58}║{Style.RESET_ALL}")
            print(f"{Fore.MAGENTA}{'╠' + '═'*58 + '╣'}{Style.RESET_ALL}")
            for i, trader in enumerate(self.traders, 1):
                wallet_short = trader.wallet_address[:10] + "..."
                if trader.user_stats:
                    stats_dict = trader.user_stats.get('stats', trader.user_stats) if isinstance(trader.user_stats, dict) else {}
                    xp = stats_dict.get('xp', stats_dict.get('XP', stats_dict.get('experience', 'N/A')))
                    level = stats_dict.get('level', stats_dict.get('Level', 'N/A'))
                    info = f"  {i}. {wallet_short} - XP: {xp}, Level: {level}"
                    print(f"{Fore.MAGENTA}║{info:<58}{Fore.MAGENTA}║{Style.RESET_ALL}")
                else:
                    info = f"  {i}. {wallet_short} - Статистика не загружена"
                    print(f"{Fore.MAGENTA}║{info:<58}{Fore.MAGENTA}║{Style.RESET_ALL}")
        
        print(f"{Fore.MAGENTA}{'╚' + '═'*58 + '╝'}{Style.RESET_ALL}\n")
    
    def run(self):
        """Основной цикл торговли"""
        self.print_status("="*60, "INFO")
        self.print_status("ЗАПУСК АВТОМАТИЧЕСКОЙ ТОРГОВЛИ", "INFO")
        self.print_status("="*60, "INFO")
        self.print_status(f"Кошельков: {len(self.traders)}", "INFO")
        self.print_status(f"Режим: {'Рандомные маркеты' if RANDOM_MARKETS else f'Маркет {MARKET_ID}'}", "INFO")
        self.print_status(f"Интервал между итерациями: {MIN_BET_INTERVAL_SECONDS} - {MAX_BET_INTERVAL_SECONDS} сек", "INFO")
        self.print_status(f"Сумма ставок: {MIN_BET_AMOUNT} - {MAX_BET_AMOUNT}", "INFO")
        self.print_status(f"Количество ставок за итерацию: {MIN_BETS_COUNT} - {MAX_BETS_COUNT}", "INFO")
        self.print_status("="*60, "INFO")
        
        # Шаг 0: Получение статистики для всех кошельков
        self.print_status("\n[ШАГ 0] Получение статистики кошельков...", "INFO")
        for trader in self.traders:
            trader.update_user_stats()
            time.sleep(1)  # Задержка между кошельками
        
        # Шаг 1: Клейм дейлика для всех кошельков (опционально, можно включить если нужно)
        # Для клейма дейлика используйте режим 2 в меню
        # self.print_status("\n[ШАГ 1] Клейм ежедневных наград...", "INFO")
        # for trader in self.traders:
        #     trader.claim_daily_reward()
        #     time.sleep(2)  # Задержка между кошельками
        
        # Шаг 2: Клейм фаусетов для всех кошельков
        # Шаг 2: Начало автоматической торговли
        self.print_status("\n[ШАГ 2] Начало автоматической торговли...", "INFO")
        self.print_status("Нажмите Ctrl+C для остановки\n", "INFO")
        
        try:
            iteration = 0
            while True:
                iteration += 1
                
                # Проходим по всем кошелькам и делаем ставки
                for trader in self.traders:
                    # Рандомно выбираем количество ставок для этой итерации
                    bets_count = random.randint(MIN_BETS_COUNT, MAX_BETS_COUNT)
                    self.print_status(f"Итерация #{iteration}: делаем {bets_count} ставок", "INFO")
                    
                    for bet_num in range(bets_count):
                        trader.make_bet_with_strategy()
                        if bet_num < bets_count - 1:  # Не ждем после последней ставки
                            time.sleep(2)  # Небольшая задержка между ставками одного кошелька
                    time.sleep(1)  # Небольшая задержка между кошельками
                
                # Обновляем статистику каждые 5 итераций
                if iteration % 5 == 0:
                    for trader in self.traders:
                        trader.update_user_stats()
                        time.sleep(0.5)
                
                # Показываем статистику каждые 10 итераций
                if iteration % 10 == 0:
                    self.print_stats()
                
                # Небольшая задержка перед следующей итерацией
                time.sleep(5)
                
        except KeyboardInterrupt:
            self.print_status("\nОстановка торговли...", "WARNING")
            self.print_stats()
        except Exception as e:
            self.print_status(f"Критическая ошибка: {e}", "ERROR")
            self.print_stats()
            raise
