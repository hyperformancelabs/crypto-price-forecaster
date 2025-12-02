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
- Master dataset file path management via `get_master_dataset_file()`

### Data Collection Pipeline
Eight main data collectors with no confirmation prompts (auto-start) plus unified dataset processing:

1. **OHLCV Collector** (`collectors/1_ohlcv-h4.py`):
   - Fetches H4 OHLCV data from Binance for BTC/ETH
   - Collects raw price data only (no calculated indicators)
   - Saves to `data/raw/ohlcv/{coin}_h4_ohlcv.csv`

2. **Market Cap Collector** (`collectors/2_marketcap-h4.py`):
   - Fetches H4 market cap data from CoinMarketCap for BTC, ETH, USDT, USDC
   - Collects individual coin market caps only (no calculated total)
   - Saves to `data/raw/marketcap/market_cap_h4.csv`

3. **Network Activity Collector** (`collectors/3_networkactivity-d1.py`):
   - Fetches daily network activity metrics from CoinMetrics for BTC/ETH
   - Collects Active Addresses and Transaction Count
   - Saves to `data/raw/networkactivity/{coin}_networkactivity.csv`

4. **Security and Mining Collector** (`collectors/4_secureandmining-d1.py`):
   - Fetches daily security and mining metrics from Blockchain.info for BTC
   - Collects Hash Rate, Mining Difficulty, and Miner Revenue
   - Saves to `data/raw/secureandmining/BTC_mining_d1.csv`

5. **Profit and Value Collector** (`collectors/5_profitandvalue-d1.py`):
   - Fetches daily profit and value metrics from CoinMetrics for BTC/ETH
   - Collects MVRV Ratio, Exchange Inflows/Outflows, Exchange Supply (raw API data only)
   - Saves to `data/raw/profitandvalue/{coin}_profitandvalue.csv`

6. **Holder Behavior Collector** (`collectors/6_holderbehavior-d1.py`):
   - Fetches daily holder behavior metrics from CoinMetrics for BTC (free tier limitations)
   - Collects Total Supply, MVRV Ratio, Exchange Flows, Exchange Supply (raw API data only)
   - Note: Advanced holder metrics (HODL Waves, Illiquid Supply, CDD, Whale Holdings) require paid APIs
   - Saves to `data/raw/holderbehavior/{coin}_holderbehavior.csv`

7. **Bitcoin Magazine News Scraper** (`collectors/7_bitcoinmagazinenews-all.py`):
   - Scrapes all Bitcoin Magazine articles with comprehensive error handling and resume functionality
   - Features: Serial ID tracking, progress bars with tqdm, automatic HTML file naming with article timestamps
   - Robots.txt compliance with bingbot user agent and 3-second delays
   - Saves to `data/raw/news/bitcoinmagazinenews.csv` and `data/raw/news/html/{ID}_{timestamp}.html`
   - **COMPLETED**: 13,391 total articles, 13,391 crawled (100% success), 0 failed, 0 pending

8. **Sentiment Index Collector** (`collectors/8_sentimentindex-d1.py`):
   - Fetches Fear & Greed Index data from Alternative.me free API
   - Collects daily sentiment values (0-100 scale) and classification labels
   - Coverage: 2018-present with complete historical data (2,841 daily records)
   - Saves to `data/raw/sentimentindex/fear_greed_index_d1.csv`
   - **COMPLETED**: 2,841 daily records from 2018-02-01 to 2025-11-15

9. **Master Dataset Processor** (`processors/cleaning.ipynb`):
   - Unified processing pipeline that combines all 8 data sources into single H4-aligned dataset
   - Advanced sentiment analysis using CryptoBERT model with 11 distinct sentiment metrics
   - Column prefixing strategy (BTC_, ETH_) for clear data source identification
   - H4 time grid alignment with comprehensive validation and forward-fill for missing values
   - News content extraction and AS-OF timeframe mapping without future leakage
   - Merges 333,571 rows across 62 columns into production-ready ML dataset
   - Saves to `data/raw/master_dataset_h4_v1.csv` (84MB unified dataset)
   - **COMPLETED**: Full H4 coverage from 2009-01-03 to 2025-11-25 with comprehensive sentiment analysis

### Data Structure

