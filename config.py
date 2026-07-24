# =====================================================
# НАСТРОЙКИ СОФТА ДЛЯ РАСПРЕДЕЛЕНИЯ ЧЕРЕЗ RELAY
# =====================================================

# ==================== ОСНОВНЫЕ НАСТРОЙКИ ====================

# Сеть ИЗ которой отправлять
# Доступные: ETHEREUM, ARBITRUM, OPTIMISM, BASE, LINEA, BLAST, ZORA, MODE, TAIKO, INK, SONEIUM, UNICHAIN, BNB
CHAIN_FROM = 'ARBITRUM'

# Сеть В которую отправлять
CHAIN_TO = 'BNB'

# Как софт будет воспринимать значения суммы:
# Absolute - значение в ETH
# Percent - процент от баланса
AMOUNT_TYPE = 'Absolute'

# Диапазон сумм для отправки на КАЖДЫЙ адрес
# Если AMOUNT_TYPE = 'Absolute' — значения в ETH (например [0.001, 0.002])
# Если AMOUNT_TYPE = 'Percent' — значения в % от баланса (например [1, 5])
AMOUNT_RANGE = [0.00053023, 0.0006186]

# Оставьте закомиченным, если юзаете авто-слипаж
# SLIPPAGE_TOLERANCE_BPS = 600

# Relay fill status polling.
RELAY_STATUS_POLL_INTERVAL = 2
RELAY_STATUS_TIMEOUT = 300

# ==================== ЗАДЕРЖКИ ====================

# Рандомная задержка между транзакциями (в секундах)
TRANSACTIONS_DELAY = [30, 60]

# ==================== ПРОКСИ ====================

# Использовать ли прокси при обращении к блокчейну (RPC)
USE_PROXIES_IN_WEB3 = False

# ==================== RPC ====================

RPC = {
    'ETHEREUM': 'https://eth.llamarpc.com',
    'ARBITRUM': 'https://arb1.arbitrum.io/rpc',
    'OPTIMISM': 'https://mainnet.optimism.io',
    'BASE': 'https://mainnet.base.org',
    'LINEA': 'https://rpc.linea.build',
    'BLAST': 'https://rpc.blast.io',
    'ZORA': 'https://rpc.zora.energy',
    'MODE': 'https://mainnet.mode.network',
    'TAIKO': 'https://rpc.taiko.xyz',
    'INK': 'https://rpc-gel.inkonchain.com',
    'SONEIUM': 'https://rpc.soneium.org',
    'UNICHAIN': 'https://mainnet.unichain.org',
    'BNB': 'https://bsc-dataseed.binance.org',
}

# ==================== НАСТРОЙКИ ТРАНЗАКЦИЙ ====================

ERR_ATTEMPTS = 3          # Количество попыток при ошибке
TX_RETRIES = 3            # Количество попыток отправки транзакции
MAX_TX_WAIT = 500         # Максимальное время ожидания подтверждения (секунды)
GAS_MULT = 1.2            # Множитель газа
GAS_PRICE_MULT = 1.5      # Множитель цены газа
