"""
Клиент для работы с фаусетами
"""
import requests
import time
import json
from urllib.parse import urlencode
from typing import Dict, Optional
from config import WALLET_ADDRESS


class CaptchaSolver:
    """Класс для решения hCaptcha и reCAPTCHA через sctg.xyz API"""
    
    def __init__(self, api_key: str, proxy: str = None):
        self.api_key = api_key
        # Используем IP адрес для более стабильной работы
        self.base_url = "https://157.180.15.203"  # IP адрес sctg.xyz
        self.proxy = proxy
    
    def solve_recaptcha(self, site_key: str, page_url: str, timeout: int = 300) -> Optional[str]:
        """
        Решает reCAPTCHA через sctg.xyz API
        
        Args:
            site_key: Ключ сайта reCAPTCHA
            page_url: URL страницы с капчей
            timeout: Максимальное время ожидания в секундах (по умолчанию 300)
        
        Returns:
            Токен решения или None
        """
        if not self.api_key:
            print("⚠ [DEBUG] API ключ не указан, решение капчи невозможно")
            return None
        
        print(f"\n{'='*60}")
        print(f"[DEBUG] Начало решения reCAPTCHA")
        print(f"{'='*60}")
        print(f"[DEBUG] Параметры:")
        print(f"  - Site Key: {site_key}")
        print(f"  - Page URL: {page_url}")
        print(f"  - Timeout: {timeout} сек")
        print(f"  - API Key: {self.api_key[:10]}...{self.api_key[-5:] if len(self.api_key) > 15 else ''}")
        print(f"  - Base URL: {self.base_url}")
        
        # Настраиваем прокси если указан (для решения капчи)
        # ВАЖНО: Используем тот же прокси, что и для запроса к Circle (если он установлен)
        proxies = None
        if self.proxy:
            proxies = self._format_proxy(self.proxy)
            print(f"[DEBUG] Прокси настроен для решения капчи: {self.proxy[:50]}...")
            print(f"[DEBUG] Форматированный прокси: {proxies}")
        else:
            print(f"[DEBUG] Прокси не используется для решения капчи (запрос к Circle тоже без прокси)")
        
        # Отправляем задачу на решение (GET запрос)
        # Используется reCAPTCHA v2 Enterprise (invisible) или v3
        # Пробуем разные методы для разных типов reCAPTCHA
        # Метод 1: userrecaptcha (для v2 и Enterprise)
        # Метод 2: userrecaptcha3 (для v3)
        # Circle использует reCAPTCHA Enterprise (invisible), пробуем оба метода
        methods_to_try = ['userrecaptcha', 'userrecaptcha3']
        
        for method in methods_to_try:
            submit_params = {
                'key': self.api_key,
                'method': method,
                'pageurl': page_url,
                'sitekey': site_key  # Используем sitekey (правильный параметр)
            }
            
            if method == 'userrecaptcha3':
                # Для v3 может потребоваться version=v3
                submit_params['version'] = 'v3'
            elif method == 'userrecaptcha':
                # Для reCAPTCHA Enterprise может потребоваться параметр enterprise
                # Пробуем добавить его для Circle (использует Enterprise)
                submit_params['enterprise'] = '1'
            
            query_string = urlencode(submit_params)
            submit_url = f"{self.base_url}/in.php?{query_string}"
            
            print(f"[DEBUG] Попытка решения с методом: {method}")
            print(f"[DEBUG] Submit URL: {submit_url[:100]}...")
            
            try:
                print(f"\n[DEBUG] Отправка запроса на решение капчи...")
                print(f"[DEBUG] Полный URL: {submit_url}")
                print(f"[DEBUG] Метод: GET")
                print(f"[DEBUG] Timeout: 30 сек")
                
                response = requests.get(submit_url, timeout=30, proxies=proxies)
                response.raise_for_status()
                
                print(f"\n[DEBUG] Ответ получен:")
                print(f"  - Status Code: {response.status_code}")
                print(f"  - Headers: {dict(response.headers)}")
                
                result = response.text.strip()
                print(f"  - Response Text: {result}")
                print(f"  - Response Length: {len(result)} символов")
                
                print(f"\n[DEBUG] Анализ ответа...")
                if "|" not in result:
                    print(f"[DEBUG] Неожиданный формат ответа: {result}")
                    if method == methods_to_try[-1]:  # Последний метод
                        print(f"⚠ Неожиданный формат ответа от сервиса капчи. Пропуск решения.")
                        print(f"{'='*60}\n")
                        return None
                    continue  # Пробуем следующий метод
                
                status, task_id = result.split("|", 1)
                print(f"[DEBUG] Распарсен ответ:")
                print(f"  - Status: {status}")
                print(f"  - Task ID: {task_id}")
                
                if status.upper() != "OK":
                    print(f"[DEBUG] Ошибка отправки капчи: {result}")
                    if method == methods_to_try[-1]:  # Последний метод
                        print(f"⚠ Ошибка отправки капчи: {result}. Пропуск решения.")
                        print(f"{'='*60}\n")
                        return None
                    continue  # Пробуем следующий метод
                
                # Если успешно, выходим из цикла методов и продолжаем с polling
                print(f"\n[DEBUG] ✓ Задача успешно создана с методом {method}")
                print(f"[DEBUG] Task ID: {task_id}")
                print(f"[DEBUG] Начинаем polling...")
                print(f"[DEBUG] Максимальное время ожидания: {timeout} сек")
                print(f"[DEBUG] Интервал проверки: 5 сек")
                break
                
            except Exception as e:
                print(f"[DEBUG] Ошибка при отправке запроса с методом {method}: {e}")
                if method == methods_to_try[-1]:  # Последний метод
                    print(f"⚠ Ошибка при отправке запроса: {e}")
                    print(f"{'='*60}\n")
                    return None
                continue  # Пробуем следующий метод
        else:
            # Если все методы не сработали
            print(f"⚠ Не удалось отправить капчу ни одним из методов. Пропуск решения.")
            print(f"{'='*60}\n")
            return None
        
        # Настраиваем прокси если указан (для polling)
        proxies = None
        if self.proxy:
            proxies = self._format_proxy(self.proxy)
            print(f"[DEBUG] Прокси настроен для polling: {self.proxy[:50]}...")
            print(f"[DEBUG] Форматированный прокси: {proxies}")
        else:
            print(f"[DEBUG] Прокси не используется для polling")
        
        # Ждем решения (polling) - как в официальном примере
        max_wait = timeout  # Максимальное время ожидания (5 минут в примере)
        poll_interval = 5  # секунд (как в примере)
        start_time = time.time()
        poll_count = 0
        
        try:
            while (time.time() - start_time) < max_wait:
                time.sleep(poll_interval)
                poll_count += 1
                
                # Get result (как в официальном примере)
                poll_params = {
                    'key': self.api_key,
                    'id': task_id,
                    'action': 'get'
                }
                poll_query = urlencode(poll_params)
                poll_url = f"{self.base_url}/res.php?{poll_query}"
                
                elapsed = time.time() - start_time
                print(f"\n[DEBUG] Poll #{poll_count} (прошло {elapsed:.1f}s)")
                print(f"[DEBUG] Poll URL: {poll_url[:100]}...")
                
                poll_response = requests.get(poll_url, timeout=30, proxies=proxies)
                poll_result = poll_response.text.strip()
                
                print(f"[DEBUG] Poll Response:")
                print(f"  - Status Code: {poll_response.status_code}")
                print(f"  - Response Text: {poll_result}")
                print(f"  - Response Length: {len(poll_result)} символов")
                
                # Проверяем, готов ли результат
                # Сервис может возвращать: NOT_READY, PROCESSING, CAPCHA_NOT_READY (альтернативное написание)
                poll_result_upper = poll_result.upper()
                print(f"[DEBUG] Проверка статуса:")
                print(f"  - Содержит 'NOT_READY': {'NOT_READY' in poll_result_upper}")
                print(f"  - Содержит 'PROCESSING': {'PROCESSING' in poll_result_upper}")
                print(f"  - Содержит 'CAPCHA_NOT_READY': {'CAPCHA_NOT_READY' in poll_result_upper}")
                
                # Проверяем, готов ли результат
                is_waiting = ("NOT_READY" in poll_result_upper or 
                             "PROCESSING" in poll_result_upper or 
                             "CAPCHA_NOT_READY" in poll_result_upper)
                
                if not is_waiting:
                    # Результат готов или ошибка
                    print(f"\n[DEBUG] ✓ Результат получен (не в статусе ожидания)")
                    print(f"[DEBUG] Полный результат: {poll_result}")
                    
                    # Обрабатываем результат
                    if "|" in poll_result:
                        print(f"[DEBUG] Результат содержит разделитель '|', парсим...")
                        # Формат: "OK|token" или "ERROR|message"
                        result_status, token = poll_result.split("|", 1)
                        print(f"[DEBUG] Распарсен результат:")
                        print(f"  - Status: {result_status}")
                        print(f"  - Token/Message: {token[:50]}..." if len(token) > 50 else f"  - Token/Message: {token}")
                        
                        if result_status.upper() == "OK":
                            print(f"\n[DEBUG] ✓✓✓ УСПЕХ! reCAPTCHA решена успешно!")
                            print(f"[DEBUG] Токен решения получен (длина: {len(token)} символов)")
                            print(f"{'='*60}\n")
                            return token
                        else:
                            # Обработка различных типов ошибок
                            error_msg = token if token else result_status
                            print(f"\n[DEBUG] ❌ Ошибка в результате:")
                            print(f"[DEBUG] Статус: {result_status}")
                            print(f"[DEBUG] Сообщение: {error_msg}")
                            
                            # Для UNSOLVABLE сразу прекращаем - сервис не может решить капчу
                            if "UNSOLVABLE" in error_msg.upper():
                                print(f"\n[DEBUG] ⚠ Сервис не может решить капчу: {error_msg}")
                                print(f"[DEBUG] Прекращаем ожидание и продолжаем без капчи")
                                print(f"{'='*60}\n")
                                return None  # Возвращаем None, чтобы продолжить без капчи
                            elif "WRONG_USER_KEY" in error_msg.upper():
                                print(f"\n⚠ Неверный API ключ: {error_msg}")
                                print(f"[DEBUG] Проверьте правильность API ключа в .env файле")
                                print(f"{'='*60}\n")
                                return None
                            elif "ZERO_BALANCE" in error_msg.upper():
                                print(f"\n⚠ Недостаточно средств на балансе: {error_msg}")
                                print(f"[DEBUG] Пополните баланс на sctg.xyz")
                                print(f"{'='*60}\n")
                                return None
                            else:
                                print(f"[DEBUG] Неизвестная ошибка, продолжаем ждать...")
                                print(f"[DEBUG] Осталось времени: {max_wait - elapsed:.1f} сек")
                                # Продолжаем polling для неизвестных ошибок
                                continue
                    else:
                        # Проверяем, не является ли это ошибкой без разделителя
                        print(f"[DEBUG] Результат не содержит разделитель '|'")
                        
                        if poll_result_upper.startswith("ERROR_"):
                            error_msg = poll_result
                            print(f"[DEBUG] Обнаружена ошибка без разделителя: {error_msg}")
                            
                            # Для UNSOLVABLE сразу прекращаем - сервис не может решить капчу
                            if "UNSOLVABLE" in error_msg.upper():
                                print(f"\n[DEBUG] ⚠ Сервис не может решить капчу: {error_msg}")
                                print(f"[DEBUG] Прекращаем ожидание и продолжаем без капчи")
                                print(f"{'='*60}\n")
                                return None  # Возвращаем None, чтобы продолжить без капчи
                            elif "WRONG_USER_KEY" in error_msg.upper():
                                print(f"\n⚠ Неверный API ключ: {error_msg}")
                                print(f"[DEBUG] Проверьте правильность API ключа в .env файле")
                                print(f"{'='*60}\n")
                                return None
                            elif "ZERO_BALANCE" in error_msg.upper():
                                print(f"\n⚠ Недостаточно средств на балансе: {error_msg}")
                                print(f"[DEBUG] Пополните баланс на sctg.xyz")
                                print(f"{'='*60}\n")
                                return None
                            else:
                                print(f"[DEBUG] Неизвестная ошибка, продолжаем ждать...")
                                print(f"[DEBUG] Осталось времени: {max_wait - elapsed:.1f} сек")
                                # Продолжаем polling для неизвестных ошибок
                                continue
                        # Возможно, это уже токен напрямую
                        elif len(poll_result) > 50:  # Токены обычно длинные
                            print(f"\n[DEBUG] ✓✓✓ УСПЕХ! Получен токен напрямую (без разделителя)")
                            print(f"[DEBUG] Длина токена: {len(poll_result)} символов")
                            print(f"{'='*60}\n")
                            return poll_result
                        else:
                            print(f"[DEBUG] ⚠ Неожиданный формат результата, продолжаем ждать...")
                            print(f"[DEBUG] Длина: {len(poll_result)} символов")
                            print(f"[DEBUG] Содержимое: {poll_result}")
                            print(f"[DEBUG] Осталось времени: {max_wait - elapsed:.1f} сек")
                            # Продолжаем polling
                            continue
                else:
                    # Все еще в процессе, продолжаем ждать
                    print(f"[DEBUG] Капча еще решается (статус: {poll_result}), продолжаем ждать...")
                    print(f"[DEBUG] Осталось времени: {max_wait - elapsed:.1f} сек")
                    continue
            
            # Если вышли из цикла по timeout
            elapsed_total = time.time() - start_time
            print(f"\n[DEBUG] ⚠ Превышено время ожидания")
            print(f"[DEBUG] Прошло времени: {elapsed_total:.1f} сек")
            print(f"[DEBUG] Максимальное время: {max_wait} сек")
            print(f"[DEBUG] Количество попыток polling: {poll_count}")
            print(f"[DEBUG] Последний результат: {poll_result if 'poll_result' in locals() else 'N/A'}")
            print(f"\n⚠ Капча не решена за {elapsed_total:.1f} секунд")
            print(f"[DEBUG] Возможные причины:")
            print(f"  - Капча слишком сложная для автоматического решения")
            print(f"  - Проблемы с прокси (недоступен или заблокирован)")
            print(f"  - Временные проблемы на стороне сервиса sctg.xyz")
            print(f"  - Неправильный site key или page URL")
            print(f"{'='*60}\n")
            return None
            
        except requests.exceptions.ProxyError as e:
            print(f"\n[DEBUG] ❌ ОШИБКА ПРОКСИ")
            print(f"[DEBUG] Тип ошибки: ProxyError")
            print(f"[DEBUG] Детали: {e}")
            print(f"[DEBUG] Прокси: {self.proxy}")
            import traceback
            traceback.print_exc()
            print(f"{'='*60}\n")
            return None
        except requests.exceptions.Timeout as e:
            print(f"\n[DEBUG] ❌ ТАЙМАУТ ЗАПРОСА")
            print(f"[DEBUG] Тип ошибки: Timeout")
            print(f"[DEBUG] Детали: {e}")
            import traceback
            traceback.print_exc()
            print(f"{'='*60}\n")
            return None
        except requests.exceptions.ConnectionError as e:
            print(f"\n[DEBUG] ❌ ОШИБКА ПОДКЛЮЧЕНИЯ")
            print(f"[DEBUG] Тип ошибки: ConnectionError")
            print(f"[DEBUG] Детали: {e}")
            print(f"[DEBUG] URL: {submit_url if 'submit_url' in locals() else 'N/A'}")
            import traceback
            traceback.print_exc()
            print(f"{'='*60}\n")
            return None
        except Exception as e:
            print(f"\n[DEBUG] ❌ НЕИЗВЕСТНАЯ ОШИБКА")
            print(f"[DEBUG] Тип ошибки: {type(e).__name__}")
            print(f"[DEBUG] Сообщение: {e}")
            import traceback
            print(f"[DEBUG] Полный traceback:")
            traceback.print_exc()
            print(f"{'='*60}\n")
            return None
    
    def solve_hcaptcha(self, site_key: str, page_url: str, timeout: int = 300) -> Optional[str]:
        """
        Решает hCaptcha через sctg.xyz API
        
        Args:
            site_key: Ключ сайта hCaptcha
            page_url: URL страницы с капчей
            timeout: Максимальное время ожидания в секундах (по умолчанию 300)
        
        Returns:
            Токен решения или None
        """
        if not self.api_key:
            return None
        
        # Отправляем задачу на решение (GET запрос)
        submit_params = {
            'key': self.api_key,
            'method': 'hcaptcha',
            'pageurl': page_url,
            'sitekey': site_key
        }
        
        query_string = urlencode(submit_params)
        submit_url = f"{self.base_url}/in.php?{query_string}"
        
        # Настраиваем прокси если указан
        proxies = None
        if self.proxy:
            proxies = self._format_proxy(self.proxy)
        
        try:
            print(f"Отправка запроса на решение капчи...")
            response = requests.get(submit_url, timeout=30, proxies=proxies)
            response.raise_for_status()
            
            result = response.text.strip()
            print(f"Ответ сервера: {result[:100]}...")
            
            # Проверяем формат ответа: "OK|task_id" или "ERROR|message"
            if "|" not in result:
                print(f"Неожиданный формат ответа: {result}")
                return None
            
            status, task_id = result.split("|", 1)
            
            if status.upper() != "OK":
                print(f"Ошибка отправки капчи: {result}")
                return None
            
            print(f"Капча отправлена на решение, ID задачи: {task_id}")
            
            # Ждем решения (polling)
            poll_interval = 5  # секунд
            start_time = time.time()
            
            while (time.time() - start_time) < timeout:
                time.sleep(poll_interval)
                
                # Get result (как в официальном примере)
                poll_params = {
                    'key': self.api_key,
                    'id': task_id,
                    'action': 'get'
                }
                poll_query = urlencode(poll_params)
                poll_url = f"{self.base_url}/res.php?{poll_query}"
                
                poll_response = requests.get(poll_url, timeout=30, proxies=proxies)
                poll_result = poll_response.text.strip()
                
                elapsed = time.time() - start_time
                print(f"  [{elapsed:.1f}s] Status: {poll_result[:50]}...")
                
                # Проверяем, готов ли результат
                poll_result_upper = poll_result.upper()
                is_waiting = ("NOT_READY" in poll_result_upper or 
                             "PROCESSING" in poll_result_upper or 
                             "CAPCHA_NOT_READY" in poll_result_upper)
                
                if not is_waiting:
                    # Результат готов или ошибка
                    if "|" in poll_result:
                        # Формат: "OK|token" или "ERROR|message"
                        result_status, token = poll_result.split("|", 1)
                        if result_status.upper() == "OK":
                            print(f"✓ Капча решена успешно!")
                            return token
                        else:
                            # Обработка различных типов ошибок
                            error_msg = token if token else result_status
                            
                            # Для UNSOLVABLE сразу прекращаем - сервис не может решить капчу
                            if "UNSOLVABLE" in error_msg.upper():
                                print(f"⚠ Сервис не может решить капчу: {error_msg}")
                                print(f"  Прекращаем ожидание и продолжаем без капчи")
                                return None  # Возвращаем None, чтобы продолжить без капчи
                            elif "WRONG_USER_KEY" in error_msg.upper():
                                print(f"⚠ Неверный API ключ: {error_msg}")
                                return None
                            elif "ZERO_BALANCE" in error_msg.upper():
                                print(f"⚠ Недостаточно средств на балансе: {error_msg}")
                                return None
                            else:
                                print(f"⚠ Неизвестная ошибка, продолжаем ждать...")
                                print(f"  Осталось времени: {timeout - elapsed:.1f} сек")
                                # Продолжаем polling для неизвестных ошибок
                                continue
                    else:
                        # Проверяем, не является ли это ошибкой без разделителя
                        poll_result_upper_check = poll_result.upper()
                        if poll_result_upper_check.startswith("ERROR_"):
                            error_msg = poll_result
                            
                            # Для UNSOLVABLE сразу прекращаем - сервис не может решить капчу
                            if "UNSOLVABLE" in error_msg.upper():
                                print(f"⚠ Сервис не может решить капчу: {error_msg}")
                                print(f"  Прекращаем ожидание и продолжаем без капчи")
                                return None  # Возвращаем None, чтобы продолжить без капчи
                            elif "WRONG_USER_KEY" in error_msg.upper():
                                print(f"⚠ Неверный API ключ: {error_msg}")
                                return None
                            elif "ZERO_BALANCE" in error_msg.upper():
                                print(f"⚠ Недостаточно средств на балансе: {error_msg}")
                                return None
                            else:
                                print(f"⚠ Неизвестная ошибка, продолжаем ждать...")
                                print(f"  Осталось времени: {timeout - elapsed:.1f} сек")
                                # Продолжаем polling для неизвестных ошибок
                                continue
                        # Возможно, это уже токен напрямую
                        elif len(poll_result) > 50:  # Токены обычно длинные
                            print(f"✓ Капча решена успешно!")
                            return poll_result
                        else:
                            print(f"⚠ Неожиданный формат результата, продолжаем ждать...")
                            print(f"  Осталось времени: {timeout - elapsed:.1f} сек")
                            # Продолжаем polling
                            continue
                else:
                    # Все еще в процессе, продолжаем ждать
                    print(f"  Капча еще решается (статус: {poll_result}), продолжаем ждать...")
                    print(f"  Осталось времени: {timeout - elapsed:.1f} сек")
                    continue
            
            # Если вышли из цикла по timeout
            elapsed_total = time.time() - start_time
            print(f"\n⚠ Превышено время ожидания решения капчи")
            print(f"  Прошло времени: {elapsed_total:.1f} сек")
            print(f"  Максимальное время: {timeout} сек")
            print(f"  Последний результат: {poll_result if 'poll_result' in locals() else 'N/A'}")
            return None
            
        except Exception as e:
            print(f"Ошибка при решении капчи: {e}")
            import traceback
            traceback.print_exc()
            return None
    
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
        
        if '@' in proxy:
            auth_part, server_part = proxy.split('@', 1)
            user, password = auth_part.split(':', 1)
            host, port = server_part.split(':', 1)
            proxy_url = f"http://{user}:{password}@{host}:{port}"
        else:
            proxy_url = f"http://{proxy}"
        
        return {
            'http': proxy_url,
            'https': proxy_url
        }


