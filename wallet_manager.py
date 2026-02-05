"""
Менеджер для работы с кошельками и прокси
"""
import os
from typing import List, Tuple, Optional
from dataclasses import dataclass


@dataclass
class WalletProxy:
    """Связка кошелька, приватного ключа и прокси"""
    wallet_address: str
    private_key: Optional[str] = None
    proxy: Optional[str] = None
    
    def __repr__(self):
        proxy_str = self.proxy if self.proxy else "без прокси"
        key_str = "есть ключ" if self.private_key else "нет ключа"
        return f"WalletProxy(address={self.wallet_address[:10]}..., key={key_str}, proxy={proxy_str})"


class WalletManager:
    """Менеджер для загрузки кошельков, приватных ключей и прокси из файлов"""
    
    def __init__(self, wallets_file: str = "wallets.txt", private_keys_file: str = "private_keys.txt", proxies_file: str = "proxies.txt"):
        self.wallets_file = wallets_file
        self.private_keys_file = private_keys_file
        self.proxies_file = proxies_file
        self.wallet_proxies: List[WalletProxy] = []
    
    def load_wallets(self) -> List[str]:
        """
        Загружает список кошельков из файла
        
        Returns:
            Список адресов кошельков
        """
        wallets = []
        
        if not os.path.exists(self.wallets_file):
            print(f"⚠ Файл {self.wallets_file} не найден!")
            return wallets
        
        try:
            with open(self.wallets_file, 'r', encoding='utf-8') as f:
                for line_num, line in enumerate(f, 1):
                    line = line.strip()
                    # Пропускаем пустые строки и комментарии
                    if not line or line.startswith('#'):
                        continue
                    
                    # Проверяем формат адреса (должен начинаться с 0x и быть длиной 42 символа)
                    if line.startswith('0x') and len(line) == 42:
                        wallets.append(line)
                    else:
                        print(f"⚠ Строка {line_num} в {self.wallets_file} не является валидным адресом кошелька: {line}")
            
            print(f"✓ Загружено {len(wallets)} кошельков из {self.wallets_file}")
            return wallets
            
        except Exception as e:
            print(f"❌ Ошибка при чтении файла {self.wallets_file}: {e}")
            return wallets
    
    def load_private_keys(self) -> List[str]:
        """
        Загружает список приватных ключей из файла
        
        Returns:
            Список приватных ключей
        """
        private_keys = []
        
        if not os.path.exists(self.private_keys_file):
            print(f"⚠ Файл {self.private_keys_file} не найден! Транзакции не будут подписываться.")
            return private_keys
        
        try:
            with open(self.private_keys_file, 'r', encoding='utf-8') as f:
                for line_num, line in enumerate(f, 1):
                    line = line.strip()
                    # Пропускаем пустые строки и комментарии
                    if not line or line.startswith('#'):
                        continue
                    
                    # Проверяем формат приватного ключа (должен быть hex строкой)
                    # Может быть с префиксом 0x или без
                    key = line.replace('0x', '')
                    if len(key) == 64 and all(c in '0123456789abcdefABCDEF' for c in key):
                        private_keys.append(line)
                    else:
                        print(f"⚠ Строка {line_num} в {self.private_keys_file} не является валидным приватным ключом")
            
            print(f"✓ Загружено {len(private_keys)} приватных ключей из {self.private_keys_file}")
            return private_keys
            
        except Exception as e:
            print(f"❌ Ошибка при чтении файла {self.private_keys_file}: {e}")
            return private_keys
    
    def load_proxies(self) -> List[str]:
        """
        Загружает список прокси из файла
        
        Returns:
            Список прокси в формате "host:port" или "user:pass@host:port"
        """
        proxies = []
        
        if not os.path.exists(self.proxies_file):
            print(f"⚠ Файл {self.proxies_file} не найден. Прокси не будут использоваться.")
            return proxies
        
        try:
            with open(self.proxies_file, 'r', encoding='utf-8') as f:
                for line_num, line in enumerate(f, 1):
                    line = line.strip()
                    # Пропускаем пустые строки и комментарии
                    if not line or line.startswith('#'):
                        continue
                    
                    proxies.append(line)
            
            print(f"✓ Загружено {len(proxies)} прокси из {self.proxies_file}")
            return proxies
            
        except Exception as e:
            print(f"❌ Ошибка при чтении файла {self.proxies_file}: {e}")
            return proxies
    
    def get_wallet_proxies(self) -> List[WalletProxy]:
        """
        Загружает кошельки, приватные ключи и прокси, связывает их по порядку
        Если есть приватные ключи, адреса извлекаются из них автоматически
        
        Returns:
            Список WalletProxy объектов
        """
        wallets = self.load_wallets()
        private_keys = self.load_private_keys()
        proxies = self.load_proxies()
        
        # Если есть приватные ключи, извлекаем адреса из них
        if private_keys:
            print("Извлечение адресов кошельков из приватных ключей...")
            from crypto_utils import verify_address_from_key
            
            extracted_wallets = []
            for i, private_key in enumerate(private_keys, 1):
                try:
                    address = verify_address_from_key(private_key)
                    extracted_wallets.append(address)
                    print(f"  {i}. Извлечен адрес: {address}")
                except Exception as e:
                    print(f"  ⚠ Ошибка при извлечении адреса из ключа {i}: {e}")
                    # Если не удалось извлечь, используем адрес из wallets.txt если есть
                    if i <= len(wallets):
                        extracted_wallets.append(wallets[i-1])
                        print(f"     Используется адрес из wallets.txt: {wallets[i-1]}")
                    else:
                        raise ValueError(f"Не удалось извлечь адрес из приватного ключа на строке {i} и нет соответствующего адреса в wallets.txt!")
            
            # Если есть адреса в wallets.txt, проверяем соответствие
            if wallets:
                print("\nПроверка соответствия адресов из wallets.txt и приватных ключей...")
                for i, (extracted, wallet_file) in enumerate(zip(extracted_wallets, wallets), 1):
                    if extracted.lower() != wallet_file.lower():
                        print(f"  ⚠ Строка {i}: Адрес из ключа ({extracted}) не совпадает с адресом из wallets.txt ({wallet_file})")
                        print(f"     Используется адрес из приватного ключа: {extracted}")
            
            wallets = extracted_wallets
        
        # Если нет ни ключей, ни адресов - ошибка
        if not wallets and not private_keys:
            raise ValueError(f"Не найдено ни одного кошелька в {self.wallets_file} и ни одного приватного ключа в {self.private_keys_file}!")
        
        if not wallets:
            raise ValueError(f"Не удалось извлечь адреса из приватных ключей!")
        
        wallet_proxies = []
        
        for index, wallet in enumerate(wallets):
            # Если есть приватный ключ для этого индекса, используем его
            private_key = private_keys[index] if index < len(private_keys) else None
            
            # Если есть прокси для этого индекса, используем его
            proxy = proxies[index] if index < len(proxies) else None
            
            wallet_proxy = WalletProxy(
                wallet_address=wallet,
                private_key=private_key,
                proxy=proxy
            )
            wallet_proxies.append(wallet_proxy)
        
        self.wallet_proxies = wallet_proxies
        
        # Выводим информацию о связках
        print(f"\n{'='*60}")
        print(f"СВЯЗКИ КОШЕЛЬКОВ, КЛЮЧЕЙ И ПРОКСИ:")
        print(f"{'='*60}")
        for i, wp in enumerate(wallet_proxies, 1):
            key_info = "✓ есть ключ" if wp.private_key else "✗ нет ключа"
            proxy_info = wp.proxy if wp.proxy else "без прокси"
            print(f"{i}. {wp.wallet_address[:20]}... -> ключ: {key_info}, прокси: {proxy_info}")
        print(f"{'='*60}\n")
        
        return wallet_proxies
    
    def format_proxy_for_requests(self, proxy: str) -> dict:
        """
        Форматирует прокси строку для использования в requests
        
        Args:
            proxy: Прокси в формате "host:port" или "user:pass@host:port"
        
        Returns:
            Словарь с настройками прокси для requests
        """
        if not proxy:
            return {}
        
        # Если прокси содержит @, значит есть авторизация
        if '@' in proxy:
            # Формат: user:pass@host:port
            auth_part, server_part = proxy.split('@', 1)
            user, password = auth_part.split(':', 1)
            host, port = server_part.split(':', 1)
            
            proxy_url = f"http://{user}:{password}@{host}:{port}"
        else:
            # Формат: host:port
            proxy_url = f"http://{proxy}"
        
        return {
            'http': proxy_url,
            'https': proxy_url
        }
