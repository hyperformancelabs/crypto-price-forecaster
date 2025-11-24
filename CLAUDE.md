# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Crypto Price Forecaster is a cryptocurrency data collection and preprocessing system designed for machine learning and technical analysis. The project collects historical OHLCV (Open, High, Low, Close, Volume) data, market cap data, and news articles for major cryptocurrencies from multiple API sources.

**Primary focus**: Historical data collection for BTC/ETH with multiple timeframes (H4, Daily) + comprehensive news scraping
**Data sources**: Binance API (OHLCV), CoinMarketCap API (market cap), CoinMetrics API (network activity & profit metrics), Blockchain.info API (mining metrics), Bitcoin Magazine (news articles)
**Architecture**: Modular, config-driven design with organized data storage and robust web scraping capabilities

## Key Architecture

### Configuration System
All settings are centralized in `config.py`:
- API endpoints and rate limiting parameters
- Data directory structure management
- Coin configurations and mappings
- Utility functions for file path management
- Automatic directory creation via `ensure_directories()`

### Data Collection Pipeline
Eight main data collectors with no confirmation prompts (auto-start):

1. **OHLCV Collector** (`data-collection/1_ohlcv-h4.py`):
   - Fetches H4 OHLCV data from Binance for BTC/ETH
   - Collects raw price data only (no calculated indicators)
   - Saves to `data/raw/ohlcv/{coin}_h4_ohlcv.csv`

2. **Market Cap Collector** (`data-collection/2_marketcap-h4.py`):
   - Fetches H4 market cap data from CoinMarketCap for BTC, ETH, USDT, USDC
   - Collects individual coin market caps only (no calculated total)
   - Saves to `data/raw/marketcap/market_cap_h4.csv`

3. **Network Activity Collector** (`data-collection/3_networkactivity-d1.py`):
   - Fetches daily network activity metrics from CoinMetrics for BTC/ETH
   - Collects Active Addresses and Transaction Count
   - Saves to `data/raw/networkactivity/{coin}_networkactivity.csv`

4. **Security and Mining Collector** (`data-collection/4_secureandmining-d1.py`):
   - Fetches daily security and mining metrics from Blockchain.info for BTC
   - Collects Hash Rate, Mining Difficulty, and Miner Revenue
   - Saves to `data/raw/secureandmining/BTC_mining_d1.csv`

5. **Profit and Value Collector** (`data-collection/5_profitandvalue-d1.py`):
   - Fetches daily profit and value metrics from CoinMetrics for BTC/ETH
   - Collects MVRV Ratio, Exchange Inflows/Outflows, Exchange Supply (raw API data only)
   - Saves to `data/raw/profitandvalue/{coin}_profitandvalue.csv`

6. **Holder Behavior Collector** (`data-collection/6_holderbehavior-d1.py`):
   - Fetches daily holder behavior metrics from CoinMetrics for BTC (free tier limitations)
   - Collects Total Supply, MVRV Ratio, Exchange Flows, Exchange Supply (raw API data only)
   - Note: Advanced holder metrics (HODL Waves, Illiquid Supply, CDD, Whale Holdings) require paid APIs
   - Saves to `data/raw/holderbehavior/{coin}_holderbehavior.csv`

7. **Bitcoin Magazine News Scraper** (`data-collection/7_bitcoinmagazinenews-all.py`):
   - Scrapes all Bitcoin Magazine articles with comprehensive error handling and resume functionality
   - Features: Serial ID tracking, progress bars with tqdm, automatic HTML file naming with article timestamps
   - Robots.txt compliance with bingbot user agent and 3-second delays
   - Saves to `data/raw/news/bitcoinmagazinenews.csv` and `data/raw/news/html/{ID}_{timestamp}.html`
   - **COMPLETED**: 13,391 total articles, 13,391 crawled (100% success), 0 failed, 0 pending

8. **Sentiment Index Collector** (`data-collection/8_sentimentindex-d1.py`):
   - Fetches Fear & Greed Index data from Alternative.me free API
   - Collects daily sentiment values (0-100 scale) and classification labels
   - Coverage: 2018-present with complete historical data (2,841 daily records)
   - Saves to `data/raw/sentimentindex/fear_greed_index_d1.csv`
   - **COMPLETED**: 2,841 daily records from 2018-02-01 to 2025-11-15

