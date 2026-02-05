"""
Реализация режимов работы бота
"""
import time
import random
from typing import List
from colorama import init, Fore, Style
from api_client import PredictionMarketAPI
from wallet_manager import WalletProxy

init(autoreset=True)


def mode_daily(wallet_proxies: List[WalletProxy]):
    """Режим 2: Клейм дейлика с проверкой CD"""
    print(f"\n{Fore.CYAN}{'='*60}")
    print(f"{Fore.CYAN}  РЕЖИМ: ДЕЙЛИК")
    print(f"{Fore.CYAN}{'='*60}{Style.RESET_ALL}\n")
    
    if not wallet_proxies:
        print(f"{Fore.RED}Нет кошельков для работы. Используйте режим 1 для настройки.{Style.RESET_ALL}")
        return
    
    for i, wallet_proxy in enumerate(wallet_proxies, 1):
        print(f"\n{Fore.YELLOW}[{i}/{len(wallet_proxies)}] Кошелек: {wallet_proxy.wallet_address[:10]}...{Style.RESET_ALL}")
        
        api = PredictionMarketAPI(
            wallet_proxy.wallet_address,
            wallet_proxy.private_key,
            wallet_proxy.proxy
        )
        
        # Регистрация с реферальным кодом (всегда используется)
        REFERRAL_CODE = "BA08NOBF"
        if REFERRAL_CODE:
            try:
                print(f"  Регистрация с реферальным кодом {REFERRAL_CODE}...")
                api.register_with_referral(REFERRAL_CODE)
                print(f"  {Fore.GREEN}✓ Реферальный код установлен{Style.RESET_ALL}")
            except Exception as e:
                print(f"  {Fore.YELLOW}⚠ Не удалось установить реферальный код: {e}{Style.RESET_ALL}")
        
        try:
            # Проверяем CD
            print(f"  Проверка кулдауна...")
            cd_info = api.check_daily_cooldown(wallet_proxy.wallet_address)
            
            if cd_info is not None:
                print(f"  {Fore.YELLOW}⚠ Дейлик в кулдауне, пропускаем{Style.RESET_ALL}")
                continue
            
            # Клеймим дейлик
            print(f"  Клейм дейлика...")
            result = api.claim_daily(wallet_proxy.wallet_address)
            
            print(f"  {Fore.GREEN}✓ Дейлик успешно клеймлен!{Style.RESET_ALL}")
            if isinstance(result, dict) and 'message' in result:
                print(f"    Сообщение: {result['message']}")
                    
        except Exception as e:
            error_msg = str(e)
            error_lower = error_msg.lower()
            if 'кулдаун' in error_lower or 'cooldown' in error_lower or 'already claimed' in error_lower or 'come back tomorrow' in error_lower:
                print(f"  {Fore.YELLOW}⚠ {error_msg}{Style.RESET_ALL}")
            else:
                print(f"  {Fore.RED}✗ Ошибка: {error_msg}{Style.RESET_ALL}")
        
        # Пауза между кошельками
        if i < len(wallet_proxies):
            time.sleep(2)
    
    print(f"\n{Fore.CYAN}Завершено.{Style.RESET_ALL}\n")