**OHLCV Data Format** (`data/raw/ohlcv/`):
- Columns: `timestamp, open, high, low, close, volume, quote_volume, trades`
- Master Dataset Format: `timestamp, BTC_open, BTC_high, BTC_low, BTC_close, BTC_volume, BTC_quote_volume, BTC_trades, ETH_*` equivalents
- Timestamp format: pandas datetime aligned to H4 grid (00:00, 04:00, 08:00, 12:00, 16:00, 20:00)
- Features: Raw price data only (no calculated indicators), with prefixed column names for source identification

**Market Cap Data Format** (`data/raw/marketcap/`):
- Columns: `timestamp, BTC_market_cap, ETH_market_cap, USDT_market_cap, USDC_market_cap`
- Master Dataset Format: Same column names with prefixed BTC_, ETH_ for consistency
- Timestamp format: pandas datetime aligned to H4 grid
- Features: Individual coin market caps from CoinMarketCap API (no calculated total)

**Network Activity Data Format** (`data/raw/networkactivity/`):
- Columns: `timestamp, active_addresses, tx_count`
- Master Dataset Format: `timestamp, BTC_active_addresses, BTC_tx_count, ETH_active_addresses, ETH_tx_count`
- Timestamp format: pandas datetime aligned to H4 grid (interpolated from daily data)
- Features: Daily on-chain network metrics for blockchain analysis with prefixed column names

**Mining Data Format** (`data/raw/secureandmining/`):
- Columns: `timestamp, hash_rate_ths, mining_difficulty, miner_revenue_usd`
- Master Dataset Format: Same column names without prefix (BTC-specific metrics only)
- Timestamp format: pandas datetime aligned to H4 grid (interpolated from daily data)
- Features: Daily mining security metrics for blockchain analysis

**Profit and Value Data Format** (`data/raw/profitandvalue/`):
- Columns: `timestamp, mvrv_ratio, exchange_inflow_native, exchange_inflow_usd, exchange_outflow_native, exchange_outflow_usd, exchange_supply_native, exchange_supply_usd`
- Master Dataset Format: `timestamp, BTC_mvrv_ratio, BTC_exchange_inflow_native, BTC_exchange_inflow_usd, BTC_exchange_outflow_native, BTC_exchange_outflow_usd, BTC_exchange_supply_native, BTC_exchange_supply_usd, ETH_*` equivalents
- Timestamp format: pandas datetime aligned to H4 grid (interpolated from daily data)
- Features: Raw on-chain metrics from CoinMetrics API with prefixed column names (no calculated fields)

**Holder Behavior Data Format** (`data/raw/holderbehavior/`):
- Columns: `timestamp, total_supply, mvrv_ratio, exchange_inflow_native, exchange_inflow_usd, exchange_outflow_native, exchange_outflow_usd, exchange_supply_native, exchange_supply_usd`
- Master Dataset Format: Same column names without prefix (BTC-specific metrics only, following legacy naming)
- Timestamp format: pandas datetime aligned to H4 grid (interpolated from daily data)
- Features: Raw BTC holder behavior metrics from CoinMetrics API (no calculated fields)

**Bitcoin Magazine News Data Format** (`data/raw/news/`):
- **Base CSV Format**: `bitcoinmagazinenews_crawl.csv` with `id, datetime, url, status` (13,391 articles)
  - `id`: Serial number (1-13391)
  - `datetime`: Article publication time (ISO format)
  - `url`: Full article URL
  - `status`: All articles completed (status=1)
- **Enhanced CSV Format**: `bitcoinmagazinenews_extract.csv` with comprehensive sentiment analysis (22 columns, 13,391 articles)
  - **Core Metadata**: `author, content, date, id, status, tags, timestamp, title, url`
  - **Head Sentiment**: `head_p_bull, head_p_neu, head_p_bear, head_sent_net` - First 1000 characters sentiment probabilities and net score
  - **Global Sentiment**: `mean_p_bull, mean_p_neu, mean_p_bear, global_sent_net` - Full article sentiment probabilities and net score
  - **Maximum Sentiment**: `max_p_bull, max_p_neu, max_p_bear` - Maximum sentiment probabilities across all chunks
  - **Top-K Sentiment**: `topk_mean_p_bull, topk_mean_p_bear` - Mean of top-3 most bullish/bearish chunks