### Data Structure

**OHLCV Data Format** (`data/raw/ohlcv/`):
- Columns: `timestamp, open, high, low, close, volume, quote_volume, trades`
- Timestamp format: pandas datetime
- Features: Raw price data only (no calculated indicators)

**Market Cap Data Format** (`data/raw/marketcap/`):
- Columns: `timestamp, BTC_market_cap, ETH_market_cap, USDT_market_cap, USDC_market_cap`
- Features: Individual coin market caps from CoinMarketCap API (no calculated total)

**Network Activity Data Format** (`data/raw/networkactivity/`):
- Columns: `timestamp, active_addresses, tx_count`
- Timestamp format: pandas datetime
- Features: Daily on-chain network metrics for blockchain analysis

**Mining Data Format** (`data/raw/secureandmining/`):
- Columns: `timestamp, hash_rate_ths, mining_difficulty, miner_revenue_usd`
- Timestamp format: pandas datetime
- Features: Daily mining security metrics for blockchain analysis

**Profit and Value Data Format** (`data/raw/profitandvalue/`):
- Columns: `timestamp, mvrv_ratio, exchange_inflow_native, exchange_inflow_usd, exchange_outflow_native, exchange_outflow_usd, exchange_supply_native, exchange_supply_usd`
- Timestamp format: pandas datetime
- Features: Raw on-chain metrics from CoinMetrics API (no calculated fields)

**Holder Behavior Data Format** (`data/raw/holderbehavior/`):
- Columns: `timestamp, total_supply, mvrv_ratio, exchange_inflow_native, exchange_inflow_usd, exchange_outflow_native, exchange_outflow_usd, exchange_supply_native, exchange_supply_usd`
- Timestamp format: pandas datetime
- Features: Raw BTC holder behavior metrics from CoinMetrics API (no calculated fields)

**Bitcoin Magazine News Data Format** (`data/raw/news/`):
- **CSV Format**: `id, datetime, url, status` (13,391 articles)
  - `id`: Serial number (1-13391)
  - `datetime`: Article publication time (ISO format)
  - `url`: Full article URL
  - `status`: All articles completed (status=1)
- **HTML Files**: `data/raw/news/html/{ID}_{YYYYMMDD_HHMMSS}.html`
  - Named by article ID and publication timestamp
  - Perfect synchronization between CSV and actual files
  - 13,391 HTML files (100% complete coverage)

**Sentiment Index Data Format** (`data/raw/sentimentindex/`):
- **Columns**: `timestamp, value, classification` (2,841 daily records)
  - `timestamp`: pandas datetime format
  - `value`: Fear & Greed Index score (0-100 scale)
  - `classification`: Sentiment label (Extreme Fear, Fear, Neutral, Greed, Extreme Greed)
- **Coverage**: 2018-02-01 to present (complete daily historical data)
- **Source**: Alternative.me Fear & Greed Index API
- **Distribution**: Fear (819 days), Greed (789 days), Extreme Fear (564 days), Neutral (388 days), Extreme Greed (281 days)

## Common Development Commands

### Running Data Collection
```bash
# Collect OHLCV data
python data-collection/1_ohlcv-h4.py

# Collect market cap data
python data-collection/2_marketcap-h4.py

# Collect network activity data
python data-collection/3_networkactivity-d1.py

# Collect security and mining data
python data-collection/4_secureandmining-d1.py

# Collect profit and value data
python data-collection/5_profitandvalue-d1.py

# Collect holder behavior data (BTC only - free tier)
python data-collection/6_holderbehavior-d1.py

# Scrape Bitcoin Magazine news (completed - 13,391 articles)
python data-collection/7_bitcoinmagazinenews-all.py

# Collect sentiment index data (Fear & Greed)
python data-collection/8_sentimentindex-d1.py
```