class CircleFaucet:
    """Клиент для Circle фаусета"""
    
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
        
        if '@' in proxy:
            auth_part, server_part = proxy.split('@', 1)
            user, password = auth_part.split(':', 1)
            host, port = server_part.split(':', 1)
            proxy_url = f"http://{user}:{password}@{host}:{port}"
        else:
            proxy_url = f"http://{proxy}"
        
        return {
            'http': proxy_url,
            'https': proxy_url
        }
    
    def __init__(self, wallet_address: str = None, captcha_solver: CaptchaSolver = None, proxy: str = None):
        self.wallet_address = wallet_address or WALLET_ADDRESS
        self.base_url = "https://faucet.circle.com/api/graphql"
        self.captcha_solver = captcha_solver
        self.session = requests.Session()
        
        # Site key для reCAPTCHA (обновлен пользователем)
        self.recaptcha_site_key = "6LcCqC8sAAAAAHGuWXnlpxcEYJD3lE_EFLebNnve"
        self.recaptcha_page_url = "https://faucet.circle.com/"
        
        # Настраиваем прокси если указан
        if proxy:
            proxy_dict = self._format_proxy(proxy)
            if proxy_dict:
                self.session.proxies.update(proxy_dict)
        
        self.session.headers.update({
            'accept': '*/*',
            'accept-encoding': 'gzip, deflate, br, zstd',
            'accept-language': 'ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7',
            'apollo-require-preflight': 'true',
            'content-type': 'application/json',
            'origin': 'https://faucet.circle.com',
            'referer': 'https://faucet.circle.com/',
            'sec-ch-ua': '"Not(A:Brand";v="8", "Chromium";v="144", "Google Chrome";v="144"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Windows"',
            'sec-fetch-dest': 'empty',
            'sec-fetch-mode': 'cors',
            'sec-fetch-site': 'same-origin',
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Safari/537.36'
        })
    
    def claim(self, recaptcha_token: str = None) -> Dict:
        """
        Клеймит фаусет Circle
        
        Args:
            recaptcha_token: Токен reCAPTCHA (если требуется)
        
        Returns:
            Ответ от API
        """
        # GraphQL запрос для клейма фаусета (на основе реального HAR файла)
        # Правильная мутация: RequestToken
        query = """
        mutation RequestToken($input: RequestTokenInput!) {
            requestToken(input: $input) {
                ...RequestTokenResponseInfo
                __typename
            }
        }
        
        fragment RequestTokenResponseInfo on RequestTokenResponse {
            amount
            blockchain
            contractAddress
            currency
            destinationAddress
            explorerLink
            hash
            status
            __typename
        }
        """
        
        # Только USDC в сети INK Sepolia
        blockchain_variants = [
            "INK",  # INK Sepolia
        ]
        
        print(f"\n[DEBUG] Circle Faucet: Начало клейма")
        print(f"[DEBUG] Wallet Address: {self.wallet_address}")
        
        # Получаем cookies перед решением капчи (важно для reCAPTCHA Enterprise)
        print(f"[DEBUG] Получение cookies с главной страницы Circle...")
        try:
            cookies_response = self.session.get("https://faucet.circle.com/", timeout=30)
            print(f"[DEBUG] Cookies получены: {len(self.session.cookies)} cookies")
            if self.session.cookies:
                print(f"[DEBUG] Список cookies: {list(self.session.cookies.keys())}")
        except Exception as e:
            print(f"[DEBUG] ⚠ Не удалось получить cookies: {e}")
        
        last_error = None
        for i, blockchain in enumerate(blockchain_variants, 1):
            print(f"\n[DEBUG] Попытка #{i}: Блокчейн = {blockchain}, Токен = USDC")
            
            # Решаем reCAPTCHA заново для каждого запроса
            # Токен может быть одноразовым или привязанным к конкретному запросу
            # ВАЖНО: Решаем капчу через ТОТ ЖЕ прокси, что и запрос к Circle
            # (Circle проверяет, что токен был решен с того же IP, с которого идет запрос)
            current_recaptcha_token = None
            if self.captcha_solver:
                print(f"Решение reCAPTCHA для попытки #{i}...")
                print("Примечание: Если на сайте не видно reCAPTCHA, это может быть невидимая версия (v3 или Enterprise)")
                
                # Используем тот же прокси, что и для запроса к Circle
                # Circle проверяет, что токен был решен с того же IP, с которого идет запрос
                # Получаем прокси из session (если он настроен)
                circle_proxy = None
                if hasattr(self.session, 'proxies') and self.session.proxies:
                    # Извлекаем прокси из session.proxies
                    # Формат: {'http': 'http://...', 'https': 'https://...'}
                    http_proxy = self.session.proxies.get('http') or self.session.proxies.get('https')
                    if http_proxy:
                        # Убираем префикс http:// для передачи в CaptchaSolver
                        circle_proxy = http_proxy.replace('http://', '').replace('https://', '')
                        print(f"⚠ ВАЖНО: Решаем капчу через ТОТ ЖЕ прокси, что и запрос к Circle: {circle_proxy[:50]}...")
                    else:
                        print(f"⚠ ВАЖНО: Решаем капчу БЕЗ прокси (запрос к Circle тоже без прокси)")
                else:
                    print(f"⚠ ВАЖНО: Решаем капчу БЕЗ прокси (запрос к Circle тоже без прокси)")
                
                # Устанавливаем прокси для решения капчи (чтобы IP совпадал)
                original_proxy = self.captcha_solver.proxy
                self.captcha_solver.proxy = circle_proxy  # Используем тот же прокси, что и для Circle
                
                current_recaptcha_token = self.captcha_solver.solve_recaptcha(
                    self.recaptcha_site_key,
                    self.recaptcha_page_url
                )
                
                # Восстанавливаем оригинальный прокси
                self.captcha_solver.proxy = original_proxy
                
                if not current_recaptcha_token:
                    print("⚠ Не удалось решить reCAPTCHA для этой попытки.")
                    print("⚠ Пропускаем эту попытку...")
                    last_error = "Не удалось решить reCAPTCHA"
                    continue
                
                print(f"[DEBUG] reCAPTCHA Token получен (первые 50 символов): {current_recaptcha_token[:50]}...")
                
                # Небольшая задержка после получения токена (имитация поведения браузера)
                import time
                delay = 2  # 2 секунды задержки
                print(f"[DEBUG] Задержка {delay} сек перед отправкой запроса (имитация поведения браузера)...")
                time.sleep(delay)
            elif recaptcha_token:
                # Если токен передан извне, используем его
                current_recaptcha_token = recaptcha_token
                print(f"[DEBUG] Используется переданный reCAPTCHA Token (первые 50 символов): {current_recaptcha_token[:50]}...")
            
            variables = {
                "input": {
                    "destinationAddress": self.wallet_address,
                    "token": "USDC",  # Только USDC поддерживается
                    "blockchain": blockchain
                }
            }
            
            payload = {
                "operationName": "RequestToken",
                "query": query,
                "variables": variables
            }
            
            # Добавляем токен reCAPTCHA (если есть)
            # Пробуем разные варианты отправки токена
            # Используем current_recaptcha_token (решенный для этого запроса)
            headers = {}
            if current_recaptcha_token:
                # Вариант 1: Токен в headers (как в HAR файле)
                headers = {
                    'recaptcha-action': 'request_token',
                    'recaptcha-token': current_recaptcha_token
                }
                # Также пробуем добавить в payload (на случай, если Circle проверяет оба места)
                payload["recaptchaToken"] = current_recaptcha_token
                print(f"[DEBUG] reCAPTCHA Token добавлен в headers и payload")
            else:
                print(f"[DEBUG] reCAPTCHA Token не установлен для этой попытки")
            
            print(f"[DEBUG] Payload:")
            print(f"  - operationName: {payload['operationName']}")
            print(f"  - destinationAddress: {variables['input']['destinationAddress']}")
            print(f"  - token: {variables['input']['token']}")
            print(f"  - blockchain: {variables['input']['blockchain']}")
            print(f"  - recaptchaToken: {'установлен' if current_recaptcha_token else 'не установлен'}")
            if current_recaptcha_token and 'recaptchaToken' in payload:
                print(f"  - recaptchaToken (первые 50 символов): {payload['recaptchaToken'][:50]}...")
            print(f"[DEBUG] URL: {self.base_url}")
            print(f"[DEBUG] Полный Payload JSON: {json.dumps(payload, indent=2)}")
            
            try:
                print(f"[DEBUG] Отправка POST запроса...")
                # Объединяем headers из session с дополнительными headers для reCAPTCHA
                request_headers = dict(self.session.headers)
                if headers:
                    request_headers.update(headers)
                
                # Логируем cookies для отладки
                print(f"[DEBUG] Cookies в запросе:")
                if self.session.cookies:
                    for cookie in self.session.cookies:
                        print(f"  - {cookie.name}: {cookie.value[:50]}..." if len(cookie.value) > 50 else f"  - {cookie.name}: {cookie.value}")
                else:
                    print(f"  - Cookies отсутствуют")
                
                # Логируем headers для отладки
                print(f"[DEBUG] Request Headers:")
                for key, value in request_headers.items():
                    if 'recaptcha' in key.lower():
                        print(f"  - {key}: {value[:50]}..." if len(str(value)) > 50 else f"  - {key}: {value}")
                    else:
                        print(f"  - {key}: {value[:100]}..." if len(str(value)) > 100 else f"  - {key}: {value}")
                
                response = self.session.post(self.base_url, json=payload, headers=request_headers, timeout=30)
                
                print(f"[DEBUG] Ответ получен:")
                print(f"  - Status Code: {response.status_code}")
                print(f"  - Headers: {dict(response.headers)}")
                print(f"  - Response Text: {response.text[:500]}")
                
                if response.status_code == 200:
                    result = response.json()
                    print(f"[DEBUG] Response JSON: {result}")
                    
                    # Проверяем, нет ли ошибок GraphQL
                    if "errors" not in result:
                        data = result.get("data", {}).get("requestToken", {})
                        status = data.get("status", "")
                        print(f"[DEBUG] GraphQL успешен, статус: {status}")
                        print(f"[DEBUG] Данные: {data}")
                        
                        if status == "success":
                            print(f"\n[DEBUG] ✓✓✓ УСПЕХ! Circle фаусет клеймлен!")
                            print(f"  Блокчейн: {blockchain}, Токен: USDC")
                            if data.get("amount"):
                                print(f"  Сумма: {data.get('amount')} {data.get('currency', '')}")
                            if data.get("hash"):
                                print(f"  Hash: {data.get('hash')}")
                            return result
                        else:
                            last_error = f"Status: {status}"
                            print(f"[DEBUG] Статус не 'success': {status}")
                            print(f"  Вариант {i} ({blockchain}): статус {status}")
                            continue
                    else:
                        errors = result.get("errors", [])
                        error_msg = errors[0].get("message", "Unknown error") if errors else "Unknown error"
                        error_code = errors[0].get("extensions", {}).get("code", "") if errors else ""
                        last_error = f"GraphQL error: {error_msg}"
                        print(f"[DEBUG] GraphQL ошибка:")
                        for err in errors:
                            print(f"  - {err}")
                        print(f"  Вариант {i} ({blockchain}): {error_msg[:100]}")
                        
                        # Специальная обработка для ошибки reCAPTCHA
                        if error_code == "RECAPTCHA_ERROR" or "ReCAPTCHA verification failed" in error_msg:
                            print(f"\n[DEBUG] ⚠⚠⚠ ПРОБЛЕМА С reCAPTCHA:")
                            print(f"[DEBUG] Circle отклоняет токен, несмотря на то, что:")
                            print(f"  - Токен успешно получен от сервиса sctg.xyz")
                            print(f"  - Токен отправлен в headers (recaptcha-action, recaptcha-token)")
                            print(f"  - Токен отправлен в payload (recaptchaToken)")
                            print(f"  - Cookies получены и отправляются ({len(self.session.cookies)} cookies)")
                            print(f"  - Используется тот же прокси для решения капчи и запроса")
                            print(f"  - Добавлена задержка перед отправкой запроса")
                            print(f"\n[DEBUG] Возможные причины:")
                            print(f"  1. Circle использует reCAPTCHA Enterprise, которая проверяет:")
                            print(f"     - Browser fingerprinting (отпечаток браузера)")
                            print(f"     - Поведение пользователя (движения мыши, клики и т.д.)")
                            print(f"     - Связь токена с конкретной браузерной сессией")
                            print(f"  2. Circle может проверять, что токен был решен в том же браузере/сессии")
                            print(f"  3. Возможно, требуется использование реального браузера (Selenium/Playwright)")
                            print(f"  4. Возможно, сервис sctg.xyz решает капчу не так, как ожидает Circle")
                            print(f"\n[DEBUG] Рекомендации:")
                            print(f"  - Попробуйте использовать другой сервис решения капчи")
                            print(f"  - Или используйте реальный браузер (Selenium/Playwright) для решения капчи")
                            print(f"  - Или проверьте, правильно ли настроен API ключ sctg.xyz")
                        
                        continue
                else:
                    last_error = f"HTTP {response.status_code}: {response.text[:200]}"
                    print(f"[DEBUG] HTTP ошибка: {response.status_code}")
                    print(f"[DEBUG] Response: {response.text[:500]}")
                    print(f"  Вариант {i} ({blockchain}) вернул HTTP {response.status_code}")
                    continue
            except requests.exceptions.RequestException as e:
                last_error = str(e)
                print(f"[DEBUG] Исключение RequestException:")
                print(f"  - Тип: {type(e).__name__}")
                print(f"  - Сообщение: {e}")
                if hasattr(e, 'response') and e.response is not None:
                    print(f"  - Response Status: {e.response.status_code}")
                    print(f"  - Response Text: {e.response.text[:500]}")
                import traceback
                traceback.print_exc()
                print(f"  Вариант {i} ({blockchain}) вызвал исключение: {str(e)[:100]}")
                continue
            except Exception as e:
                last_error = str(e)
                print(f"[DEBUG] Неизвестное исключение:")
                print(f"  - Тип: {type(e).__name__}")
                print(f"  - Сообщение: {e}")
                import traceback
                traceback.print_exc()
                print(f"  Вариант {i} ({blockchain}) вызвал исключение: {str(e)[:100]}")
                continue
        
        # Если все варианты не сработали
        raise Exception(f"Не удалось клеймнуть Circle фаусет после {len(blockchain_variants)} попыток. Последняя ошибка: {last_error}")


