# Crypto Price Forecaster

Machine learning pipeline for cryptocurrency price prediction using multi-source data.

## Overview

Production-ready data pipeline for BTC/ETH price forecasting with 7 data sources, 30+ engineered features, and multiple ML algorithms.

> 📄 **[Technical Report (PDF)](docs/technical_report.pdf)** — Full methodology, analysis, and results.

## Project Structure

```
crypto-price-forecaster-glm/
├── collectors/          # Data collection scripts (7 sources)
├── processors/          # Data processing notebooks
├── infer/              # Model training
├── utils/              # Utility functions
├── data/               # Raw & processed data
├── docs/               # Documentation
├── config.py           # Centralized configuration
└── .env.example        # Environment template
```

## Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env

# Collect data (run all collectors)
python collectors/1_ohlcv-h4.py
python collectors/2_marketcap-h4.py
python collectors/3_networkactivity-d1.py
python collectors/4_secureandmining-d1.py
python collectors/5_onchainmetrics-d1.py
python collectors/6_bitcoinmagazinenews-all.py
python collectors/7_sentimentindex-d1.py

# Process data (run notebooks in order)
jupyter notebook processors/build_master.ipynb
jupyter notebook processors/cleaning.ipynb
jupyter notebook processors/feature_engineering.ipynb

# Train models
jupyter notebook infer/train.ipynb
```

## Data Sources

| Source | Type | Frequency | API |
|---------|------|------------|------|
| Binance | OHLCV | 4H | Free |
| CoinMarketCap | Market Cap | 4H | Free |
| CoinMetrics | Network/On-chain | Daily | Free |
| Blockchain.info | Mining | Daily | Free |
| Bitcoin Magazine | News | As published | Scraping |
| Alternative.me | Fear & Greed | Daily | Free |

## Key Features

**Price & Returns**: Log returns, volatility
**Volume**: Relative volume, momentum
**Technical**: Bollinger Bands, CLV, wick imbalance
**Market Structure**: Correlations, market cap ratios
**Network**: Active addresses, transaction intensity
**Mining**: Hash ribbon, Puell multiple
**On-chain**: MVRV, exchange flows, reserves
**News Sentiment**: Article count, sentiment scores, decay
**Market Sentiment**: Fear & Greed Index changes

**Target**: BTC next-period log return (1-period horizon, 6-period window)

## Models

**Linear**: Ridge, Lasso, ElasticNet, Huber, SGD
**Non-linear**: LinearSVR, SVR-RBF, Decision Tree
**Ensemble**: Random Forest, Gradient Boosting

**Metrics**: RMSE, MAE, IC, Directional Accuracy, PnL, Win Rate, Max Drawdown

## Configuration

Edit [`config.py`](config.py:1) to set:
- `END_TIME`: Collection end point (default: `'2025-11-14 00:00'`)
- `DEFAULT_START_DATES`: Start dates per source
- API rate limits and chunk sizes

## Documentation

Detailed guides in [`docs/`](docs/):
- [`structure.md`](docs/structure.md) - Architecture
- [`collection.md`](docs/collection.md) - Data collection
- [`preprocessing.md`](docs/preprocessing.md) - Building master dataset
- [`cleaning.md`](docs/cleaning.md) - Data cleaning
- [`feature_engineering.md`](docs/feature_engineering.md) - Feature creation
- [`training.md`](docs/training.md) - Model training
- [`data-readme.md`](docs/data-readme.md) - Data dictionary

## Data Files

**Raw** (`data/raw/`): Per-source collected data
**Processed** (`data/processed/`): Merged, cleaned, feature-engineered
**Artifacts** (`artifacts/`): Trained models and scalers

## License

See [`LICENSE`](LICENSE).