### Data Management
```bash
# Check data directory structure
ls -la data/raw/ohlcv/
ls -la data/raw/marketcap/
ls -la data/raw/networkactivity/
ls -la data/raw/secureandmining/
ls -la data/raw/profitandvalue/
ls -la data/raw/holderbehavior/
ls -la data/raw/news/
ls -la data/raw/sentimentindex/

# View data samples
head data/raw/ohlcv/BTC_h4_ohlcv.csv
head data/raw/marketcap/market_cap_h4.csv
head data/raw/networkactivity/BTC_networkactivity.csv
head data/raw/secureandmining/BTC_mining_d1.csv
head data/raw/profitandvalue/BTC_profitandvalue.csv
head data/raw/holderbehavior/BTC_holderbehavior.csv
head data/raw/news/bitcoinmagazinenews.csv
head data/raw/sentimentindex/fear_greed_index_d1.csv
```

## Important Configuration Details

### API Rate Limiting
- Binance: 0.1s delay between requests
- CoinMarketCap: 1s delay between requests, 2s between different coins
- CoinMetrics: 6s delay between requests (10 requests per 6 seconds)
- Blockchain.info: 1s delay between requests
- Automatic chunking: 365-day chunks for large historical requests

### Timeframe and Data Granularity
- Default timeframe: 4-hour (H4) intervals for OHLCV and market cap data
- Network activity: Daily (D1) intervals
- Mining metrics: Daily (D1) intervals
- Historical coverage: From earliest available timestamp to present
- Data processing: Automatic duplicate removal and forward-filling

### Coin Mappings
- **OHLCV**: BTC, ETH (Binance USDT pairs)
- **Market Cap**: BTC (ID: 1), ETH (ID: 1027), USDT (ID: 825), USDC (ID: 3408)
- **Network Activity**: BTC, ETH (CoinMetrics metrics: Active Addresses, Transaction Count)
- **Mining Metrics**: BTC (Blockchain.info metrics: Hash Rate, Difficulty, Miner Revenue)
- **Profit and Value**: BTC, ETH (CoinMetrics metrics: MVRV, Exchange Flows, Exchange Supply)
- **Holder Behavior**: BTC only (CoinMetrics metrics: Total Supply, MVRV, Exchange Flows, Exchange Supply)

## Data Collection Philosophy

### Low-Level Data Collection Only
This system follows a strict "collect-only" philosophy:
- **Raw API Data Only**: All collected features come directly from legitimate API responses or web scraping
- **No Calculations**: No arithmetic operations, derived metrics, or synthetic data during collection
- **No Estimations**: No fallback to fake/random data or artificial assumptions
- **Processing Stage Separation**: All calculations (net flows, percentages, log returns) are moved to data processing stage

### Data Source Authenticity
All 8 collectors use authoritative, legitimate sources:
- **Binance API**: Real exchange OHLCV data
- **CoinMarketCap API**: Real cryptocurrency market cap data
- **CoinMetrics API**: Real blockchain on-chain metrics
- **Blockchain.info API**: Real Bitcoin mining statistics
- **Alternative.me API**: Real market sentiment data
- **Bitcoin Magazine**: Direct web scraping of real news content

### Benefits of Low-Level Collection
- **Data Integrity**: 100% authentic data with no synthetic contamination
- **Flexibility**: Derived metrics can be recalculated with different parameters
- **Reliability**: Raw data sources are stable and verifiable
- **ML Ready**: Clean foundation for machine learning pipelines

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
- BTC Daily Mining Metrics: ~365 records (latest year)
- BTC Daily Profit and Value: ~6.2K records (1.1MB)
- ETH Daily Profit and Value: ~3.8K records (0.8MB)
- BTC Daily Holder Behavior: ~6.2K records (1.2MB)
- Bitcoin Magazine News: 13,391 complete articles (CSV + HTML files)
- Fear & Greed Daily Sentiment: 2,841 records (200KB)

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

## Mining Metrics

### Available Metrics
The security and mining collector provides the following blockchain security metrics:
- **Hash Rate**: Network computing power in tera hashes per second (TH/s)
- **Mining Difficulty**: Relative measure of how difficult it is to find a new block
- **Miner Revenue**: Total value of coinbase block rewards and transaction fees paid to miners (USD)

### Data Sources
- **Blockchain.info API**: Free public API with comprehensive mining statistics
- **No API key required**: Public access to historical blockchain data
- **Rate limited**: 1 request per second to ensure fair usage

### Historical Coverage
- **Bitcoin**: From 2009-01-03 to present (daily data)
- **Automatic updates**: Extends to most recent available data
- **Chunk-based collection**: 365-day chunks for efficient data retrieval

