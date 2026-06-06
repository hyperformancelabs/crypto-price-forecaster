# Preprocessing Guide

## Overview

The preprocessing pipeline ([`build_master.ipynb`](processors/build_master.ipynb:1)) merges all data sources into a unified master dataset with sentiment analysis.

## Process Flow

```
Raw Data Files (7 sources)
       ↓
   Load & Convert Timestamps
       ↓
   Extract & Analyze News
       ↓
   Sentiment Analysis (CryptoBERT)
       ↓
   Merge News by Actionable Time
       ↓
   Align All Data to H4 Grid
       ↓
   Master Dataset (CSV)
```

## Step 1: Data Loading

### Load All Sources

Each data source loaded into separate DataFrame:

```python
DATA_SOURCES = [
    ("OHLCV", COINS, get_ohlcv_file),
    ("Market Cap", None, get_marketcap_file),
    ("Network Activity", COINS, get_networkactivity_file),
    ("Mining", None, get_mining_file),
    ("Onchain Metrics", ["BTC"], get_onchainmetrics_file),
    ("News", None, get_news_file),
    ("Sentiment Index", None, get_sentimentindex_file),
]
```

### Timestamp Conversion

All timestamps converted to UTC datetime:

```python
def convert_timestamp(df, col, tz="UTC", round_to="s"):
    # Handles: datetime, numeric epoch, string formats
    # Removes microseconds for problematic ISO strings
    # Converts to target timezone
    # Rounds to specified precision
```

### Column Renaming

Prefix columns with source/coin for clarity:
- `BTC_open`, `BTC_close`, etc. (OHLCV)
- `BTC_market_cap`, `ETH_market_cap` (Market cap)
- `BTC_active_addresses`, `BTC_tx_count` (Network activity)
- `mining_difficulty`, `hash_rate_ths` (Mining)
- `BTC_onchain_mvrv_ratio`, `BTC_onchain_exchange_inflow_usd` (On-chain)
- `sentiment_index_value`, `sentiment_index_classification` (Sentiment index)

## Step 2: News Processing

### Article Extraction

Extract structured content from HTML files:

```python
def extract_article(source):
    # Extract metadata: title, author, date, tags
    # Locate main content container
    # Remove junk: scripts, ads, navigation
    # Extract paragraphs recursively
    # Clean whitespace and punctuation
    return {
        'title': str,
        'content': str,
        'author': str,
        'date': datetime,
        'tags': list
    }
```

**Selectors tried** (in priority order):
- `.tdb_single_content .tdb-block-inner`
- `.tdb_single_content`
- `.entry-content`
- `.post-content`
- `article`

### Resume Logic

Check for existing extractions:
- Load `bitcoinmagazinenews_crawl.csv` if exists
- Merge with master list
- Only fetch missing articles

### Safe Separator Detection

Find separator not present in data:
- Tests: `,`, `;`, `|`, `\t`, `~`, `^`
- Uses first safe separator for CSV

## Step 3: Sentiment Analysis

### CryptoBERT Model

