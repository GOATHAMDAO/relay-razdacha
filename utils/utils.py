from loguru import logger
from config import ERR_ATTEMPTS, TRANSACTIONS_DELAY
from .constants import DEFAULT_PRIVATE_KEY, DEFAULT_PROXIES
import sys
import time
import asyncio
import random


def intToDecimal(qty, decimal):
    """Конвертирует человекочитаемое число в wei"""
    return int(qty * int("".join(["1"] + ["0"] * decimal)))


def decimalToInt(price, decimal):
    """Конвертирует wei в человекочитаемое число"""
    return price / int("".join((["1"] + ["0"] * decimal)))


def round_decimal_value(value: int, rounding: int):
    """Округляет значение до указанного количества значащих цифр"""
    value = int(value)
    l = len(str(value))

    value = str(value)[:rounding]
    if int(value[-1]) > 5:
        value = int(value) + 1

    while len(str(value)) < l:
        value = str(value) + "0"

    return int(value)


def error_handler(error_msg, retries=ERR_ATTEMPTS):
    """Синхронный декоратор для обработки ошибок"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            for i in range(0, retries):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    logger.error(f"{error_msg}: {str(e)[:100]}")
                    logger.info(f'Повтор через 10 сек. Попыток осталось: {retries - i - 1}')
                    time.sleep(10)
                    if i == retries - 1:
                        return 0
        return wrapper
    return decorator


def async_error_handler(error_msg, retries=ERR_ATTEMPTS):
    """Асинхронный декоратор для обработки ошибок"""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            for i in range(0, retries):
                try:
                    return await func(*args, **kwargs)

                except TimeoutError as e:
                    logger.error(f"{error_msg}: TimeoutError - {str(e)[:250]}")
                    if i == retries - 1:
                        return 0
                    logger.info(f"TimeoutError: Повтор через 10 сек. Попыток осталось: {retries - i - 1}")
                    await asyncio.sleep(10)

                except Exception as e:
                    logger.error(f"{error_msg}: {str(e)}")
                    if i == retries - 1:
                        return 0
                    logger.info(f"Повтор через 10 сек. Попыток осталось: {retries - i - 1}")
                    await asyncio.sleep(10)

        return wrapper
    return decorator


def get_proxy():
    """Получает прокси из файла"""
    with open(DEFAULT_PROXIES, 'r') as f:
        lines = [line.strip() for line in f.readlines() if line.strip() and not line.startswith('#')]
        if len(lines) == 0:
            return None
        proxy = lines[0]
        return {
            'http': f'http://{proxy}',
            'https': f'http://{proxy}'
        }


async def async_sleep(seconds: int = None, address: str = None):
    """Асинхронная задержка между транзакциями"""
    if seconds is None:
        seconds = random.randint(*TRANSACTIONS_DELAY)
    
    prefix = f'{address}: ' if address else ''
    logger.info(f'{prefix}Ожидание {seconds} секунд...')
    await asyncio.sleep(seconds)


def sync_sleep(seconds: int = None, address: str = None):
    """Синхронная задержка между транзакциями"""
    if seconds is None:
        seconds = random.randint(*TRANSACTIONS_DELAY)
    
    prefix = f'{address}: ' if address else ''
    logger.info(f'{prefix}Ожидание {seconds} секунд...')
    time.sleep(seconds)


def load_private_key() -> str:
    """Загружает приватный ключ из файла"""
    with open(DEFAULT_PRIVATE_KEY, 'r', encoding='utf-8') as f:
        lines = [line.strip() for line in f.readlines() if line.strip() and not line.startswith('#')]
        if len(lines) == 0:
            logger.error('Приватный ключ не найден в файле private_key.txt')
            sys.exit(1)
        return lines[0]


def load_recipients() -> list:
    """Загружает адреса получателей из файла"""
    from .constants import DEFAULT_RECIPIENTS
    with open(DEFAULT_RECIPIENTS, 'r', encoding='utf-8') as f:
        recipients = [line.strip() for line in f.readlines() if line.strip() and not line.startswith('#')]
        if len(recipients) == 0:
            logger.error('Адреса получателей не найдены в файле recipients.txt')
            sys.exit(1)
        return recipients

