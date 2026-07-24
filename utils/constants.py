from dataclasses import dataclass

BASE_PATH = 'user_data/'

DEFAULT_PRIVATE_KEY = BASE_PATH + 'private_key.txt'
DEFAULT_RECIPIENTS = BASE_PATH + 'recipients.txt'
DEFAULT_PROXIES = BASE_PATH + 'proxies.txt'
FAILED_RECIPIENTS = BASE_PATH + 'failed.txt'

# Телеграм канал
TG_CHANNEL = 'https://t.me/goathamdao'


@dataclass
class ChainMap:
    idToName: dict
    nameToId: dict
    eip1559_chains: dict


# Поддерживаемые сети
CHAIN_MAP = ChainMap(
    idToName={
        1: 'ETHEREUM',
        42161: 'ARBITRUM',
        10: 'OPTIMISM',
        8453: 'BASE',
        59144: 'LINEA',
        81457: 'BLAST',
        7777777: 'ZORA',
        34443: 'MODE',
        167000: 'TAIKO',
        57073: 'INK',
        1868: 'SONEIUM',
        130: 'UNICHAIN',
        56: 'BNB',
    },
    nameToId={
        'ETHEREUM': 1,
        'ARBITRUM': 42161,
        'OPTIMISM': 10,
        'BASE': 8453,
        'LINEA': 59144,
        'BLAST': 81457,
        'ZORA': 7777777,
        'MODE': 34443,
        'TAIKO': 167000,
        'INK': 57073,
        'SONEIUM': 1868,
        'UNICHAIN': 130,
        'BNB': 56,
    },
    eip1559_chains={
        'ETHEREUM': True,
        'ARBITRUM': True,
        'OPTIMISM': True,
        'BASE': True,
        'LINEA': True,
        'BLAST': True,
        'ZORA': True,
        'MODE': True,
        'TAIKO': True,
        'INK': True,
        'SONEIUM': True,
        'UNICHAIN': True,
        'BNB': False,
    },
)

ZERO_ADDRESS = '0x0000000000000000000000000000000000000000'

logo = r"""
<cyan>
  ____  _            ____                   
 | __ )| |_   _  ___|  _ \  ___ _ __  _ __  
 |  _ \| | | | |/ _ \ | | |/ _ \ '_ \| '_ \ 
 | |_) | | |_| |  __/ |_| |  __/ |_) | |_) |
 |____/|_|\__,_|\___|____/ \___| .__/| .__/ 
                               |_|   |_|    
</cyan>
"""

PROJECT = """
<light-magenta>
 ╔═══════════════════════════════════════════════════════════════╗
 ║        RELAY РАЗДАЧА - Распределение ETH через Relay          ║
 ║               Выбор исходной и целевой сети                   ║
 ╠═══════════════════════════════════════════════════════════════╣
 ║                  Telegram: https://t.me/goathamdao            ║
 ╚═══════════════════════════════════════════════════════════════╝
</light-magenta>
"""

ERC20_ABI = '[{"constant":true,"inputs":[{"name":"_owner","type":"address"}],"name":"balanceOf","outputs":[{"name":"balance","type":"uint256"}],"type":"function"},{"constant":true,"inputs":[],"name":"decimals","outputs":[{"name":"","type":"uint8"}],"type":"function"}]'

