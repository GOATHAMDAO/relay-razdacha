import requests
from eth_account import Account
from eth_utils import to_checksum_address
from config import MAX_TX_WAIT, GAS_MULT, TX_RETRIES, GAS_PRICE_MULT, RPC, USE_PROXIES_IN_WEB3
from .utils import decimalToInt, get_proxy
from .constants import CHAIN_MAP
from loguru import logger
import time


class AccountEVM:
    """Класс для работы с EVM аккаунтом через JSON-RPC"""

    def __init__(
        self,
        chain_name: str,
        private_key: str,
        proxy: bool = USE_PROXIES_IN_WEB3,
        tx_timeout: int = MAX_TX_WAIT
    ):
        self.rpc_url = RPC[chain_name]
        self.chain_name = chain_name
        self._private_key = private_key
        self._account = Account.from_key(private_key)
        self._tx_timeout = tx_timeout
        self._eip1559 = CHAIN_MAP.eip1559_chains.get(chain_name, True)
        self.address = self._account.address
        
        if proxy:
            self.proxy = get_proxy()
        else:
            self.proxy = None

    def _rpc_call(self, method: str, params: list = None) -> dict:
        """Выполняет JSON-RPC вызов"""
        payload = {
            "jsonrpc": "2.0",
            "method": method,
            "params": params or [],
            "id": 1
        }
        
        response = requests.post(
            self.rpc_url,
            json=payload,
            proxies=self.proxy,
            timeout=30
        )
        result = response.json()
        
        if "error" in result:
            raise Exception(f"RPC Error: {result['error']}")
        
        return result.get("result")

    def get_balance(self) -> int:
        """Получает баланс в wei"""
        result = self._rpc_call("eth_getBalance", [self.address, "latest"])
        return int(result, 16)

    def get_balance_human(self) -> float:
        """Получает баланс в ETH"""
        balance_wei = self.get_balance()
        return decimalToInt(balance_wei, 18)

    def get_chain_id(self) -> int:
        """Получает chain ID"""
        result = self._rpc_call("eth_chainId")
        return int(result, 16)

    def get_nonce(self) -> int:
        """Получает nonce аккаунта"""
        result = self._rpc_call("eth_getTransactionCount", [self.address, "latest"])
        return int(result, 16)

    def get_gas_price(self) -> int:
        """Получает текущую цену газа"""
        result = self._rpc_call("eth_gasPrice")
        return int(result, 16)

    def estimate_gas(self, tx_dict: dict) -> int:
        """Оценивает газ для транзакции"""
        params = {
            "from": self.address,
            "to": to_checksum_address(tx_dict.get("to")),
            "value": hex(int(tx_dict.get("value", 0))),
        }
        if "data" in tx_dict:
            params["data"] = tx_dict["data"]
            
        result = self._rpc_call("eth_estimateGas", [params])
        return int(result, 16)

    def get_fee_history(self):
        """Получает историю комиссий для EIP-1559"""
        result = self._rpc_call("eth_feeHistory", ["0x5", "latest", [10, 20, 30]])
        return result

    def _get_gas_prices(self) -> dict:
        """Получает цены на газ"""
        gas_params = {}
        
        if self._eip1559:
            try:
                fee_history = self.get_fee_history()
                
                # Средняя базовая комиссия
                base_fees = [int(x, 16) for x in fee_history['baseFeePerGas']]
                avg_base_fee = sum(base_fees) / len(base_fees)
                
                # Средняя приоритетная комиссия
                rewards = fee_history['reward']
                avg_priority_fee = sum([
                    sum([int(r, 16) for r in reward]) / len(reward) 
                    for reward in rewards
                ]) / len(rewards)
                
                max_fee_per_gas = int((avg_base_fee + avg_priority_fee) * GAS_MULT)
                max_priority_fee_per_gas = int(avg_priority_fee * GAS_PRICE_MULT)
                
                if max_priority_fee_per_gas > max_fee_per_gas:
                    max_priority_fee_per_gas = max_fee_per_gas
                
                gas_params['maxFeePerGas'] = max_fee_per_gas
                gas_params['maxPriorityFeePerGas'] = max_priority_fee_per_gas
            except:
                # Fallback к legacy gas price
                gas_price = self.get_gas_price()
                gas_params['gasPrice'] = int(gas_price * GAS_MULT)
        else:
            chain_id = self.get_chain_id()
            if chain_id == 56:  # BSC
                gas_params['gasPrice'] = 3000000000  # 3 gwei
            else:
                gas_price = self.get_gas_price()
                gas_params['gasPrice'] = int(gas_price * GAS_MULT)
        
        return gas_params

    def send_raw_transaction(self, signed_tx: str) -> str:
        """Отправляет подписанную транзакцию"""
        result = self._rpc_call("eth_sendRawTransaction", [signed_tx])
        return result

    def get_transaction_receipt(self, tx_hash: str) -> dict:
        """Получает квитанцию транзакции"""
        result = self._rpc_call("eth_getTransactionReceipt", [tx_hash])
        return result

    def wait_for_transaction(self, tx_hash: str) -> int:
        """Ждёт подтверждения транзакции"""
        start_time = time.time()
        
        while time.time() - start_time < self._tx_timeout:
            receipt = self.get_transaction_receipt(tx_hash)
            if receipt:
                status = int(receipt['status'], 16)
                if status == 1:
                    logger.success(f'Транзакция успешна: {tx_hash}')
                    return 1
                else:
                    logger.warning(f'Транзакция неудачна: {tx_hash}')
                    return 0
            time.sleep(2)
        
        logger.warning(f'Таймаут ожидания транзакции: {tx_hash}')
        return 0

    def send_tx(self, tx_dict: dict, return_hash: bool = False) -> int | str:
        """Отправляет транзакцию"""
        for attempt in range(TX_RETRIES):
            try:
                # Подготавливаем транзакцию
                tx_dict['to'] = to_checksum_address(tx_dict['to'])
                tx_dict['from'] = self.address
                tx_dict['chainId'] = self.get_chain_id()
                tx_dict['nonce'] = self.get_nonce()
                tx_dict['value'] = int(tx_dict.get('value', 0))
                
                # Газ
                if 'gas' not in tx_dict or not tx_dict['gas']:
                    tx_dict['gas'] = self.estimate_gas(tx_dict)
                else:
                    tx_dict['gas'] = int(tx_dict['gas'])
                
                # Цены на газ
                gas_prices = self._get_gas_prices()
                tx_dict.update(gas_prices)
                
                # Подписываем
                signed = self._account.sign_transaction(tx_dict)
                
                # Отправляем
                tx_hash = self.send_raw_transaction(signed.rawTransaction.hex())
                logger.info(f'{self.address}: Транзакция отправлена')
                
                # Ждём подтверждения
                result = self.wait_for_transaction(tx_hash)
                
                if result == 1:
                    return tx_hash if return_hash else 1
                else:
                    raise Exception('Транзакция неудачна')
                    
            except Exception as e:
                logger.error(f"Ошибка отправки: {str(e)[:100]}")
                if attempt < TX_RETRIES - 1:
                    logger.info(f"Повтор через 10 сек. Попыток осталось: {TX_RETRIES - attempt - 1}")
                    time.sleep(10)
                else:
                    return 0
        
        return 0