- **HTML Files**: `data/raw/news/html/{ID}_{YYYYMMDD_HHMMSS}.html`
  - Named by article ID and publication timestamp
  - Perfect synchronization between CSV and actual files
  - 13,391 HTML files (100% complete coverage)
  - **Data Quality**: 85 articles removed during processing (0.63% cleanup rate)

**Sentiment Index Data Format** (`data/raw/sentimentindex/`):
- **Columns**: `timestamp, value, classification` (2,841 daily records)
  - `timestamp`: pandas datetime format
  - `value`: Fear & Greed Index score (0-100 scale)
  - `classification`: Sentiment label (Extreme Fear, Fear, Neutral, Greed, Extreme Greed)
- **Coverage**: 2018-02-01 to present (complete daily historical data)
- **Source**: Alternative.me Fear & Greed Index API
- **Distribution**: Fear (819 days), Greed (789 days), Extreme Fear (564 days), Neutral (388 days), Extreme Greed (281 days)

**Master Dataset Format** (`data/raw/master_dataset_h4_v1.csv`):
- **Size**: 84MB, 333,571 rows with complete H4 coverage from 2009-01-03 to 2025-11-25
- **Timestamp**: UTC datetime aligned to 4-hour grid (00:00, 04:00, 08:00, 12:00, 16:00, 20:00)
- **Structure**: 62 columns organized across 9 data categories with prefixed naming convention
- **Price Data (8 columns)**: `BTC_open`, `BTC_high`, `BTC_low`, `BTC_close`, `BTC_volume`, `BTC_quote_volume`, `BTC_trades`, `ETH_*` equivalents
- **Market Cap Data (4 columns)**: `BTC_market_cap`, `ETH_market_cap`, `USDT_market_cap`, `USDC_market_cap`
- **Network Activity Data (4 columns)**: `BTC_active_addresses`, `BTC_tx_count`, `ETH_active_addresses`, `ETH_tx_count`
- **Mining Metrics (3 columns)**: `mining_difficulty`, `hash_rate_ths`, `miner_revenue_usd`
- **Profit and Value Data (14 columns)**: `BTC_mvrv_ratio`, `BTC_exchange_inflow_native`, `BTC_exchange_inflow_usd`, `BTC_exchange_outflow_native`, `BTC_exchange_outflow_usd`, `BTC_exchange_supply_native`, `BTC_exchange_supply_usd`, `ETH_*` equivalents
- **Holder Behavior Data (8 columns)**: `total_supply`, `mvrv_ratio`, `exchange_inflow_native`, `exchange_inflow_usd`, `exchange_outflow_native`, `exchange_outflow_usd`, `exchange_supply_native`, `exchange_supply_usd`
- **Sentiment Index Data (2 columns)**: `value`, `classification` (Fear & Greed Index)
- **News Processing Data (12 columns)**: `merged_content`, `news_article_count`, `news_log_article_count`, `has_news`, `news_head_sent_net_mean`, `news_global_sent_net_mean`, `news_head_sent_net_max`, `news_head_sent_net_min`, `news_head_sent_net_std`, `news_max_bull_prob`, `news_max_bear_prob`, `original_ids`
- **Column Naming**: All data source columns use prefixes (BTC_, ETH_) to prevent conflicts and enable clear source identification
- **Data Quality**: Comprehensive H4 grid alignment with forward-fill for missing values, automatic duplicate removal, and cross-source validation

## Common Development Commands

### Running Data Collection
```bash
# Collect OHLCV data
python collectors/1_ohlcv-h4.py

# Collect market cap data
python collectors/2_marketcap-h4.py

# Collect network activity data
python collectors/3_networkactivity-d1.py

# Collect security and mining data
python collectors/4_secureandmining-d1.py

# Collect profit and value data
python collectors/5_profitandvalue-d1.py

# Collect holder behavior data (BTC only - free tier)
python collectors/6_holderbehavior-d1.py

# Scrape Bitcoin Magazine news (completed - 13,391 articles)
python collectors/7_bitcoinmagazinenews-all.py

# Collect sentiment index data (Fear & Greed)
python collectors/8_sentimentindex-d1.py

# Process master dataset (unified H4-aligned dataset with sentiment analysis)
jupyter lab processors/cleaning.ipynb
```

