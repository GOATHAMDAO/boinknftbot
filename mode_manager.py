"""
Менеджер режимов работы бота
"""
import os
from typing import List, Optional
from colorama import init, Fore, Style
from wallet_manager import WalletManager
from crypto_utils import verify_address_from_key

init(autoreset=True)


class ModeManager:
    """Управление режимами работы бота"""
    
    MODE_SETUP = 1  # Режим настройки: ввод ключей и прокси
    MODE_DAILY = 2   # Режим дейлика
    MODE_BET = 3     # Режим ставок
    MODE_STATS = 4   # Режим статистики
    
    def __init__(self):
        self.wallet_manager = WalletManager()
    
    def show_menu(self):
        """Показывает меню выбора режима"""
        print(f"\n{Fore.CYAN}{'='*60}")
        print(f"{Fore.CYAN}  БОТ ДЛЯ ПРЕДИКШН МАРКЕТА")
        print(f"{Fore.CYAN}{'='*60}{Style.RESET_ALL}\n")
        print(f"{Fore.YELLOW}Выберите режим работы:{Style.RESET_ALL}\n")
        print(f"{Fore.GREEN}[1]{Style.RESET_ALL} Настройка: Ввод приватных ключей и прокси")
        print(f"{Fore.GREEN}[2]{Style.RESET_ALL} Дейлик: Клейм ежедневной награды")
        print(f"{Fore.GREEN}[3]{Style.RESET_ALL} Ставки: Автоматическая торговля")
        print(f"{Fore.GREEN}[4]{Style.RESET_ALL} Статистика: Сбор XP и достижений")
        print(f"{Fore.GREEN}[0]{Style.RESET_ALL} Выход\n")
    
    def get_mode(self) -> int:
        """Получает выбор режима от пользователя"""
        while True:
            try:
                choice = input(f"{Fore.CYAN}Ваш выбор: {Style.RESET_ALL}").strip()
                mode = int(choice)
                if mode in [0, 1, 2, 3, 4]:
                    return mode
                else:
                    print(f"{Fore.RED}Неверный выбор. Введите число от 0 до 4.{Style.RESET_ALL}")
            except ValueError:
                print(f"{Fore.RED}Пожалуйста, введите число.{Style.RESET_ALL}")
    
    def mode_setup(self):
        """Режим 1: Настройка - чтение ключей и прокси из файлов"""
        print(f"\n{Fore.CYAN}{'='*60}")
        print(f"{Fore.CYAN}  РЕЖИМ НАСТРОЙКИ")
        print(f"{Fore.CYAN}{'='*60}{Style.RESET_ALL}\n")
        
        # Читаем приватные ключи из файла
        private_keys = []
        if os.path.exists('private_keys.txt'):
            print(f"{Fore.YELLOW}Чтение приватных ключей из private_keys.txt...{Style.RESET_ALL}")
            try:
                with open('private_keys.txt', 'r', encoding='utf-8') as f:
                    for line_num, line in enumerate(f, 1):
                        key = line.strip()
                        if not key or key.startswith('#'):
                            continue
                        
                        # Убираем 0x если есть
                        if key.startswith('0x'):
                            key = key[2:]
                        
                        # Проверяем длину
                        if len(key) != 64:
                            print(f"{Fore.RED}⚠ Строка {line_num}: Неверная длина ключа (должно быть 64 символа, пропускаем){Style.RESET_ALL}")
                            continue
                        
                        # Проверяем, что это hex
                        try:
                            int(key, 16)
                        except ValueError:
                            print(f"{Fore.RED}⚠ Строка {line_num}: Неверный формат ключа (не hex), пропускаем{Style.RESET_ALL}")
                            continue
                        
                        private_keys.append(key)
            except Exception as e:
                print(f"{Fore.RED}Ошибка при чтении private_keys.txt: {e}{Style.RESET_ALL}")
        else:
            print(f"{Fore.YELLOW}⚠ Файл private_keys.txt не найден.{Style.RESET_ALL}")
            print(f"{Fore.YELLOW}Создайте файл private_keys.txt и добавьте туда приватные ключи (один на строку).{Style.RESET_ALL}\n")
            return
        
        if not private_keys:
            print(f"{Fore.RED}Не найдено ни одного валидного приватного ключа в файле.{Style.RESET_ALL}\n")
            return
        
        # Читаем прокси из файла
        proxies = []
        if os.path.exists('proxies.txt'):
            print(f"{Fore.YELLOW}Чтение прокси из proxies.txt...{Style.RESET_ALL}")
            try:
                with open('proxies.txt', 'r', encoding='utf-8') as f:
                    for line in f:
                        proxy = line.strip()
                        if not proxy or proxy.startswith('#'):
                            proxies.append(None)
                        else:
                            proxies.append(proxy)
            except Exception as e:
                print(f"{Fore.RED}Ошибка при чтении proxies.txt: {e}{Style.RESET_ALL}")
        else:
            print(f"{Fore.YELLOW}⚠ Файл proxies.txt не найден. Прокси не будут использоваться.{Style.RESET_ALL}")
        
        # Дополняем прокси до количества ключей (если прокси меньше)
        while len(proxies) < len(private_keys):
            proxies.append(None)
        
        # Извлекаем адреса из ключей и показываем информацию
        print(f"\n{Fore.GREEN}✓ Данные загружены!")
        print(f"  - Приватных ключей: {len(private_keys)}")
        print(f"  - Прокси: {sum(1 for p in proxies if p)}{Style.RESET_ALL}\n")
        
        print(f"{Fore.CYAN}Извлеченные адреса кошельков:{Style.RESET_ALL}")
        valid_wallets = []
        for i, key in enumerate(private_keys, 1):
            try:
                address = verify_address_from_key(key)
                proxy_info = f" (прокси: {proxies[i-1]})" if proxies[i-1] else " (без прокси)"
                print(f"  {Fore.GREEN}{i}. {address}{Style.RESET_ALL}{proxy_info}")
                valid_wallets.append((address, key, proxies[i-1] if i <= len(proxies) else None))
            except Exception as e:
                print(f"  {Fore.RED}{i}. Ошибка при извлечении адреса: {e}{Style.RESET_ALL}")
        
        if valid_wallets:
            print(f"\n{Fore.GREEN}✓ Успешно загружено {len(valid_wallets)} кошельков{Style.RESET_ALL}")
        else:
            print(f"\n{Fore.RED}✗ Не удалось загрузить ни одного кошелька{Style.RESET_ALL}")
        
        print()
    
    def get_wallets(self) -> List:
        """Получает список кошельков для работы"""
        try:
            return self.wallet_manager.get_wallet_proxies()
        except ValueError as e:
            print(f"{Fore.RED}Ошибка: {e}{Style.RESET_ALL}")
            print(f"{Fore.YELLOW}Используйте режим 1 для настройки кошельков.{Style.RESET_ALL}")
            return []