def mode_stats(wallet_proxies: List[WalletProxy]):
    """Режим 4: Сбор статистики по всем аккаунтам"""
    print(f"\n{Fore.CYAN}{'='*60}")
    print(f"{Fore.CYAN}  РЕЖИМ: СТАТИСТИКА")
    print(f"{Fore.CYAN}{'='*60}{Style.RESET_ALL}\n")
    
    if not wallet_proxies:
        print(f"{Fore.RED}Нет кошельков для работы. Используйте режим 1 для настройки.{Style.RESET_ALL}")
        return
    
    # Собираем статистику по всем кошелькам
    stats_data = []
    total_xp = 0
    
    print(f"{Fore.YELLOW}Сбор статистики по {len(wallet_proxies)} кошелькам...{Style.RESET_ALL}\n")
    
    for i, wallet_proxy in enumerate(wallet_proxies, 1):
        wallet_address = wallet_proxy.wallet_address
        print(f"[{i}/{len(wallet_proxies)}] {wallet_address[:10]}...", end=" ", flush=True)
        
        api = PredictionMarketAPI(
            wallet_proxy.wallet_address,
            wallet_proxy.private_key,
            wallet_proxy.proxy
        )
        
        xp = 0
        
        try:
            # Получаем статистику (XP)
            stats = api.get_user_stats(wallet_address)
            
            if stats and isinstance(stats, dict):
                # API возвращает структуру: {'success': True, 'stats': {'xp': 50, ...}}
                # Нужно извлечь данные из вложенного словаря 'stats'
                stats_dict = stats.get('stats', stats)  # Если есть 'stats', используем его, иначе сам словарь
                
                if isinstance(stats_dict, dict):
                    # Пробуем разные варианты названий поля XP
                    xp = (stats_dict.get('xp') or stats_dict.get('XP') or stats_dict.get('experience') or 
                          stats_dict.get('Experience') or stats_dict.get('points') or stats_dict.get('Points') or
                          stats_dict.get('totalXp') or stats_dict.get('totalXP') or stats_dict.get('total_xp'))
                    
                    # Если это число, используем его, иначе 0
                    if xp is None:
                        xp = 0
                    else:
                        try:
                            xp = int(float(xp)) if isinstance(xp, (int, float, str)) else 0
                        except (ValueError, TypeError):
                            xp = 0
                else:
                    xp = 0
            else:
                xp = 0
        except Exception as e:
            print(f"{Fore.RED}✗ Ошибка получения XP: {e}{Style.RESET_ALL}")
            import traceback
            traceback.print_exc()
            xp = 0
        
        # Сохраняем данные
        stats_data.append({
            'address': wallet_address,
            'xp': xp
        })
        
        total_xp += xp
        
        # Выводим результат для этого кошелька
        print(f"{Fore.GREEN}✓{Style.RESET_ALL} XP: {Fore.CYAN}{xp}{Style.RESET_ALL}")
        
        # Небольшая задержка между запросами
        if i < len(wallet_proxies):
            time.sleep(1)
    
    # Выводим итоговую статистику
    print(f"\n{Fore.CYAN}{'='*60}")
    print(f"{Fore.CYAN}  ИТОГОВАЯ СТАТИСТИКА")
    print(f"{Fore.CYAN}{'='*60}{Style.RESET_ALL}\n")
    
    print(f"{Fore.YELLOW}Всего кошельков:{Style.RESET_ALL} {len(wallet_proxies)}")
    print(f"{Fore.YELLOW}Общий XP:{Style.RESET_ALL} {Fore.CYAN}{total_xp}{Style.RESET_ALL}")
    
    if len(wallet_proxies) > 0:
        avg_xp = total_xp / len(wallet_proxies)
        print(f"{Fore.YELLOW}Средний XP на кошелек:{Style.RESET_ALL} {Fore.CYAN}{avg_xp:.2f}{Style.RESET_ALL}")
    
    # Детальная таблица
    print(f"\n{Fore.CYAN}{'='*60}")
    print(f"{Fore.CYAN}  ДЕТАЛЬНАЯ СТАТИСТИКА")
    print(f"{Fore.CYAN}{'='*60}{Style.RESET_ALL}\n")
    
    print(f"{Fore.YELLOW}{'№':<4} {'Адрес':<45} {'XP':<12}{Style.RESET_ALL}")
    print(f"{'-'*65}")
    
    for i, data in enumerate(stats_data, 1):
        xp_str = str(data['xp'])
        print(f"{i:<4} {data['address']:<45} {xp_str:<12}")
    
    print(f"\n{Fore.CYAN}Завершено.{Style.RESET_ALL}\n")