### Data Processing Commands
```bash
# Run the complete cleaning and processing pipeline
jupyter lab processors/cleaning.ipynb
# Follow the notebook cells sequentially for:
# - Data loading and validation
# - H4 grid alignment and interpolation
# - News content extraction and sentiment analysis
# - Column prefixing and data merging
# - Master dataset export and validation

# Validate the master dataset
python -c "
import pandas as pd
df = pd.read_csv('data/raw/master_dataset_h4_v1.csv')
print(f'Master Dataset Shape: {df.shape}')
print(f'Columns: {list(df.columns)}')
print(f'Time Range: {df.timestamp.min()} to {df.timestamp.max()}')
print(f'Missing Values: {df.isnull().sum().sum()}')
print(f'H4 Grid Coverage: {df.shape[0]} rows')
"
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

# View master dataset sample and statistics
head data/raw/master_dataset_h4_v1.csv
wc -l data/raw/master_dataset_h4_v1.csv
ls -lh data/raw/master_dataset_h4_v1.csv
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
- **Unified processing**: Master dataset processor integrates all sources into single H4-aligned dataset
- **Column prefixing**: Systematic BTC_/ETH_ naming for clear source identification
- **Error handling**: Graceful error handling with retry logic and comprehensive validation

### Data Quality
- Automatic data validation during collection
- Forward-fill missing values in time series
- Duplicate timestamp removal
- Consistent column naming across datasets with prefixed source identification
- H4 grid alignment with comprehensive interpolation and validation
- Cross-source data integrity verification and gap analysis

### ML Integration Architecture
- **Production-ready pipeline**: End-to-end processing from raw collection to ML-ready dataset
- **Advanced sentiment features**: 11 distinct CryptoBERT sentiment metrics for market psychology analysis
- **Time-aligned features**: All data sources synchronized to H4 grid for model training
- **Feature engineering**: Log transformations, binary indicators, and aggregated statistics
- **Sparse data handling**: Comprehensive missing value strategies and validation
- **Memory efficiency**: Optimized processing for large datasets (84MB, 333K+ rows)

### Data Processing Pipeline

The `processors/cleaning.ipynb` provides comprehensive data processing capabilities:

#### HTML Content Extraction
- **Article Parser**: Extracts structured content from Bitcoin Magazine HTML files
- **Content Cleaning**: Removes junk elements, promotional content, and formatting artifacts
- **Metadata Extraction**: Retrieves title, author, date, tags, and publication metadata
- **Error Handling**: Graceful handling of malformed HTML and missing files

#### Sentiment Analysis with CryptoBERT
- **Model**: Uses `ElKulako/cryptobert` for cryptocurrency-specific sentiment analysis
- **Chunking Strategy**: Divides long articles into 256-token chunks with 48-token overlap for comprehensive analysis
- **Multi-perspective Analysis**:
  - **Head Analysis**: First 1000 characters (title + introduction) for immediate sentiment signals
  - **Global Analysis**: Entire article content for comprehensive sentiment assessment
  - **Top-K Analysis**: Mean of top-3 most bullish/bearish chunks for sentiment intensity
- **Device Support**:
  - **GPU Inference**: Local processing with configurable batch sizes (default: 32)
  - **API Inference**: HuggingFace Inference Client for CPU processing (default: 8)
  - **Automatic Selection**: Falls back to API if GPU unavailable
- **Batch Processing**: Configurable GPU/CPU batch sizes with rate limiting and retry logic
- **Output Metrics**: 11 sentiment columns with probabilistic scores:
  - **Head Sentiment**: `head_p_bull, head_p_neu, head_p_bear, head_sent_net`
  - **Global Sentiment**: `mean_p_bull, mean_p_neu, mean_p_bear, global_sent_net`
  - **Maximum Sentiment**: `max_p_bull, max_p_neu, max_p_bear`
  - **Top-K Sentiment**: `topk_mean_p_bull, topk_mean_p_bear`
- **Configuration**: Chunk size, overlap, max chunks, and batch sizes are fully configurable
- **Performance**: Optimized for processing large article collections with memory-efficient chunking

#### Time Series Processing
- **Timestamp Normalization**: Converts various timestamp formats to UTC with configurable rounding
- **Actionable Time Mapping**: Maps news to next actionable candle times (supports m/h/d/w/M)
- **Content Merging**: Combines multiple articles into structured LLM-ready format
- **DataFrame Operations**: Group by timeframe, merge content, count articles

### ML Integration Features
- **CryptoBERT News Sentiment**: Cryptocurrency-specific sentiment analysis with 11 distinct metrics
- **Time Series Alignment**: News grouped by actionable timeframes for model training
- **Advanced Feature Engineering**: Multiple sentiment dimensions for comprehensive analysis:
  - **Head Sentiment**: Immediate market reaction signals from article introduction
  - **Global Sentiment**: Comprehensive article sentiment assessment
  - **Maximum Sentiment**: Peak sentiment intensity detection across all chunks
  - **Top-K Sentiment**: Most extreme bullish/bearish passage identification
  - **Net Sentiment Scores**: Bullish minus Bearish probability differences
- **Sentiment-Based Trading Signals**: Market psychology indicators for ML models:
  - **High Head Bullish**: Immediate positive market sentiment indicators
  - **High Global Bearish**: Extended negative sentiment warnings
  - **Top-K Imbalance**: Strong directional sentiment from key passages
- **Comprehensive Coverage**: Dataset spans 2012-2025 with 13,391 articles
- **ML-Ready Format**: TSV-separated cleaned data with proper type handling and sentiment probabilities
- **Multi-Resolution Analysis**: Sentiment features available at chunk-level, article-level, and aggregate timeframe levels

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
- Bitcoin Magazine News Base: 13,391 articles (4-column crawl format, CSV + HTML files)
- Bitcoin Magazine News Enhanced: 13,391 articles with comprehensive sentiment analysis (22 columns, 2.7MB)
  - **11 Sentiment Metrics**: Head, global, maximum, and top-K sentiment probabilities per article
  - **ML-Ready Format**: Structured sentiment scores for cryptocurrency market analysis
  - **Time Coverage**: 2012-2025 with complete chronological sentiment tracking
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

## Enhanced Sentiment Analysis

### CryptoBERT Integration
The master dataset processor includes advanced sentiment analysis using cryptocurrency-specific models:

#### **Model Specifications**
- **Primary Model**: `ElKulako/cryptobert` - Fine-tuned BERT model for cryptocurrency sentiment analysis
- **Training Domain**: Specialized on cryptocurrency news, social media, and market discussions
- **Output Classes**: Bullish, Neutral, Bearish sentiment probabilities
- **Device Support**: Automatic GPU/CPU detection with adaptive batch sizes (GPU: 32, CPU: 8)

#### **Multi-dimensional Analysis Strategy**
- **Head Analysis**: First 1000 characters (title + introduction) for immediate market reaction signals
- **Global Analysis**: Entire article content processed in 256-token chunks with 48-token overlap
- **Maximum Detection**: Peak sentiment intensity identification across all chunks
- **Top-K Analysis**: Mean of top-3 most bullish/bearish passages for sentiment extremes

#### **Sentiment Metrics Pipeline**
1. **Content Extraction**: Sophisticated HTML parsing with junk removal and metadata extraction
2. **Chunking Strategy**: Long articles divided into manageable 256-token chunks with overlap
3. **Batch Processing**: Configurable GPU/CPU batch sizes with rate limiting and retry logic
4. **Probabilistic Scoring**: 11 distinct sentiment metrics per article:
   - **Head Sentiment**: `head_p_bull, head_p_neu, head_p_bear, head_sent_net`
   - **Global Sentiment**: `mean_p_bull, mean_p_neu, mean_p_bear, global_sent_net`
   - **Maximum Sentiment**: `max_p_bull, max_p_neu, max_p_bear`
   - **Top-K Sentiment**: `topk_mean_p_bull, topk_mean_p_bear`

#### **Market Psychology Applications**
- **High Head Bullish**: Immediate positive market sentiment indicators for short-term signals
- **High Global Bearish**: Extended negative sentiment warnings for medium-term outlooks
- **Top-K Imbalance**: Strong directional sentiment from key passages for trading opportunities
- **Cross-timeframe Analysis**: Sentiment trends across different horizons for comprehensive market assessment

#### **Time Series Integration**
- **AS-OF H4 Mapping**: News mapped to actionable 4-hour candle times without future leakage
- **Aggregated Features**: Mean, max, min, std sentiment metrics per H4 timeframe
- **Log-transformed Counts**: News intensity features with `log(article_count + 1)`
- **Binary Indicators**: `has_news` flags for sparse news periods
- **Extreme Probability Tracking**: Maximum bullish/bearish probabilities per timeframe

### Data Processing Pipeline

#### **Unified Workflow Architecture**
The master dataset processor implements a comprehensive data unification pipeline:

#### **Phase 1: Data Ingestion and Validation**
1. **Multi-source Loading**: Concurrent loading of all 8 raw data sources
2. **Schema Validation**: Automatic column type checking and format standardization
3. **Timestamp Normalization**: ISO 8601 parsing with microsecond cleanup and UTC conversion
4. **Quality Checks**: Duplicate detection, missing value analysis, and data integrity validation

#### **Phase 2: H4 Grid Alignment**
1. **Time Grid Creation**: Complete 4-hour timestamp grid from 2009-01-03 to present
2. **Interpolation Strategy**: Daily data interpolated to H4 with appropriate methods
3. **Forward Fill Application**: Missing values filled using time-appropriate strategies
4. **Gap Analysis**: Identification and documentation of data coverage gaps
5. **Validation**: Complete H4 grid coverage with comprehensive alignment checks

#### **Phase 3: Column Prefixing and Organization**
1. **Source Identification**: Automatic detection of data source type and cryptocurrency
2. **Prefix Application**: Systematic BTC_/ETH_ prefixing for column name consistency
3. **Schema Consolidation**: 62-column unified structure with clear data source provenance
4. **Naming Convention**: Standardized column naming following master dataset specification
5. **Legacy Compatibility**: Maintained backward compatibility with original column names where needed

#### **Phase 4: Advanced News Processing**
1. **HTML Content Extraction**: Sophisticated parsing with multiple layout support
2. **Content Cleaning**: Junk removal, promotional content filtering, and text normalization
3. **Metadata Extraction**: Author, date, tags, title extraction with error handling
4. **Sentiment Analysis**: Multi-dimensional CryptoBERT processing with configurable parameters
5. **Time Mapping**: AS-OF H4 timeframe mapping preventing future data leakage

#### **Phase 5: Integration and Export**
1. **Data Merging**: Left join of all sources to H4 grid with comprehensive validation
2. **Feature Engineering**: Log transformations, binary indicators, and aggregated statistics
3. **Quality Assurance**: Final validation checks and data integrity verification
4. **Export Generation**: Production-ready CSV with complete metadata and documentation

#### **Error Handling and Recovery**
- **Resilient Processing**: Graceful handling of malformed data, missing files, and API failures
- **Retry Logic**: Configurable retry strategies with exponential backoff
- **Progress Tracking**: Comprehensive logging and progress reporting for long-running operations
- **Validation Checks**: Multi-level validation with detailed error reporting and recovery suggestions

#### **Performance Optimizations**
- **Memory Management**: Efficient chunked processing for large datasets
- **Parallel Processing**: Concurrent data loading and processing where appropriate
- **Batch Operations**: Optimized batch sizes for both GPU and CPU inference
- **Caching**: Intelligent caching of intermediate results to avoid redundant processing

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
4. Follow column naming conventions with cryptocurrency prefixes (BTC_, ETH_)

### Column Naming Conventions
When adding new data sources to the master dataset:
- **Use Prefixes**: Apply cryptocurrency prefixes (BTC_, ETH_) to all column names
- **Snake Case**: Use underscores for multi-word column names (e.g., `exchange_inflow_native`)
- **Source Identification**: Include data source in column names where appropriate
- **Consistency**: Follow existing patterns from similar data sources
- **Avoid Conflicts**: Ensure unique column names across all data sources
- **Master Dataset Integration**: Consider H4 grid alignment and interpolation requirements

### Master Dataset Integration
When extending the master dataset with new data sources:
1. **Raw Data Collection**: Add new collector following existing 8-collector pattern
2. **Column Prefixing**: Apply systematic naming with cryptocurrency prefixes
3. **H4 Alignment**: Implement time grid alignment and interpolation as needed
4. **Validation**: Add data quality checks and validation in processing pipeline
5. **Documentation**: Update Data Structure section with new format specifications
6. **Testing**: Validate integration with existing master dataset structure