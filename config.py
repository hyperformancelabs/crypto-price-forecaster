"""
Configuration file for crypto price forecaster project
Shared variables used across all data collection scripts
"""

import os
from pathlib import Path

# Data directories - Production ready structure
DATA_DIR = "data"
RAW_DIR = f"{DATA_DIR}/raw"
OHLCV_DIR = f"{RAW_DIR}/ohlcv"
MARKETCAP_DIR = f"{RAW_DIR}/marketcap"

# API endpoints
BINANCE_BASE_URL = "https://api.binance.com/api/v3"
CMC_API_BASE = "https://api.coinmarketcap.com/data-api/v3"

# Coin configurations
COINS = ['BTC', 'ETH']
CMC_IDS = {
    'BTC': 1,
    'ETH': 1027,
    'USDT': 825,
    'USDC': 3408
}

# API parameters
DEFAULT_TIMEFRAME = '4h'
CHUNK_DAYS = 365
RATE_LIMIT_DELAY = 1
REQUEST_DELAY = 2

# Timeframes for aggregation
AGGREGATION_TIMEFRAMES = {
    'D': '1d',
    '4D': '4d',
    'W': '1w',
    'M': '1M'
}

# Initialize directories
def ensure_directories():
    """Create necessary directories if they don't exist"""
    directories = [
        DATA_DIR, RAW_DIR, OHLCV_DIR, MARKETCAP_DIR
    ]
    for directory in directories:
        if not os.path.exists(directory):
            os.makedirs(directory)

# File paths
def get_ohlcv_file(coin: str) -> str:
    """Get OHLCV file path for a coin (raw data)"""
    return f"{OHLCV_DIR}/{coin}_h4_ohlcv.csv"

def get_marketcap_file() -> str:
    """Get market cap file path (raw data)"""
    return f"{MARKETCAP_DIR}/market_cap_h4.csv"