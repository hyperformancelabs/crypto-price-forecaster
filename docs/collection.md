# Data Collection Guide

## Overview

Automated data collection from 7 sources using Python scripts in [`collectors/`](collectors/).

## Configuration

All collectors use centralized configuration from [`config.py`](config.py:1):

```python
# Set collection end time
END_TIME = 'now'  # or '2025-11-14 00:00'

# API rate limits (respected automatically)
RATE_LIMIT_DELAY = 1
REQUEST_DELAY = 2
```

## Running Collectors

Execute in order:

```bash
# 1. OHLCV data (BTC, ETH)
python collectors/1_ohlcv-h4.py

# 2. Market cap (BTC, ETH, USDT, USDC)
python collectors/2_marketcap-h4.py

# 3. Network activity (BTC, ETH)
python collectors/3_networkactivity-d1.py

# 4. Mining metrics (BTC)
python collectors/4_secureandmining-d1.py

# 5. On-chain metrics (BTC, ETH)
python collectors/5_onchainmetrics-d1.py

# 6. News (Bitcoin Magazine)
python collectors/6_bitcoinmagazinenews-all.py

# 7. Sentiment index (Fear & Greed)
python collectors/7_sentimentindex-d1.py
```

## Data Sources

### 1. OHLCV ([`1_ohlcv-h4.py`](collectors/1_ohlcv-h4.py:1))

**Source**: Binance API (free, no key)
**Data**: Open, High, Low, Close, Volume, Quote Volume, Trades
**Frequency**: 4-hour candles
**Coins**: BTC, ETH
**Output**: `data/raw/ohlcv/{COIN}_h4_ohlcv.csv`

**Features**:
- Fetches from earliest available timestamp
- Merges with existing data
- Respects END_TIME truncation

### 2. Market Cap ([`2_marketcap-h4.py`](collectors/2_marketcap-h4.py:1))

**Source**: CoinMarketCap internal API (free, no key)
**Data**: Market capitalization
**Frequency**: 4-hour
**Coins**: BTC, ETH, USDT, USDC
**Output**: `data/raw/marketcap/market_cap_h4.csv`

**Features**:
- Single merged file with all coins
- Forward-fills gaps (up to 6 hours)
- Filters zero market cap records

### 3. Network Activity ([`3_networkactivity-d1.py`](collectors/3_networkactivity-d1.py:1))

**Source**: CoinMetrics Community API (free tier)
**Data**: Active addresses, Transaction count
**Frequency**: Daily (forward-filled to H4)
**Coins**: BTC, ETH
**Output**: `data/raw/networkactivity/{COIN}_networkactivity.csv`

**Metrics**:
- `AdrActCnt`: Active addresses
- `TxCnt`: Transaction count

**Features**:
- Chunked requests (365 days per request)
- Rate limited (10 requests per 6 seconds)
- Forward-fills missing values

### 4. Mining Metrics ([`4_secureandmining-d1.py`](collectors/4_secureandmining-d1.py:1))

**Source**: Blockchain.info API (free, public)
**Data**: Hash rate, Difficulty, Miner revenue
**Frequency**: Daily
**Coin**: BTC only
**Output**: `data/raw/secureandmining/BTC_mining_d1.csv`

**Metrics**:
- Hash Rate (TH/s)
- Mining Difficulty
- Miner Revenue (USD)

**Features**:
- Fetches all historical data in one request
- Pivots metrics to columns
- Forward-fills missing values

### 5. On-chain Metrics ([`5_onchainmetrics-d1.py`](collectors/5_onchainmetrics-d1.py:1))

**Source**: CoinMetrics Community API (free tier)
**Data**: Supply, MVRV, Exchange flows, Exchange supply
**Frequency**: Daily
**Coins**: BTC, ETH
**Output**: `data/raw/onchainmetrics/{COIN}_onchainmetrics.csv`

**Metrics**:
- `SplyCur`: Total supply (BTC only)
- `CapMVRVCur`: MVRV ratio
- `FlowInExNtv/USD`: Exchange inflow
- `FlowOutExNtv/USD`: Exchange outflow
- `SplyExNtv/USD`: Exchange supply

**Note**: Advanced metrics (HODL waves, illiquid supply) require paid APIs.

### 6. News ([`6_bitcoinmagazinenews-all.py`](collectors/6_bitcoinmagazinenews-all.py:1))

**Source**: Bitcoin Magazine (web scraping)
**Data**: Article URLs, timestamps, HTML content
**Frequency**: As published
**Output**: 
- `data/raw/news/bitcoinmagazinenews.csv` (metadata)
- `data/raw/news/html/*.html` (article content)

**Features**:
- Sitemap-based discovery
- Serial ID tracking for resume
- Status tracking (0=pending, 1=crawled)
- HTML files named: `ID_YYYYMMDD_HHMMSS.html`

**Requirements**:
- None for collection
- HuggingFace API key for sentiment analysis (in build_master)

### 7. Sentiment Index ([`7_sentimentindex-d1.py`](collectors/7_sentimentindex-d1.py:1))

**Source**: Alternative.me API (free, public)
**Data**: Fear & Greed Index value and classification
**Frequency**: Daily
**Output**: `data/raw/sentimentindex/fear_greed_index_d1.csv`

**Metrics**:
- Value (0-100)
- Classification (Extreme Fear to Extreme Greed)

**Features**:
- Fetches all historical data
- Merges with existing data
- Respects END_TIME truncation

## Incremental Collection

All collectors support incremental updates:

1. Check for existing data file
2. Read last timestamp from file
3. Fetch new data from last timestamp
4. Merge with existing data
5. Apply END_TIME truncation
6. Save updated dataset

## Rate Limiting

Each collector respects API rate limits:

| API | Rate Limit | Implementation |
|------|-------------|----------------|
| Binance | 1200 requests/minute | 0.1s delay |
| CoinMarketCap | ~10 requests/second | 2s delay |
| CoinMetrics | 10 requests/6 seconds | 6s delay |
| Blockchain.info | 1 request/second | 1s delay |
| Alternative.me | 1 request/hour | N/A (all at once) |
| Bitcoin Magazine | Manual | 3s delay |

## Error Handling

Collectors include:
- Retry logic with exponential backoff
- Graceful handling of 403/429 errors
- Progress saving on interruption
- Detailed error logging

## Troubleshooting

### Collection Fails

**Check API status**: Verify source API is operational
**Check END_TIME**: Ensure not in future
**Check disk space**: Verify write permissions
**Check network**: Verify internet connectivity

### Missing Data

**Source availability**: Some metrics have limited historical data
**Rate limiting**: Increase delays if hitting limits
**Time range**: Adjust DEFAULT_START_DATES in config

### Resume Collection

Collectors automatically resume from last saved timestamp. Just re-run the script.