Uses [`ElKulako/cryptobert`](https://huggingface.co/ElKulako/cryptobert) for sentiment classification.

**Classes**: Bullish, Neutral, Bearish
**Requirements**: HuggingFace API key (set as `hf_key` in `.env`)

### Initialization

```python
tokenizer, classify_batch = init_cryptobert_classifier(
    hf_key=hf_key,
    model_name="ElKulako/cryptobert",
    batch_size_gpu=256,
    batch_size_cpu=8
)
```

### Text Chunking

Long articles split into chunks:

```python
def chunk_by_tokens(text, tokenizer, chunk_size=256, overlap=48):
    # Split by tokens
    # Overlap chunks for context
    # Max 10 chunks per article
```

### Sentiment Scoring

**Head-focused** (title + first 1000 chars):
- Captures immediate market impact
- Higher weight in combined score

**Global** (entire article):
- Captures full context
- Used for divergence analysis

**Metrics computed**:
- `head_p_bull/neu/bear`: Head sentiment probabilities
- `mean_p_bull/neu/bear`: Global mean probabilities
- `max_p_bull/neu/bear`: Global max probabilities
- `topk_mean_p_bull/bear`: Top-K mean
- `head_sent_net`: Head bullish - bearish
- `global_sent_net`: Global bullish - bearish

### Resume Logic

Check for existing scores:
- Load `bitcoinmagazinenews_extract.csv` if exists
- Only score missing articles
- Merge with existing scores

## Step 4: News Aggregation

### Actionable Time Mapping

Map news to H4 candles without lookahead:

```python
def map_to_actionable_time(timestamp, timeframe="4h"):
    # News in (T-Δ, T] → candle T
    # News at exact open → belongs to this candle
    # Otherwise → belongs to NEXT candle
```

### Per-Bucket Aggregation

Aggregate all news in each H4 bucket:

**Volume metrics**:
- `news_article_count`: Number of articles
- `news_log_article_count`: Log(1 + count)
- `has_news`: Binary flag

**Sentiment metrics**:
- `news_combined_sent_mean/std/max/min`: Combined sentiment stats
- `news_combined_sent_max_abs`: Maximum absolute sentiment
- `news_combined_sent_sum_abs`: Sum of absolute sentiment

**Bull/Bear structure**:
- `news_bull_ratio`: Fraction bullish
- `news_bear_ratio`: Fraction bearish

**CryptoBERT probabilities**:
- `news_p_bull/bear/neu_mean`: Mean probabilities
- `news_max_p_bull/bear_bucket`: Max probabilities

**Conflict detection**:
- `news_is_conflict`: Strong bull AND strong bear present

**Head vs Global**:
- `news_head_sent_mean/std/max/min`: Head sentiment stats
- `news_head_global_diff_mean`: Head - global difference
- `news_head_global_abs_diff_mean`: Absolute difference
- `news_head_exag_ratio`: Head exaggeration ratio

**Combined sentiment** (alpha-weighted):
```python
alpha = 1 / (1 + K_ALPHA * |head - global|)
combined = alpha * global + (1 - alpha) * head
```

## Step 5: Data Alignment

### H4 Grid Creation

Create complete 4-hour timestamp grid:

```python
full_idx = pd.date_range(
    start=master_df['timestamp'].min(),
    end=master_df['timestamp'].max(),
    freq="4h"
)
```

### Reindex

Fill missing timestamps:

```python
final_df = (
    master_df
    .set_index("timestamp")
    .reindex(full_idx)
    .rename_axis("timestamp")
    .reset_index()
)
```

**Result**: Every H4 timestamp present, even if no data exists.

### Merge Strategy

Outer join all dataframes on timestamp:
- Preserves all timestamps
- Creates NaN where data missing
- Maintains chronological order

## Step 6: Quality Checks

### H4 Validation

Verify timestamps align to 4-hour grid:

```python
VALID_HOURS = {0, 4, 8, 12, 16, 20}
bad_hour = (~ts.dt.hour.isin(VALID_HOURS)).sum()
```

### Duplicate Detection

Check for duplicate timestamps:
```python
if master_df['timestamp'].duplicated().any():
    print(f"WARNING: Found {count} duplicate timestamps!")
```

## Output

### Master Dataset

**File**: `data/raw/master_dataset_h4_v1.csv`
**Format**: CSV
**Structure**: 
- Column: `timestamp`
- Columns: All data sources merged
- Rows: All H4 timestamps in range

### Columns Count

~75+ columns from all sources:
- 14 OHLCV columns (BTC + ETH)
- 4 Market cap columns
- 4 Network activity columns
- 3 Mining columns
- 8 On-chain columns (BTC only)
- 22 News sentiment columns
- 2 Sentiment index columns

## Next Steps

After preprocessing, run:
1. [`cleaning.ipynb`](cleaning.md) - Clean and validate data
2. [`feature_engineering.ipynb`](feature_engineering.md) - Create features
3. [`train.ipynb`](training.md) - Train models
