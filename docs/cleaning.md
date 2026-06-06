# Data Cleaning Guide

## Overview

The cleaning pipeline ([`cleaning.ipynb`](processors/cleaning.ipynb:1)) validates and fixes data quality issues in the master dataset.

## Process Flow

```
Master Dataset (raw)
       ↓
   Load & Initial Checks
       ↓
   Missing Data Analysis
       ↓
   Feature-Specific Cleaning
       ↓
   Data Quality Validation
       ↓
   Cleaned Dataset (PKL)
```

## Step 1: Load & Initial Checks

### Load Dataset

```python
master_df = pd.read_csv('data/raw/master_dataset_h4_v1.csv')
master_df['timestamp'] = pd.to_datetime(master_df['timestamp'], utc=True)
```

### Drop Unnecessary Columns

Remove metadata columns:
- `merged_content`: Large text field not needed for modeling
- `original_ids`: Article ID list not needed

### Basic Validation

**Duplicate timestamps**:
```python
if master_df['timestamp'].duplicated().any():
    print(f"WARNING: Found {count} duplicate timestamps!")
```

**Missing timestamps**:
```python
full_range = pd.date_range(start=min, end=max, freq='4h')
missing = full_range.difference(pd.DatetimeIndex(master_df['timestamp']))
print(f"Missing timestamps: {len(missing)}")
```

## Step 2: Missing Data Analysis

### Missingness Matrix

Visualize missing data patterns:
- Binary heatmap (black=missing, white=present)
- Grouped by feature source (BTC, ETH, news, etc.)
- Timeline view shows data availability

### Missing Rate by Column

Calculate and plot missing percentage:
```python
missing_pct = (master_df.isna().mean() * 100).sort_values(ascending=False)
```

## Step 3: Feature-Specific Cleaning

### H4 Features (High-Frequency)

**Features**: OHLCV, market cap
**Strategy**: Linear interpolation

```python
H4_features = [
    "BTC_open","BTC_high","BTC_low","BTC_close","BTC_volume",
    "BTC_quote_volume","BTC_trades",
    "ETH_open","ETH_high","ETH_low","ETH_close","ETH_volume",
    "ETH_quote_volume","ETH_trades",
    "BTC_market_cap","ETH_market_cap",
    "USDT_market_cap","USDC_market_cap"
]

# Interpolate non-market cap columns
interp_cols = [col for col in H4_features if "cap" not in col]
df_h4[interp_cols] = df_h4[interp_cols].interpolate(method='linear')

# Forward fill market cap, fill remaining with 0
locf_cols = [col for col in H4_features if "cap" in col]
df_h4[locf_cols] = df_h4[locf_cols].ffill().fillna(0)
```

**Rationale**:
- OHLCV: Small gaps, linear interpolation appropriate
- Market cap: Step function, forward-fill preserves structure

### News Features

**Features**: 22 sentiment-related columns
**Strategy**: Default values for missing

```python
news_features = [
    "news_article_count", "news_log_article_count", "has_news",
    "news_combined_sent_mean", "news_combined_sent_std", ...
]

# Find rows where ALL news features are null
rows_all_null = news_cols.isna().all(axis=1)

# Fill with defaults based on dtype
news_defaults = {}
for c in news_cols:
    if is_bool_dtype: news_defaults[c] = False
    elif is_integer_dtype: news_defaults[c] = 0
    elif is_float_dtype: news_defaults[c] = 0.0

news_cols.loc[rows_all_null, :] = news_defaults
```

**Rationale**: No news = neutral sentiment (0)

### D1 Features (Daily)

**Features**: Network activity, mining, on-chain, sentiment index
**Strategy**: Forward-fill

```python
D1_features = [
    "BTC_active_addresses","BTC_tx_count",
    "mining_difficulty","hash_rate_ths","miner_revenue_usd",
    "BTC_onchain_total_supply","BTC_onchain_mvrv_ratio",
    ...
]

df_d1 = df_d1.ffill()
```

**Rationale**: Daily values constant within H4 period

## Step 4: Data Quality Validation

### Negative Values

Check for invalid negative values:
```python
numeric_cols = master_df.select_dtypes(include="number").columns
neg_counts = (master_df[numeric_cols] < 0).sum()
```

**Expected negatives**: Log returns, sentiment scores
**Unexpected negatives**: Prices, volumes, counts

### Value Ranges

Validate min/max per column:
```python
range_summary = master_df[numeric_cols].agg(["min", "max"]).T
```

### Infinite Values

Check for +/- infinity:
```python
pos_inf_counts = pd.Series(np.isposinf(master_df[numeric_cols]).sum())
neg_inf_counts = pd.Series(np.isneginf(master_df[numeric_cols]).sum())
```

### OHLC Sanity

Validate candle structure:
```python
def ohlc_violations(df, prefix):
    cols = [f"{prefix}_open", f"{prefix}_high", 
             f"{prefix}_low", f"{prefix}_close"]
    highs = df[f"{prefix}_high"]
    lows = df[f"{prefix}_low"]
    other_cols = df[cols]
    
    bad = df[
        (highs < other_cols.max(axis=1)) |  # high should be >= others
        (lows > other_cols.min(axis=1))     # low should be <= others
    ]
    return bad
```

**Violations**: High < Open/Close/Low OR Low > Open/Close/High

### Outlier Detection

IQR method (1.5x, same as boxplot whiskers):
```python
for col in numeric_cols:
    q1, q3 = master_df[col].quantile([0.25, 0.75])
    iqr = q3 - q1
    lo, hi = q1 - 1.5 * iqr, q3 + 1.5 * iqr
    outlier_mask[col] = (master_df[col] < lo) | (master_df[col] > hi)
```

**Visualization**: Boxplots for all numeric columns
**Action**: Outliers identified but retained (model robustness)

## Step 5: Time Range Filtering

Filter to start from sentiment index availability:

```python
min_date = master_df.loc[
    master_df['sentiment_index_value'].notna(), 
    'timestamp'
].min()
master_df = master_df[master_df['timestamp'] >= min_date]
```

**Rationale**: Ensure all features available for modeling

## Step 6: Final Validation

### Missing Data Summary

After cleaning:
```python
missing_summary = pd.concat([
    master_df.isna().sum(),
    (master_df.isna().mean() * 100).round(2)
], axis=1, keys=["missing_rows", "missing_pct"])
```

**Goal**: Minimal missing data (< 5% per feature)

### Outlier Summary

```python
outlier_per = (outlier_mask.sum() / len(master_df) * 100).sort_values(ascending=False)
```

## Output

### Cleaned Dataset

**File**: `data/processed/master_dataset_h4_cleaned_v1.pkl`
**Format**: Pickle (preserves dtypes)
**Structure**: Same columns as master, cleaned values

**Also saved as**: `master_dataset_h4_cleaned_v1.csv`

## Cleaning Strategies Summary

| Feature Type | Strategy | Rationale |
|-------------|----------|-----------|
| OHLCV | Linear interpolation | Small gaps, continuous data |
| Market Cap | Forward-fill + 0 | Step function, preserves structure |
| News | Default values (0/False) | No news = neutral |
| Daily metrics | Forward-fill | Constant within H4 period |
| Outliers | Identify, retain | Model robustness testing |

## Next Steps

After cleaning, run:
1. [`feature_engineering.ipynb`](feature_engineering.md) - Create features
2. [`train.ipynb`](training.md) - Train models