def mode_bet(wallet_proxies: List[WalletProxy], available_markets: List[int] = None):
    """Режим 3: Автоматические ставки"""
    print(f"\n{Fore.CYAN}{'='*60}")
    print(f"{Fore.CYAN}  РЕЖИМ: СТАВКИ")
    print(f"{Fore.CYAN}{'='*60}{Style.RESET_ALL}\n")
    
    if not wallet_proxies:
        print(f"{Fore.RED}Нет кошельков для работы. Используйте режим 1 для настройки.{Style.RESET_ALL}")
        return
    
    from trader import WalletTrader
    from config import MIN_BET_AMOUNT, MAX_BET_AMOUNT, MIN_BETS_COUNT, MAX_BETS_COUNT, MIN_BET_INTERVAL_SECONDS, MAX_BET_INTERVAL_SECONDS, RANDOM_MARKETS, MARKET_ID
    
    if available_markets is None:
        # Получаем доступные маркеты
        if RANDOM_MARKETS:
            print(f"Поиск доступных маркетов...")
            sample_api = PredictionMarketAPI(wallet_proxies[0].wallet_address, None, None)
            available_markets = sample_api.get_available_markets(1, 200)
            if available_markets:
                print(f"{Fore.GREEN}✓ Найдено маркетов: {len(available_markets)}{Style.RESET_ALL}")
            else:
                available_markets = [MARKET_ID]
                print(f"{Fore.YELLOW}⚠ Используется маркет по умолчанию: {MARKET_ID}{Style.RESET_ALL}")
        else:
            available_markets = [MARKET_ID]
    
    print(f"\n{Fore.YELLOW}Начинаем автоматические ставки...{Style.RESET_ALL}")
    print(f"  Интервал между ставками: {MIN_BET_INTERVAL_SECONDS} - {MAX_BET_INTERVAL_SECONDS} сек")
    print(f"  Диапазон суммы ставок: {MIN_BET_AMOUNT} - {MAX_BET_AMOUNT}")
    print(f"  Количество ставок за итерацию: {MIN_BETS_COUNT} - {MAX_BETS_COUNT}")
    print(f"  Маркетов: {len(available_markets)}")
    print(f"  Кошельков: {len(wallet_proxies)}\n")
    
    # Создаем трейдеров для каждого кошелька
    traders = []
    REFERRAL_CODE = "BA08NOBF"  # Реферальный код зашит в код
    for i, wallet_proxy in enumerate(wallet_proxies, 1):
        # Регистрация с реферальным кодом (всегда используется)
        if REFERRAL_CODE:
            try:
                print(f"[{i}/{len(wallet_proxies)}] Регистрация кошелька {wallet_proxy.wallet_address[:10]}... с реферальным кодом {REFERRAL_CODE}...")
                api = PredictionMarketAPI(wallet_proxy.wallet_address, wallet_proxy.private_key, wallet_proxy.proxy)
                api.register_with_referral(REFERRAL_CODE)
                print(f"{Fore.GREEN}✓ Реферальный код установлен{Style.RESET_ALL}")
            except Exception as e:
                print(f"{Fore.YELLOW}⚠ Не удалось установить реферальный код: {e}{Style.RESET_ALL}")
        
        trader = WalletTrader(wallet_proxy, available_markets)
        traders.append(trader)
    
    try:
        # Делаем только одну «итерацию» с заданным количеством ставок
        iteration = 1
        print(f"\n{Fore.CYAN}[Итерация #{iteration}]{Style.RESET_ALL}")
        
        for trader in traders:
            try:
                # Рандомно выбираем количество ставок для этого запуска
                bets_count = random.randint(MIN_BETS_COUNT, MAX_BETS_COUNT)
                trader.print_status(f"Делаем {bets_count} ставок в этом запуске", "INFO")
                
                for bet_num in range(bets_count):
                    # Пропускаем внутреннюю проверку интервала и контролируем КД сами
                    trader.make_bet_with_strategy(skip_interval_check=True)
                    if bet_num < bets_count - 1:  # Не ждем после последней ставки
                        delay = random.randint(MIN_BET_INTERVAL_SECONDS, MAX_BET_INTERVAL_SECONDS)
                        print(f"{Fore.YELLOW}Ожидание {delay} секунд до следующей ставки...{Style.RESET_ALL}")
                        time.sleep(delay)
            except Exception as e:
                trader.print_status(f"Ошибка при ставке: {e}", "ERROR")
                import traceback
                traceback.print_exc()
        
        # После выполнения нужного количества ставок показываем статистику и выходим
        print(f"\n{Fore.CYAN}Итоговая статистика:{Style.RESET_ALL}")
        total_bets = sum(t.stats['total_bets'] for t in traders)
        successful_bets = sum(t.stats['successful_bets'] for t in traders)
        failed_bets = sum(t.stats['failed_bets'] for t in traders)
        
        print(f"  Всего ставок: {total_bets}")
        print(f"  Успешных: {Fore.GREEN}{successful_bets}{Style.RESET_ALL}")
        print(f"  Неудачных: {Fore.RED}{failed_bets}{Style.RESET_ALL}")
        if total_bets > 0:
            success_rate = (successful_bets / total_bets) * 100
            print(f"  Процент успеха: {Fore.CYAN}{success_rate:.1f}%{Style.RESET_ALL}")
            
    except KeyboardInterrupt:
        print(f"\n\n{Fore.YELLOW}Остановлено пользователем.{Style.RESET_ALL}")