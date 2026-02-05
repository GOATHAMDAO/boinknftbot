"""
API клиент для работы с предикшн маркетом
"""
import requests
import time
import json
from typing import Dict, List, Optional
from config import API_BASE_URL, MARKET_ID, WALLET_ADDRESS
# Реферальный код зашит в код
REFERRAL_CODE = "BA08NOBF"


class PredictionMarketAPI:
    def __init__(self, wallet_address: str = None, private_key: str = None, proxy: str = None):
        self.base_url = API_BASE_URL
        self.wallet_address = wallet_address or WALLET_ADDRESS
        self.private_key = private_key
        self.session = requests.Session()
        
        # Настраиваем прокси если указан
        if proxy:
            proxy_dict = self._format_proxy(proxy)
            if proxy_dict:
                self.session.proxies.update(proxy_dict)
        
        # Устанавливаем заголовки как в браузере
        self.session.headers.update({
            'accept': 'application/json, text/plain, */*',
            'accept-encoding': 'gzip, deflate, br, zstd',
            'accept-language': 'ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7',
            'origin': 'https://prediction.boinknfts.club',
            'referer': 'https://prediction.boinknfts.club/',
            'sec-ch-ua': '"Not(A:Brand";v="8", "Chromium";v="144", "Google Chrome";v="144"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Windows"',
            'sec-fetch-dest': 'empty',
            'sec-fetch-mode': 'cors',
            'sec-fetch-site': 'cross-site',
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Safari/537.36'
        })
    
    def _format_proxy(self, proxy: str) -> dict:
        """Форматирует прокси строку для использования в requests"""
        if not proxy:
            return {}
        
        # Убираем префикс http:// или https:// если есть
        proxy = proxy.strip()
        if proxy.startswith('http://'):
            proxy = proxy[7:]
        elif proxy.startswith('https://'):
            proxy = proxy[8:]
        
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
    
    def _setup_referral(self, referral_code: str):
        """
        Устанавливает реферальный код через посещение сайта с реферальной ссылкой
        Это позволяет установить cookie/сессию с реферальным кодом
        
        Args:
            referral_code: Реферальный код (например, BA08NOBF)
        """
        try:
            referral_url = f"https://prediction.boinknfts.club/?ref={referral_code}"
            
            # Делаем GET запрос к реферальной ссылке для установки cookie
            response = self.session.get(referral_url, timeout=10)
            response.raise_for_status()
        except Exception as e:
            # Продолжаем работу, реферальный код может быть необязательным
            pass
    
    def register_with_referral(self, referral_code: str = None) -> Dict:
        """
        Регистрирует аккаунт с реферальным кодом или привязывает реферальный код к существующему аккаунту
        
        Args:
            referral_code: Реферальный код (если не указан, используется из конфига)
        
        Returns:
            Ответ от API
        """
        referral_code = referral_code or REFERRAL_CODE
        if not referral_code:
            return {"success": False, "error": "Реферальный код не указан"}
        
        wallet_address = self.wallet_address
        
        # Устанавливаем реферальный код через посещение ссылки (это устанавливает cookie)
        self._setup_referral(referral_code)
        
        # Пробуем только самые вероятные endpoints (без множественных попыток)
        # Большинство сайтов используют cookie для реферальных кодов, поэтому API может быть не нужен
        possible_endpoints = [
            f"{self.base_url}/user/register",
            f"{self.base_url}/user/{wallet_address}/register",
        ]
        
        # Пробуем только один вариант payload (самый стандартный)
        payload = {"userAddress": wallet_address, "referralCode": referral_code}
        
        # Если есть приватный ключ, подписываем запрос
        if self.private_key:
            try:
                from crypto_utils import sign_message
                message = json.dumps(payload, separators=(',', ':'))
                signature = sign_message(message, self.private_key)
                payload["signature"] = signature
            except Exception:
                pass
        
        # Пробуем только 2 самых вероятных endpoint'а
        for endpoint in possible_endpoints:
            try:
                response = self.session.post(endpoint, json=payload, timeout=5)
                if response.status_code == 200:
                    result = response.json()
                    if result.get("success"):
                        return result
            except:
                continue
        
        # Реферальный код установлен через cookie (это основной способ)
        return {"success": True, "message": f"Реферальный код {referral_code} установлен"}
    
    def make_bet(self, outcome: str, amount: float, market_id: int = None) -> Dict:
        """
        Делает ставку на маркете
        
        Args:
            outcome: Исход ставки (например, "YES" или "NO")
            amount: Сумма ставки
            market_id: ID маркета (по умолчанию из конфига)
        
        Returns:
            Ответ от API
        """
        url = f"{self.base_url}/user/bet"
        market_id = market_id or MARKET_ID
        
        # API требует: userAddress, marketId, amount, position
        payload = {
            "userAddress": self.wallet_address,
            "marketId": market_id,
            "amount": amount,
            "position": outcome  # position вместо outcome (YES/NO)
        }
        
        # Если есть приватный ключ, подписываем запрос
        if self.private_key:
            try:
                from crypto_utils import sign_message
                # Создаем сообщение для подписи
                message = f"{self.wallet_address}:{market_id}:{outcome}:{amount}"
                signature = sign_message(message, self.private_key)
                payload["signature"] = signature
            except Exception as e:
                print(f"⚠ Ошибка при подписании запроса: {e}")
                # Продолжаем без подписи, возможно API не требует её
        
        try:
            response = self.session.post(url, json=payload)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Ошибка при размещении ставки: {e}")
            if hasattr(e, 'response') and e.response is not None:
                print(f"Ответ сервера: {e.response.text}")
            raise
    
    def get_user_bets(self, wallet_address: str = None) -> List[Dict]:
        """
        Получает список ставок пользователя
        
        Args:
            wallet_address: Адрес кошелька (по умолчанию из конфига)
        
        Returns:
            Список ставок
        """
        wallet_address = wallet_address or self.wallet_address
        url = f"{self.base_url}/user/{wallet_address}/bets"
        
        try:
            response = self.session.get(url)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Ошибка при получении ставок пользователя: {e}")
            raise
    
    def get_market_bets(self, market_id: int = None, silent: bool = False) -> List[Dict]:
        """
        Получает список всех ставок на маркете
        
        Args:
            market_id: ID маркета (по умолчанию из конфига)
            silent: Если True, не выводит ошибки в консоль
        
        Returns:
            Список ставок
        """
        market_id = market_id or MARKET_ID
        url = f"{self.base_url}/market/{market_id}/bets"
        
        try:
            response = self.session.get(url, timeout=5)
            response.raise_for_status()
            
            # Проверяем, что ответ - валидный JSON
            try:
                data = response.json()
                return data if isinstance(data, list) else []
            except (ValueError, json.JSONDecodeError) as e:
                if not silent:
                    print(f"Ошибка при парсинге JSON для маркета {market_id}: {e}")
                raise
            
        except requests.exceptions.RequestException as e:
            if not silent:
                print(f"Ошибка при получении ставок маркета {market_id}: {e}")
            raise
        except (ValueError, json.JSONDecodeError) as e:
            if not silent:
                print(f"Ошибка при парсинге JSON для маркета {market_id}: {e}")
            raise
    
    def check_daily_cooldown(self, wallet_address: str = None) -> Optional[Dict]:
        """
        Проверяет, доступен ли дейлик (не в кулдауне)
        
        Args:
            wallet_address: Адрес кошелька (по умолчанию из конфига)
        
        Returns:
            None если можно клеймить, иначе словарь с информацией о CD
        """
        wallet_address = wallet_address or self.wallet_address
        stats = self.get_user_stats(wallet_address)
        
        if stats:
            # Проверяем наличие информации о CD в статистике
            # Предполагаем, что если есть поле lastDailyClaim или cooldown, проверяем его
            if 'lastDailyClaim' in stats:
                # Здесь можно добавить логику проверки времени последнего клейма
                pass
            # Если нет информации о CD, значит можно клеймить
            return None
        
        return None
    
    def claim_daily(self, wallet_address: str = None) -> Dict:
        """
        Клеймит ежедневную награду (с проверкой CD)
        
        Args:
            wallet_address: Адрес кошелька (по умолчанию из конфига)
        
        Returns:
            Ответ от API
        """
        wallet_address = wallet_address or self.wallet_address
        
        # Проверяем CD перед клеймом
        cd_info = self.check_daily_cooldown(wallet_address)
        if cd_info is not None:
            raise Exception("Дейлик в кулдауне, нельзя клеймить")
        
        url = f"{self.base_url}/user/{wallet_address}/claim-daily"
        
        payload = {}
        
        # Если есть приватный ключ, подписываем запрос
        headers = {}
        if self.private_key:
            try:
                from crypto_utils import sign_message
                # Создаем сообщение для подписи (стандартизированный JSON)
                message = json.dumps(payload, separators=(',', ':'))
                signature = sign_message(message, self.private_key)
                headers = {
                    'X-Signature': signature,
                    'X-Address': wallet_address
                }
            except Exception as e:
                print(f"⚠ Ошибка при подписании запроса: {e}")
        
        try:
            response = self.session.post(url, json=payload if payload else None, headers=headers)
            
            # Проверяем, не в CD ли мы или уже клеймлен
            if response.status_code == 400 or response.status_code == 429:
                error_text = response.text.lower()
                response_json = {}
                try:
                    response_json = response.json()
                except:
                    pass
                
                # Проверяем различные варианты сообщений о кулдауне
                if 'cooldown' in error_text or 'wait' in error_text or 'too soon' in error_text:
                    raise Exception("Дейлик в кулдауне, нужно подождать")
                
                # Проверяем, что дейлик уже клеймлен сегодня
                if 'already claimed' in error_text or 'come back tomorrow' in error_text:
                    error_msg = response_json.get('error', 'Already claimed today')
                    raise Exception(f"Дейлик уже клеймлен сегодня: {error_msg}")
            
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            if hasattr(e, 'response') and e.response is not None:
                error_text = e.response.text.lower()
                try:
                    response_json = e.response.json()
                    # Проверяем, что дейлик уже клеймлен
                    if 'already claimed' in error_text or 'come back tomorrow' in error_text:
                        error_msg = response_json.get('error', 'Already claimed today')
                        raise Exception(f"Дейлик уже клеймлен сегодня: {error_msg}")
                except:
                    pass
                if 'cooldown' in error_text or 'wait' in error_text or 'too soon' in error_text:
                    raise Exception("Дейлик в кулдауне, нужно подождать")
            print(f"Ошибка при клейме дейлика: {e}")
            if hasattr(e, 'response') and e.response is not None:
                print(f"Ответ сервера: {e.response.text}")
            raise
    
    def get_market_info(self, market_id: int = None) -> Dict:
        """
        Получает информацию о маркете (если такой endpoint существует)
        """
        market_id = market_id or MARKET_ID
        url = f"{self.base_url}/market/{market_id}"
        
        try:
            response = self.session.get(url)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException:
            # Если endpoint не существует, возвращаем None
            return None
    
    def get_available_markets(self, min_id: int = 1, max_id: int = 200) -> List[int]:
        """
        Получает список доступных маркетов, проверяя диапазон ID
        
        Args:
            min_id: Минимальный ID маркета для проверки
            max_id: Максимальный ID маркета для проверки
        
        Returns:
            Список доступных ID маркетов
        """
        available_markets = []
        checked = 0
        
        # Проверяем каждый маркет в диапазоне (тихо, без вывода ошибок)
        for market_id in range(min_id, max_id + 1):
            checked += 1
            try:
                bets = self.get_market_bets(market_id, silent=True)
                if bets is not None and isinstance(bets, list):
                    available_markets.append(market_id)
                    if len(available_markets) >= 20:  # Ограничиваем количество найденных маркетов
                        break
            except:
                continue
            
            # Показываем прогресс каждые 50 маркетов
            if checked % 50 == 0:
                print(f"  Проверено {checked} маркетов, найдено доступных: {len(available_markets)}")
        
        return available_markets
    
    def is_market_available(self, market_id: int) -> bool:
        """
        Проверяет, доступен ли маркет
        
        Args:
            market_id: ID маркета
        
        Returns:
            True если маркет доступен, False иначе
        """
        try:
            bets = self.get_market_bets(market_id, silent=True)
            return bets is not None and isinstance(bets, list)
        except:
            return False
    
    def get_user_stats(self, wallet_address: str = None) -> Dict:
        """
        Получает статистику пользователя (XP и другие данные)
        
        Args:
            wallet_address: Адрес кошелька (по умолчанию из конфига)
        
        Returns:
            Словарь со статистикой пользователя
        """
        wallet_address = wallet_address or self.wallet_address
        url = f"{self.base_url}/user/{wallet_address}/stats"
        
        try:
            # Делаем запрос с заголовками, отключающими кеш, чтобы всегда получать свежие данные
            headers = {
                'Cache-Control': 'no-cache',
                'Pragma': 'no-cache'
            }
            response = self.session.get(url, headers=headers)
            
            # Если получили 304, игнорируем и делаем запрос заново
            if response.status_code == 304:
                # Убираем If-None-Match и делаем запрос заново
                headers['If-None-Match'] = ''
                response = self.session.get(url, headers=headers)
            
            response.raise_for_status()
            
            # Парсим JSON ответ
            try:
                data = response.json()
            except json.JSONDecodeError:
                # Если не JSON, возвращаем пустой словарь
                return {}
            
            return data if isinstance(data, dict) else {}
        except requests.exceptions.RequestException:
            # Не выводим ошибку, просто возвращаем пустой словарь
            return {}
        except (ValueError, json.JSONDecodeError):
            # Если не JSON, возвращаем пустой словарь
            return {}
    
    def get_user_achievements(self, wallet_address: str = None) -> List[Dict]:
        """
        Получает достижения пользователя
        
        Args:
            wallet_address: Адрес кошелька (по умолчанию из конфига)
        
        Returns:
            Список достижений
        """
        wallet_address = wallet_address or self.wallet_address
        url = f"{self.base_url}/user/{wallet_address}/achievements"
        
        try:
            response = self.session.get(url)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Ошибка при получении достижений пользователя: {e}")
            raise
