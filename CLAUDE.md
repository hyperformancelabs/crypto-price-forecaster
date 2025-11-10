# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Crypto Price Forecaster is a cryptocurrency data collection and preprocessing system designed for machine learning and technical analysis. The project collects historical OHLCV (Open, High, Low, Close, Volume) data and market cap data for major cryptocurrencies from multiple API sources.

**Primary focus**: Historical data collection for BTC/ETH with multiple timeframes (H4, Daily)
**Data sources**: Binance API (OHLCV), CoinMarketCap API (market cap), CoinMetrics API (network activity)
**Architecture**: Modular, config-driven design with organized data storage

## Key Architecture

### Configuration System
All settings are centralized in `config.py`:
- API endpoints and rate limiting parameters
- Data directory structure management
- Coin configurations and mappings
- Utility functions for file path management
- Automatic directory creation via `ensure_directories()`

### Data Collection Pipeline
Three main data collectors with no confirmation prompts (auto-start):

1. **OHLCV Collector** (`data-collection/1_ohlcv-h4.py`):
   - Fetches H4 OHLCV data from Binance for BTC/ETH
   - Calculates log returns and technical indicators
   - Saves to `data/raw/ohlcv/{coin}_h4_ohlcv.csv`

2. **Market Cap Collector** (`data-collection/2_marketcap-h4.py`):
   - Fetches H4 market cap data from CoinMarketCap for BTC, ETH, USDT, USDC
   - Merges multi-coin data and calculates total market cap
   - Saves to `data/raw/marketcap/market_cap_h4.csv`

3. **Network Activity Collector** (`data-collection/3_networkactivity-d1.py`):
   - Fetches daily network activity metrics from CoinMetrics for BTC/ETH
   - Collects Active Addresses and Transaction Count
   - Saves to `data/raw/networkactivity/{coin}_networkactivity.csv`

### Data Structure

**OHLCV Data Format** (`data/raw/ohlcv/`):
- Columns: `timestamp, open, high, low, close, volume, quote_volume, log_returns, trades`
- Timestamp format: pandas datetime
- Features: Includes calculated log returns for ML analysis

**Market Cap Data Format** (`data/raw/marketcap/`):
- Columns: `timestamp, total_market_cap, BTC_market_cap, ETH_market_cap, USDT_market_cap, USDC_market_cap`
- Features: Individual and total market cap calculations

**Network Activity Data Format** (`data/raw/networkactivity/`):
- Columns: `timestamp, active_addresses, tx_count`
- Timestamp format: pandas datetime
- Features: Daily on-chain network metrics for blockchain analysis

## Common Development Commands

### Running Data Collection
```bash
# Collect OHLCV data
python data-collection/1_ohlcv-h4.py

# Collect market cap data
python data-collection/2_marketcap-h4.py

# Collect network activity data
python data-collection/3_networkactivity-d1.py
```

### Data Management
```bash
# Check data directory structure
ls -la data/raw/ohlcv/
ls -la data/raw/marketcap/
ls -la data/raw/networkactivity/

# View data samples
head data/raw/ohlcv/BTC_h4_ohlcv.csv
head data/raw/marketcap/market_cap_h4.csv
head data/raw/networkactivity/BTC_networkactivity.csv
```

## Important Configuration Details

### API Rate Limiting
- Binance: 0.1s delay between requests
- CoinMarketCap: 1s delay between requests, 2s between different coins
- CoinMetrics: 6s delay between requests (10 requests per 6 seconds)
- Automatic chunking: 365-day chunks for large historical requests

### Timeframe and Data Granularity
- Default timeframe: 4-hour (H4) intervals for OHLCV and market cap data
- Network activity: Daily (D1) intervals
- Historical coverage: From earliest available timestamp to present
- Data processing: Automatic duplicate removal and forward-filling

### Coin Mappings
- **OHLCV**: BTC, ETH (Binance USDT pairs)
- **Market Cap**: BTC (ID: 1), ETH (ID: 1027), USDT (ID: 825), USDC (ID: 3408)
- **Network Activity**: BTC, ETH (CoinMetrics metrics: Active Addresses, Transaction Count)

## Development Notes

### Code Architecture Patterns
- **No confirmation prompts**: All collectors start automatically
- **Production-ready data structure**: Clean separation of raw data by type
- **Modular design**: Each collector is self-contained with clear responsibilities
- **Error handling**: Graceful error handling with retry logic

### Data Quality
- Automatic data validation during collection
- Forward-fill missing values in time series
- Duplicate timestamp removal
- Consistent column naming across datasets

### Current Data Assets
- BTC H4 OHLCV: ~18K records (1.9MB)
- ETH H4 OHLCV: ~18K records (1.8MB)
- Market Cap H4: ~11K records (1.1MB)
- BTC Daily Network Activity: ~6.2K records (256KB)
- ETH Daily Network Activity: ~3.8K records (162KB)

## Network Activity Metrics

### Available Metrics
The network activity collector provides the following on-chain metrics:
- **Active Addresses (AdrActCnt)**: Number of unique addresses participating in transactions
- **Transaction Count (TxCnt)**: Total number of transactions processed on the network

### Data Sources
- **CoinMetrics Community API**: Free tier with comprehensive on-chain metrics
- **No API key required**: Public access to historical blockchain data
- **Rate limited**: 10 requests per 6 seconds to ensure fair usage

### Historical Coverage
- **Bitcoin**: From 2009-01-03 to present (daily data)
- **Ethereum**: From 2015-07-30 to present (daily data)
- **Automatic updates**: Extends to most recent available data

### Integration Benefits
Network activity data complements price and market cap data by:
- Providing blockchain usage indicators
- Enabling correlation analysis between on-chain activity and price movements
- Supporting machine learning models with fundamental blockchain metrics
- Offering insights into network health and adoption trends

## Extension Points

### Adding New Coins
1. Update `COINS` list in `config.py`
2. Add coin IDs to `CMC_IDS` mapping if needed
3. Collectors will automatically handle new coins

### Adding New Timeframes
1. Modify `DEFAULT_TIMEFRAME` in `config.py`
2. Update collector API parameters as needed
3. File naming conventions will adapt automatically

### Adding New Data Sources
1. Add API configuration to `config.py`
2. Create new collector following existing patterns
3. Use `ensure_directories()` and path utility functions