from relay.bridge import RelayBridge
from utils.constants import CHAIN_MAP, TG_CHANNEL, FAILED_RECIPIENTS
from utils.eth_account import AccountEVM
from utils.utils import (
    round_decimal_value, 
    intToDecimal, 
    sync_sleep,
    load_private_key,
    load_recipients,
    decimalToInt
)
from config import TRANSACTIONS_DELAY, AMOUNT_TYPE, CHAIN_FROM, CHAIN_TO, AMOUNT_RANGE

from typing import Literal
from loguru import logger
from eth_account import Account
import random
import sys
from pathlib import Path


class Runner:
    """Основной класс для запуска распределения ETH через Relay"""

    def __init__(self, private_key: str, recipients: list):
        self.private_key = private_key
        self.recipients = recipients
        self.address = Account.from_key(private_key).address

    def _reset_failed_recipients(self):
        """Очищает список ошибок перед новым запуском раздачи."""
        self._failed_recipients = set()
        failed_path = Path(FAILED_RECIPIENTS)

        try:
            failed_path.parent.mkdir(parents=True, exist_ok=True)
            failed_path.write_text('', encoding='utf-8')
            logger.info(f"Список ошибочных адресов сохранится в: {failed_path}")
        except Exception as e:
            logger.error(f"Не удалось подготовить файл failed.txt: {e}")

    def _record_failed_recipient(self, recipient: str):
        """Добавляет адрес в failed.txt один раз за текущий запуск."""
        recipient = str(recipient).strip()
        if not recipient:
            return

        if not hasattr(self, '_failed_recipients'):
            self._failed_recipients = set()
        if recipient in self._failed_recipients:
            return

        self._failed_recipients.add(recipient)
        failed_path = Path(FAILED_RECIPIENTS)

        try:
            failed_path.parent.mkdir(parents=True, exist_ok=True)
            with failed_path.open('a', encoding='utf-8') as file:
                file.write(f'{recipient}\n')
            logger.info(f"Адрес добавлен в failed.txt: {recipient}")
        except Exception as e:
            logger.error(f"Не удалось записать адрес {recipient} в failed.txt: {e}")

    def _generate_amount(
        self,
        chain_name: str,
        amount_range: list[int | float],
        amount_type: Literal['Percent', 'Absolute'] = AMOUNT_TYPE,
    ) -> int:
        """Генерирует сумму для отправки"""
        account = AccountEVM(chain_name, self.private_key)
        balance = account.get_balance()
        decimals = 18

        if balance == 0:
            raise Exception(f'{account.address}: Баланс аккаунта равен 0')

        if amount_type == 'Percent':
            if amount_range[0] == 100:
                return balance
            percent = random.uniform(*amount_range) if amount_range[0] != amount_range[1] else amount_range[0]
            amount_spent = balance * percent / 100
            amount_spent = round_decimal_value(amount_spent, random.randrange(2, 4))
        else:  # Absolute
            amount = random.uniform(*amount_range) if amount_range[0] != amount_range[1] else amount_range[0]
            amount_spent = intToDecimal(amount, decimals)
            amount_spent = round_decimal_value(amount_spent, random.randrange(2, 4))
            if amount_spent > balance:
                raise Exception(f'{account.address}: Указанная сумма превышает баланс аккаунта')

        return amount_spent

    def _single_bridge(
        self,
        chain_from: str,
        chain_to: str,
        recipient: str,
        amount: int
    ) -> int:
        """Выполняет один бридж на указанный адрес"""
        try:
            bridge = RelayBridge(chain_from, chain_to, self.private_key)
            return bridge.bridge_to_recipient(amount, recipient)
        except Exception as e:
            logger.error(f"Ошибка бриджа: {str(e)}")
            return 0

    def _get_balance(self, chain_name: str) -> float:
        """Получает баланс в человекочитаемом формате"""
        account = AccountEVM(chain_name, self.private_key)
        return account.get_balance_human()

    def _print_menu(self):
        """Выводит меню"""
        print("\n" + "="*50)
        print("  МЕНЮ")
        print("="*50)
        print("  1. 🚀 Запустить раздачу")
        print("  2. 💰 Проверить баланс")
        print("  3. 📋 Показать получателей")
        print("  4. ⚙️  Показать настройки")
        print("  5. ❌ Выход")
        print("="*50)

    def _get_choice(self) -> str:
        """Получает выбор пользователя"""
        while True:
            try:
                choice = input("\nВведите номер действия (1-5): ").strip()
                if choice in ['1', '2', '3', '4', '5']:
                    return choice
                print("❌ Неверный ввод. Введите число от 1 до 5.")
            except KeyboardInterrupt:
                return '5'

    def _confirm(self, message: str) -> bool:
        """Запрашивает подтверждение"""
        while True:
            try:
                answer = input(f"\n{message} (y/n): ").strip().lower()
                if answer in ['y', 'yes', 'да', 'д']:
                    return True
                if answer in ['n', 'no', 'нет', 'н']:
                    return False
                print("Введите 'y' или 'n'")
            except KeyboardInterrupt:
                return False

    def run_interface(self):
        """Запускает интерактивный интерфейс"""
        
        logger.opt(raw=True, colors=True).info(f"\n<cyan>📢 Telegram канал: {TG_CHANNEL}</cyan>\n")

        # Показываем текущие настройки из конфига
        self._show_config()

        while True:
            self._print_menu()
            choice = self._get_choice()

            try:
                if choice == '1':
                    self._run_distribution()
                elif choice == '2':
                    self._check_balance()
                elif choice == '3':
                    self._show_recipients()
                elif choice == '4':
                    self._show_config()
                elif choice == '5':
                    logger.info("До свидания!")
                    sys.exit()

            except KeyboardInterrupt:
                logger.info("\nВозврат в главное меню...")
                continue
            except Exception as e:
                logger.error(f"Ошибка: {e}")
                continue

    def _show_config(self):
        """Показывает текущие настройки из конфига"""
        amount_unit = 'ETH' if AMOUNT_TYPE == 'Absolute' else '%'
        
        logger.info(f"\n⚙️  Текущие настройки (config.py):")
        logger.info(f"   📤 Сеть отправки: {CHAIN_FROM}")
        logger.info(f"   📥 Сеть получения: {CHAIN_TO}")
        logger.info(f"   💵 Тип суммы: {AMOUNT_TYPE}")
        logger.info(f"   💰 Диапазон: {AMOUNT_RANGE[0]} - {AMOUNT_RANGE[1]} {amount_unit}")
        logger.info(f"   ⏱️  Задержка: {TRANSACTIONS_DELAY[0]} - {TRANSACTIONS_DELAY[1]} сек")
        logger.info(f"   👥 Получателей: {len(self.recipients)}")

    def _run_distribution(self):
        """Запускает процесс распределения ETH"""
        
        # Проверяем, что сети существуют
        if CHAIN_FROM not in CHAIN_MAP.nameToId:
            logger.error(f"❌ Сеть {CHAIN_FROM} не найдена! Проверьте config.py")
            return
        if CHAIN_TO not in CHAIN_MAP.nameToId:
            logger.error(f"❌ Сеть {CHAIN_TO} не найдена! Проверьте config.py")
            return

        # Показываем баланс
        balance = self._get_balance(CHAIN_FROM)
        logger.info(f"\n💰 Баланс: {balance:.6f} ETH в {CHAIN_FROM}")

        amount_unit = 'ETH' if AMOUNT_TYPE == 'Absolute' else '%'

        # Подтверждение
        logger.info(f"\n📊 Параметры раздачи:")
        logger.info(f"   📤 Из сети: {CHAIN_FROM}")
        logger.info(f"   📥 В сеть: {CHAIN_TO}")
        logger.info(f"   👥 Получателей: {len(self.recipients)}")
        logger.info(f"   💰 Сумма на каждого: {AMOUNT_RANGE[0]} - {AMOUNT_RANGE[1]} {amount_unit}")

        if not self._confirm("Начать раздачу?"):
            logger.info("Раздача отменена")
            return

        self._reset_failed_recipients()

        # Запуск раздачи
        logger.info(f"\n🚀 Начинаем раздачу на {len(self.recipients)} адресов...")

        successful = 0
        failed = 0

        for i, recipient in enumerate(self.recipients, 1):
            recipient_succeeded = False
            try:
                logger.info(f"\n[{i}/{len(self.recipients)}] Обработка: {recipient[:10]}...{recipient[-8:]}")
                
                # Генерируем сумму
                amount = self._generate_amount(CHAIN_FROM, AMOUNT_RANGE, AMOUNT_TYPE)
                
                amount_eth = decimalToInt(amount, 18)
                logger.info(f"   Сумма: {amount_eth:.6f} ETH")
                
                # Выполняем бридж
                result = self._single_bridge(CHAIN_FROM, CHAIN_TO, recipient, amount)
                
                if result == 1:
                    successful += 1
                    recipient_succeeded = True
                    logger.success(f"✅ Успешно отправлено!")
                else:
                    failed += 1
                    self._record_failed_recipient(recipient)
                    logger.error(f"❌ Ошибка отправки")

                # Задержка между транзакциями
                if i < len(self.recipients):
                    sync_sleep()

            except Exception as e:
                if not recipient_succeeded:
                    failed += 1
                    self._record_failed_recipient(recipient)
                logger.error(f"❌ Ошибка: {str(e)}")

        # Итоги
        logger.info(f"\n{'='*50}")
        logger.info(f"📊 ИТОГИ РАЗДАЧИ:")
        logger.info(f"   ✅ Успешно: {successful}")
        logger.info(f"   ❌ Ошибки: {failed}")
        logger.info(f"   📊 Всего: {len(self.recipients)}")
        logger.info(f"{'='*50}")

    def _check_balance(self):
        """Проверяет баланс в сетях из конфига"""
        logger.info(f"\n💰 Проверка баланса...")
        
        # Баланс в сети отправки
        balance_from = self._get_balance(CHAIN_FROM)
        logger.info(f"   {CHAIN_FROM}: {balance_from:.6f} ETH")
        
        # Если сети разные, показываем баланс и в целевой сети
        if CHAIN_FROM != CHAIN_TO:
            balance_to = self._get_balance(CHAIN_TO)
            logger.info(f"   {CHAIN_TO}: {balance_to:.6f} ETH")
        
        logger.info(f"   Адрес: {self.address}")

    def _show_recipients(self):
        """Показывает список получателей"""
        logger.info(f"\n📋 Список получателей ({len(self.recipients)} адресов):")
        for i, recipient in enumerate(self.recipients, 1):
            logger.info(f"   {i}. {recipient}")
