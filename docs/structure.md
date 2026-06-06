# Project Structure

## Directory Layout

```
crypto-price-forecaster-glm/
├── collectors/              # Data collection modules
├── processors/              # Data processing notebooks
├── infer/                  # Model training and inference
├── utils/                  # Shared utility functions
├── data/                   # Data storage (raw & processed)
├── docs/                   # Project documentation
├── config.py               # Centralized configuration
├── .env.example            # Environment variables template
├── .gitignore              # Git ignore patterns
├── CLAUDE.md              # AI assistant instructions
└── README.md               # Project overview
```

## Components

### Data Collection ([`collectors/`](collectors/))

Automated scripts for fetching data from various sources:

| Script | Purpose | Source | Output |
|--------|---------|--------|--------|
| [`1_ohlcv-h4.py`](collectors/1_ohlcv-h4.py:1) | OHLCV price data | Binance API | `data/raw/ohlcv/*.csv` |
| [`2_marketcap-h4.py`](collectors/2_marketcap-h4.py:1) | Market capitalization | CoinMarketCap API | `data/raw/marketcap/market_cap_h4.csv` |
| [`3_networkactivity-d1.py`](collectors/3_networkactivity-d1.py:1) | Network activity metrics | CoinMetrics API | `data/raw/networkactivity/*.csv` |
| [`4_secureandmining-d1.py`](collectors/4_secureandmining-d1.py:1) | Mining statistics | Blockchain.info API | `data/raw/secureandmining/BTC_mining_d1.csv` |
| [`5_onchainmetrics-d1.py`](collectors/5_onchainmetrics-d1.py:1) | On-chain metrics | CoinMetrics API | `data/raw/onchainmetrics/*.csv` |
| [`6_bitcoinmagazinenews-all.py`](collectors/6_bitcoinmagazinenews-all.py:1) | News articles | Bitcoin Magazine | `data/raw/news/*.csv` + HTML files |
| [`7_sentimentindex-d1.py`](collectors/7_sentimentindex-d1.py:1) | Fear & Greed Index | Alternative.me API | `data/raw/sentimentindex/fear_greed_index_d1.csv` |

### Data Processing ([`processors/`](processors/))

Jupyter notebooks for data transformation:

| Notebook | Purpose | Input | Output |
|-----------|---------|--------|--------|
| [`build_master.ipynb`](processors/build_master.ipynb:1) | Merge all data sources | Raw data files | `data/raw/master_dataset_h4_v1.csv` |
| [`cleaning.ipynb`](processors/cleaning.ipynb:1) | Clean and validate | Master dataset | `data/processed/master_dataset_h4_cleaned_v1.pkl` |
| [`feature_engineering.ipynb`](processors/feature_engineering.ipynb:1) | Create features | Cleaned dataset | `data/processed/final.pkl` |

### Model Training ([`infer/`](infer/))

| Notebook | Purpose | Input | Output |
|-----------|---------|--------|--------|
| [`train.ipynb`](infer/train.ipynb:1) | Train and evaluate models | Feature dataset | `artifacts/model_*.joblib` |

### Utilities ([`utils/`](utils/))

Shared functions used across the project:

| File | Purpose |
|------|---------|
| [`time_utils.py`](utils/time_utils.py:1) | Time parsing, range calculation, data merging |

### Configuration ([`config.py`](config.py:1))

Centralized configuration including:
- API endpoints and rate limits
- Data source mappings
- Directory paths
- Time range settings
- Default start dates per source

## Data Flow

```
Raw Data Sources
       ↓
   Collectors (7 scripts)
       ↓
   Raw CSV Files (data/raw/)
       ↓
   build_master.ipynb
       ↓
   Master Dataset (data/raw/master_dataset_h4_v1.csv)
       ↓
   cleaning.ipynb
       ↓
   Cleaned Dataset (data/processed/master_dataset_h4_cleaned_v1.pkl)
       ↓
   feature_engineering.ipynb
       ↓
   Feature Dataset (data/processed/final.pkl)
       ↓
   train.ipynb
       ↓
   Trained Models (artifacts/)
```

## Key Design Patterns

### Modular Architecture
- Each collector is independent and self-contained
- Shared utilities in [`utils/`](utils/) avoid code duplication
- Configuration centralized in [`config.py`](config.py:1)

### Incremental Collection
- Collectors check for existing data
- Only fetch new data beyond last timestamp
- Support resume after interruption

### Time-Based Alignment
- All data aligned to 4-hour timestamps
- Daily data forward-filled to H4 frequency
- Actionable time mapping prevents lookahead bias

### State Persistence
- Progress saved during collection
- Intermediate datasets persisted
- Models and scalers saved as artifacts
