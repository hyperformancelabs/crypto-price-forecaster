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
NETWORKACTIVITY_DIR = f"{RAW_DIR}/networkactivity"
SECUREANDMINING_DIR = f"{RAW_DIR}/secureandmining"
PROFITANDVALUE_DIR = f"{RAW_DIR}/profitandvalue"
HOLDERBEHAVIOR_DIR = f"{RAW_DIR}/holderbehavior"
SENTIMENTINDEX_DIR = f"{RAW_DIR}/sentimentindex"

# API endpoints
BINANCE_BASE_URL = "https://api.binance.com/api/v3"
CMC_API_BASE = "https://api.coinmarketcap.com/data-api/v3"
NETWORK_API_BASE = "https://community-api.coinmetrics.io/v4"
BLOCKCHAIN_API_BASE = "https://api.blockchain.info/charts"
SENTIMENTINDEX_API_BASE = "https://api.alternative.me/fng"

# Coin configurations
COINS = ['BTC', 'ETH']
CMC_IDS = {
    'BTC': 1,
    'ETH': 1027,
    'USDT': 825,
    'USDC': 3408
}

# Network activity metrics configuration (only available free tier metrics)
NETWORK_ACTIVITY_METRICS = {
    'BTC': ['AdrActCnt', 'TxCnt'],
    'ETH': ['AdrActCnt', 'TxCnt']
}

# Mining metrics configuration
MINING_METRICS = {
    'hash-rate': {'name': 'Hash Rate', 'unit': 'TH/s', 'description': 'Network hash rate in tera hashes per second'},
    'difficulty': {'name': 'Difficulty', 'unit': 'Difficulty', 'description': 'Mining difficulty level'},
    'miners-revenue': {'name': 'Miners Revenue', 'unit': 'USD', 'description': 'Total mining revenue in USD'}
}

# Profit and value metrics configuration (available on CoinMetrics free tier)
PROFITANDVALUE_METRICS = {
    'BTC': ['CapMVRVCur', 'FlowInExNtv', 'FlowInExUSD', 'FlowOutExNtv', 'FlowOutExUSD', 'SplyExNtv', 'SplyExUSD'],
    'ETH': ['CapMVRVCur', 'FlowInExNtv', 'FlowInExUSD', 'FlowOutExNtv', 'FlowOutExUSD', 'SplyExNtv', 'SplyExUSD']
}

# Holder behavior metrics configuration (BTC only - free tier limitations)
HOLDERBEHAVIOR_METRICS = {
    'BTC': ['SplyCur', 'CapMVRVCur', 'FlowInExNtv', 'FlowInExUSD', 'FlowOutExNtv', 'FlowOutExUSD', 'SplyExNtv', 'SplyExUSD']
}

# API parameters
DEFAULT_TIMEFRAME = '4h'
CHUNK_DAYS = 365
RATE_LIMIT_DELAY = 1
REQUEST_DELAY = 2

# Network activity API parameters
NETWORK_RATE_LIMIT = 6  # CoinMetrics: 10 requests per 6 seconds
NETWORK_CHUNK_DAYS = 365

# Mining API parameters
MINING_RATE_LIMIT = 1  # Blockchain.info: 1 request per second
MINING_CHUNK_DAYS = 365

# Secure and mining API parameters
SECUREANDMINING_RATE_LIMIT = 1  # Blockchain.info: 1 request per second
SECUREANDMINING_CHUNK_DAYS = 365

# Profit and value API parameters
PROFITANDVALUE_RATE_LIMIT = 6  # CoinMetrics: 10 requests per 6 seconds
PROFITANDVALUE_CHUNK_DAYS = 365

# Holder behavior API parameters
HOLDERBEHAVIOR_RATE_LIMIT = 6  # CoinMetrics: 10 requests per 6 seconds
HOLDERBEHAVIOR_CHUNK_DAYS = 365

# Sentiment Index API parameters
SENTIMENTINDEX_RATE_LIMIT = 3600  # Alternative.me: 1 request per hour (respectful limit)

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
        DATA_DIR, RAW_DIR, OHLCV_DIR, MARKETCAP_DIR, NETWORKACTIVITY_DIR, SECUREANDMINING_DIR, PROFITANDVALUE_DIR, HOLDERBEHAVIOR_DIR, SENTIMENTINDEX_DIR
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

def get_networkactivity_file(coin: str) -> str:
    """Get network activity file path for a coin (raw data)"""
    return f"{NETWORKACTIVITY_DIR}/{coin}_networkactivity.csv"

def get_mining_file() -> str:
    """Get mining metrics file path (raw data)"""
    return f"{SECUREANDMINING_DIR}/BTC_mining_d1.csv"

def get_profitandvalue_file(coin: str) -> str:
    """Get profit and value file path for a coin (raw data)"""
    return f"{PROFITANDVALUE_DIR}/{coin}_profitandvalue.csv"

def get_holderbehavior_file(coin: str) -> str:
    """Get holder behavior file path for a coin (raw data)"""
    return f"{HOLDERBEHAVIOR_DIR}/{coin}_holderbehavior.csv"

def get_sentimentindex_file() -> str:
    """Get sentiment index file path (raw data)"""
    return f"{SENTIMENTINDEX_DIR}/fear_greed_index_d1.csv"