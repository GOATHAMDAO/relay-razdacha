from utils.eth_account import AccountEVM
from utils.constants import CHAIN_MAP, ZERO_ADDRESS
from .constants import RELAY_URL, RELAY_API_URL
from utils.utils import decimalToInt
import config
from loguru import logger
import requests
import time


class RelayBridge(AccountEVM):
    """
    Класс для бриджа ETH через Relay API
    Позволяет отправлять ETH с одной сети на другую на указанный адрес
    """

    def __init__(
        self,
        chain_from: str,
        chain_to: str,
        private_key: str,
        proxy: bool = False
    ):
        self._chain_from = chain_from
        self._chain_to = chain_to
        self.url = RELAY_URL
        self.api_url = RELAY_API_URL
        self.chain_map = CHAIN_MAP

        super().__init__(chain_from, private_key)

    def _quote_tx_data(
        self,
        amount: int,
        recipient: str,
        from_contract: str = ZERO_ADDRESS,
        to_contract: str = ZERO_ADDRESS
    ):
        """
        Получает данные транзакции от Relay API
        """
        headers = {
            'accept': 'application/json, text/plain, */*',
            'content-type': 'application/json',
            'referer': f'{self.url}bridge/{self._chain_from.lower()}?fromChainId={self.chain_map.nameToId[self._chain_from]}&fromCurrency={from_contract}&toCurrency={to_contract}'
        }

        body = {
            'amount': str(amount),
            'destinationChainId': self.chain_map.nameToId[self._chain_to],
            'destinationCurrency': to_contract,
            'originChainId': self.chain_map.nameToId[self._chain_from],
            'originCurrency': from_contract,
            'recipient': recipient,
            'referrer': 'relay.link/swap',
            'tradeType': 'EXACT_INPUT',
            'useExternalLiquidity': False,
            'user': self.address,
            'refundTo': self.address,
        }
        slippage_tolerance_bps = getattr(config, 'SLIPPAGE_TOLERANCE_BPS', None)
        if slippage_tolerance_bps is not None:
            body['slippageTolerance'] = str(slippage_tolerance_bps)

        try:
            response = requests.post(
                self.api_url + 'quote/v2',
                headers=headers,
                json=body,
                proxies=self.proxy,
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                steps = data.get('steps', [])
                step = next(
                    (item for item in steps if item.get('kind') == 'transaction' and item.get('items')),
                    None,
                )
                if step:
                    item = step['items'][0]
                    return {
                        'tx': item['data'],
                        'request_id': step.get('requestId'),
                    }
                else:
                    logger.error(f"Неожиданный формат ответа от Relay API: {data}")
                    return None
            else:
                if response.status_code == 400:
                    try:
                        msg = response.json().get('message', 'Unknown error')
                        logger.error(f"Relay API error: {msg}")
                    except:
                        pass
                logger.error(f"HTTP Error: {response.status_code}")
                return None
        except Exception as e:
            logger.error(f"Ошибка запроса к Relay API: {e}")
            return None

    def _wait_for_relay(self, request_id: str) -> bool:
        """Ждёт, пока Relay подтвердит fill или возвратит депозит."""
        deadline = time.time() + config.RELAY_STATUS_TIMEOUT

        while time.time() < deadline:
            try:
                response = requests.get(
                    self.api_url + 'intents/status/v3',
                    params={'requestId': request_id},
                    proxies=self.proxy,
                    timeout=30,
                )

                if response.status_code != 200:
                    logger.warning(f"Relay status HTTP {response.status_code}")
                else:
                    status_data = response.json()
                    status = status_data.get('status')

                    if status == 'success':
                        logger.success(f"Relay fill подтверждён: {request_id}")
                        return True

                    if status in {'refund', 'refunded', 'failure'}:
                        details = status_data.get('details', 'без подробностей')
                        logger.error(f"Relay завершил заявку статусом {status}: {details}")
                        return False

                    logger.info(f"Relay status: {status or 'unknown'}")
            except Exception as e:
                logger.warning(f"Ошибка проверки статуса Relay: {str(e)[:120]}")

            time.sleep(config.RELAY_STATUS_POLL_INTERVAL)

        logger.error(f"Таймаут ожидания финального статуса Relay: {request_id}")
        return False

    def bridge_to_recipient(
        self,
        amount: int,
        recipient: str,
        from_contract: str = ZERO_ADDRESS,
        to_contract: str = ZERO_ADDRESS
    ) -> int:
        """
        Отправляет ETH через Relay на указанный адрес
        
        Returns:
            1 если успешно, 0 если неудачно
        """
        amount_eth = decimalToInt(amount, 18)
        logger.info(
            f'{self.address}: Отправка {amount_eth:.6f} ETH '
            f'из {self._chain_from} в {self._chain_to} '
            f'на адрес {recipient[:10]}...{recipient[-8:]} через Relay'
        )

        quote = self._quote_tx_data(amount, recipient, from_contract, to_contract)
        if not quote or not quote.get('request_id'):
            logger.warning(f'{self.address}: Не удалось получить данные транзакции от API')
            return 0

        origin_tx_hash = self.send_tx(quote['tx'], return_hash=True)
        if not origin_tx_hash:
            return 0

        logger.info(f'{self.address}: Депозит подтверждён, ожидаем fill Relay')
        return 1 if self._wait_for_relay(quote['request_id']) else 0