class InkonchainFaucet:
    """Клиент для Inkonchain Mystery фаусета"""
    
    def __init__(self, wallet_address: str = None, captcha_solver: CaptchaSolver = None, proxy: str = None):
        self.wallet_address = wallet_address or WALLET_ADDRESS
        self.base_url = "https://mystery-faucet.inkonchain.com/api/claim"
        self.captcha_solver = captcha_solver
        self.session = requests.Session()
        
        # Site key для hCaptcha
        self.hcaptcha_site_key = "69acb042-0738-48ee-9db8-53b6855a838a"
        self.hcaptcha_page_url = "https://inkonchain.com/"
        
        # Настраиваем прокси если указан
        if proxy:
            proxy_dict = self._format_proxy(proxy)
            if proxy_dict:
                self.session.proxies.update(proxy_dict)
        
        self.session.headers.update({
            'accept': '*/*',
            'accept-encoding': 'gzip, deflate, br, zstd',
            'accept-language': 'ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7',
            'content-type': 'application/json',
            'origin': 'https://inkonchain.com',
            'referer': 'https://inkonchain.com/',
            'sec-ch-ua': '"Not(A:Brand";v="8", "Chromium";v="144", "Google Chrome";v="144"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Windows"',
            'sec-fetch-dest': 'empty',
            'sec-fetch-mode': 'cors',
            'sec-fetch-site': 'same-site',
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
        
        if '@' in proxy:
            auth_part, server_part = proxy.split('@', 1)
            user, password = auth_part.split(':', 1)
            host, port = server_part.split(':', 1)
            proxy_url = f"http://{user}:{password}@{host}:{port}"
        else:
            proxy_url = f"http://{proxy}"
        
        return {
            'http': proxy_url,
            'https': proxy_url
        }
    
    def claim(self) -> Dict:
        """
        Клеймит Inkonchain фаусет
        
        Returns:
            Ответ от API
        """
        # По HAR видно, что фронтенд шлет на backend JSON вида:
        # {"address": "...", "chainId": 763373}
        # hCaptcha отрабатывает отдельно через запросы к hcaptcha.com,
        # backend же ожидает только адрес и chainId.

        payload = {
            "address": self.wallet_address,
            "chainId": 763373,  # Ink chainId из HAR
        }

        last_response_text = None

        try:
            # Preflight OPTIONS, как в браузере (на всякий случай)
            try:
                self.session.options(self.base_url, timeout=10)
            except Exception:
                pass

            response = self.session.post(self.base_url, json=payload, timeout=30)
            last_response_text = response.text[:500]

            if response.status_code == 200:
                try:
                    result = response.json()
                    print("✓ Inkonchain фаусет успешно клеймлен")
                    return result
                except Exception:
                    print("✓ Inkonchain фаусет успешно клеймлен (не JSON ответ)")
                    return {"success": True, "message": response.text[:100]}

            # Если не 200 — выводим понятную ошибку
            raise Exception(f"HTTP {response.status_code}: {response.text[:300]}")

        except requests.exceptions.RequestException as e:
            msg = str(e)
            if last_response_text:
                msg += f"\nПоследний ответ сервера: {last_response_text}"
            raise Exception(f"Ошибка запроса к Inkonchain фаусету: {msg}")


class FaucetManager:
    """Менеджер для работы со всеми фаусетами"""
    
    def __init__(self, wallet_address: str = None, captcha_api_key: str = None, proxy: str = None):
        self.wallet_address = wallet_address or WALLET_ADDRESS
        self.proxy = proxy
        self.captcha_solver = CaptchaSolver(captcha_api_key, proxy) if captcha_api_key else None
        
        self.circle_faucet = CircleFaucet(self.wallet_address, self.captcha_solver, proxy)
        self.inkonchain_faucet = InkonchainFaucet(self.wallet_address, self.captcha_solver, proxy)
    
    def claim_all(self) -> Dict[str, Dict]:
        """
        Клеймит все доступные фаусеты
        
        Returns:
            Словарь с результатами клейма каждого фаусета
        """
        results = {}
        
        # Circle фаусет
        print("Попытка клейма Circle фаусета...")
        try:
            results['circle'] = self.circle_faucet.claim()
            # Проверяем успешность клейма
            if isinstance(results['circle'], dict):
                data = results['circle'].get('data', {}).get('requestToken', {})
                if data.get('status') == 'success':
                    print("✅ Circle фаусет успешно клеймлен")
                    if data.get('amount'):
                        print(f"   Получено: {data.get('amount')} {data.get('currency', 'USDC')}")
                else:
                    status = data.get('status', 'unknown')
                    print(f"⚠ Circle фаусет: статус '{status}' (не success)")
                    results['circle'] = {"success": False, "status": status, "data": data}
            else:
                print("✅ Circle фаусет: запрос выполнен")
        except Exception as e:
            error_msg = str(e)
            results['circle'] = {"success": False, "error": error_msg}
            
            # Определяем тип ошибки для более понятного сообщения
            if "ReCAPTCHA verification failed" in error_msg or "RECAPTCHA_ERROR" in error_msg:
                print(f"⚠ Circle фаусет пропущен: Circle отклоняет токен reCAPTCHA")
                print(f"   Причина: Circle использует reCAPTCHA Enterprise с очень строгой проверкой")
                print(f"   Токен успешно получен от сервиса, но Circle проверяет дополнительные параметры")
                print(f"   (browser fingerprinting, связь с браузерной сессией и т.д.)")
                print(f"   Рекомендация: попробуйте другой сервис решения капчи или используйте реальный браузер")
                print(f"   Софт продолжит работу с другими фаусетами...")
            elif "UNSOLVABLE" in error_msg or "решить reCAPTCHA" in error_msg:
                print(f"⚠ Circle фаусет пропущен: не удалось решить reCAPTCHA")
                print(f"   Причина: сервис не смог решить капчу (возможно, слишком сложная или проблемы с прокси)")
            elif "WRONG_USER_KEY" in error_msg or "API ключ" in error_msg:
                print(f"❌ Circle фаусет: ошибка API ключа")
            elif "ZERO_BALANCE" in error_msg or "недостаточно средств" in error_msg:
                print(f"❌ Circle фаусет: недостаточно средств на балансе сервиса решения капчи")
            else:
                print(f"❌ Ошибка Circle фаусета: {error_msg[:150]}")
        
        # Небольшая задержка между запросами
        time.sleep(2)
        
        # Inkonchain фаусет
        print("Попытка клейма Inkonchain фаусета...")
        try:
            results['inkonchain'] = self.inkonchain_faucet.claim()
            print("✅ Inkonchain фаусет успешно клеймлен")
        except Exception as e:
            results['inkonchain'] = {"error": str(e)}
            print(f"❌ Ошибка Inkonchain фаусета: {e}")
        
        return results