### Integration Benefits
Mining metrics data complements price and market data by:
- Providing blockchain security indicators
- Enabling correlation analysis between mining economics and price movements
- Supporting machine learning models with network security metrics
- Offering insights into mining network health and profitability trends

## Profit and Value Metrics

### Available Metrics
The profit and value collector provides the following valuation and flow metrics:
- **MVRV Ratio (CapMVRVCur)**: Market Value to Realized Value ratio
- **Exchange Inflows/Outflows**: Native units and USD value flowing to/from exchanges
- **Exchange Supply**: Total supply held on exchanges
- **Note**: Net flows and realized price are calculated during data processing, not collection

### Data Sources
- **CoinMetrics Community API**: Free tier with comprehensive on-chain valuation metrics
- **No API key required**: Public access to historical valuation data
- **Rate limited**: 10 requests per 6 seconds to ensure fair usage

### Historical Coverage
- **Bitcoin**: From 2009-01-03 to present (daily data)
- **Ethereum**: From 2015-07-30 to present (daily data)
- **Automatic updates**: Extends to most recent available data

### Integration Benefits
Profit and value data complements price and market data by:
- Providing valuation metrics (MVRV) for market cycle analysis
- Enabling analysis of exchange flow patterns and supply dynamics
- Supporting machine learning models with on-chain valuation indicators

## Holder Behavior Metrics

### Available Metrics
The holder behavior collector provides the following BTC holder metrics (free tier):
- **Total Supply (SplyCur)**: Complete circulating supply of Bitcoin
- **MVRV Ratio (CapMVRVCur)**: Market Value to Realized Value ratio
- **Exchange Inflows/Outflows**: Native units and USD value flowing to/from exchanges
- **Exchange Supply**: Total supply held on exchanges
- **Note**: Net flows and exchange supply percentage are calculated during data processing, not collection

### Data Sources
- **CoinMetrics Community API**: Free tier with limited holder behavior metrics
- **No API key required**: Public access to historical holder data
- **Rate limited**: 10 requests per 6 seconds to ensure fair usage

### Historical Coverage
- **Bitcoin**: From 2009-01-03 to present (daily data)
- **Automatic updates**: Extends to most recent available data
- **Chunk-based collection**: 365-day chunks for efficient data retrieval

### Limitations
- **Free tier only**: Advanced holder metrics require paid subscriptions
- **Missing metrics**: HODL Waves, Illiquid Supply, Coin Days Destroyed, Whale Holdings
- **Premium sources**: Glassnode, CryptoQuant, Kaiko offer comprehensive holder analytics

### Integration Benefits
Holder behavior data complements price and market data by:
- Providing exchange flow patterns for accumulation/distribution analysis
- Enabling MVRV-based market cycle identification
- Supporting machine learning models with holder positioning indicators
- Offering insights into long-term vs short-term holder behavior

## Sentiment Index Metrics

### Available Metrics
The sentiment index collector provides the following market sentiment metrics:
- **Fear & Greed Index**: Composite market sentiment score (0-100 scale)
- **Classification**: Sentiment category (Extreme Fear, Fear, Neutral, Greed, Extreme Greed)

### Data Sources
- **Alternative.me API**: Free public API with comprehensive Fear & Greed Index data
- **No API key required**: Public access to historical sentiment data
- **Rate limited**: 1 request per hour (respectful limit for API stability)

### Historical Coverage
- **Fear & Greed Index**: From 2018-02-01 to present (daily data)
- **Complete coverage**: 2,841 daily records with no gaps
- **Automatic updates**: Extends to most recent available data

### Integration Benefits
Sentiment index data complements price and market data by:
- Providing market sentiment indicators for trading psychology analysis
- Enabling correlation analysis between sentiment and price movements
- Supporting machine learning models with market sentiment features
- Offering insights into market cycle identification and reversal signals

### Sentiment Classification Scale
- **0-24**: Extreme Fear (historical buying opportunities)
- **25-44**: Fear (accumulation phase)
- **45-55**: Neutral (balanced market conditions)
- **56-75**: Greed (distribution phase)
- **76-100**: Extreme Greed (historical selling opportunities)

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