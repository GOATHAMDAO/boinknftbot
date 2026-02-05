"""
Утилиты для работы с криптографией и подписью транзакций
"""
from eth_account import Account
from eth_account.messages import encode_defunct
from typing import Optional
import hashlib


def sign_message(message: str, private_key: str) -> str:
    """
    Подписывает сообщение приватным ключом (EIP-191)
    
    Args:
        message: Сообщение для подписания
        private_key: Приватный ключ (с префиксом 0x или без)
    
    Returns:
        Подпись в формате hex
    """
    # Убираем префикс 0x если есть
    if private_key.startswith('0x'):
        private_key = private_key[2:]
    
    # Создаем аккаунт из приватного ключа
    account = Account.from_key(private_key)
    
    # Кодируем сообщение по стандарту EIP-191
    message_encoded = encode_defunct(text=message)
    
    # Подписываем сообщение
    signed_message = account.sign_message(message_encoded)
    
    return signed_message.signature.hex()


def verify_address_from_key(private_key: str) -> str:
    """
    Получает адрес кошелька из приватного ключа
    
    Args:
        private_key: Приватный ключ (с префиксом 0x или без)
    
    Returns:
        Адрес кошелька
    """
    # Убираем префикс 0x если есть
    if private_key.startswith('0x'):
        private_key = private_key[2:]
    
    # Создаем аккаунт из приватного ключа
    account = Account.from_key(private_key)
    
    return account.address


def verify_key_address_match(private_key: str, address: str) -> bool:
    """
    Проверяет, соответствует ли приватный ключ адресу кошелька
    
    Args:
        private_key: Приватный ключ
        address: Адрес кошелька
    
    Returns:
        True если ключ соответствует адресу, False иначе
    """
    try:
        derived_address = verify_address_from_key(private_key)
        # Сравниваем в нижнем регистре
        return derived_address.lower() == address.lower()
    except Exception:
        return False
