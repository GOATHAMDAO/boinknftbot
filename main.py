"""
Главный файл для запуска автоматической торговли
"""
from colorama import init, Fore, Style
from mode_manager import ModeManager
from modes import mode_daily, mode_bet, mode_stats

init(autoreset=True)


def print_banner():
    """Выводит ASCII-баннер при запуске программы"""
    banner = f"""
{Fore.WHITE}╔══════════════════════════════════════════════════════════════════╗
║                                                                  ║
║  _____ _____ _____ _____ _____ _____ _____    ____  _____ _____  ║
║ |   __|     |  _  |_   _|  |  |  _  |     |  |    \\|  _  |     | ║
║ |  |  |  |  |     | | | |     |     | | | |  |  |  |     |  |  | ║
║ |_____|_____|__|__| |_| |__|__|__|__|_|_|_|  |____/|__|__|_____| ║
║                                                                  ║
║                          BOINK Bot                               ║
║                                                                  ║
║                          BY: Goatham                             ║
║                                                                  ║
║                     https://t.me/goathamdao                      ║
║                                                                  ║
╚══════════════════════════════════════════════════════════════════╝{Style.RESET_ALL}
"""
    print(banner)


if __name__ == "__main__":
    # Показываем баннер при запуске
    print_banner()
    
    mode_manager = ModeManager()
    
    while True:
        try:
            # Показываем меню
            mode_manager.show_menu()
            
            # Получаем выбор режима
            mode = mode_manager.get_mode()
            
            if mode == 0:
                print(f"\n{Fore.CYAN}Выход из программы.{Style.RESET_ALL}\n")
                break
            
            elif mode == ModeManager.MODE_SETUP:
                # Режим 1: Настройка
                mode_manager.mode_setup()
            
            elif mode in [ModeManager.MODE_DAILY, ModeManager.MODE_BET, ModeManager.MODE_STATS]:
                # Режимы 2, 3, 4: Требуют загруженные кошельки
                wallet_proxies = mode_manager.get_wallets()
                
                if not wallet_proxies:
                    print(f"\n{Fore.RED}Нет кошельков для работы.{Style.RESET_ALL}")
                    print(f"{Fore.YELLOW}Используйте режим 1 для настройки кошельков.{Style.RESET_ALL}\n")
                    continue
                
                if mode == ModeManager.MODE_DAILY:
                    # Режим 2: Дейлик
                    mode_daily(wallet_proxies)
                
                elif mode == ModeManager.MODE_BET:
                    # Режим 3: Ставки
                    mode_bet(wallet_proxies)
                
                elif mode == ModeManager.MODE_STATS:
                    # Режим 4: Статистика
                    mode_stats(wallet_proxies)
            
        except KeyboardInterrupt:
            print(f"\n\n{Fore.YELLOW}Прервано пользователем.{Style.RESET_ALL}\n")
            break
        except ValueError as e:
            print(f"\n{Fore.RED}Ошибка конфигурации: {e}{Style.RESET_ALL}")
            print(f"{Fore.YELLOW}Пожалуйста, создайте файл private_keys.txt с приватными ключами{Style.RESET_ALL}")
            print(f"{Fore.YELLOW}Адреса кошельков будут извлечены автоматически из ключей{Style.RESET_ALL}")
            print(f"{Fore.YELLOW}Формат: один ключ на строку (hex строка, 64 символа){Style.RESET_ALL}\n")
        except Exception as e:
            print(f"\n{Fore.RED}Ошибка: {e}{Style.RESET_ALL}\n")
            import traceback
            traceback.print_exc()
