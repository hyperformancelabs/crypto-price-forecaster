# Feature Engineering Guide

## Overview

Feature engineering pipeline ([`feature_engineering.ipynb`](processors/feature_engineering.ipynb:1)) creates 30+ predictive features from cleaned data.

## Process Flow

```
Cleaned Dataset
       ↓
   OHLCV Features (Returns, Volume, Volatility)
       ↓
   Microstructure Features (CLV, Wicks)
       ↓
   Technical Indicators (Bollinger Bands)
       ↓
   Market Structure Features (Correlation, Market Cap)
       ↓
   Network Activity Features (Addresses, Transactions)
       ↓
   Mining Features (Hash Ribbon, Puell)
       ↓
   On-chain Features (MVRV, Flows, Reserves)
       ↓
   News Features (Sentiment, Decay, Shock)
       ↓
   Sentiment Index Features (F&G Change, Divergence)
       ↓
   Final Feature Set (30+ features)
```

## Feature Categories

### 1. Price & Returns

**BTC_log_return**: `ln(close_t / close_{t-1})`
- Stationary transformation of price
- Used as base for target

**ETH_log_return**: `ln(close_t / close_{t-1})`
- Inter-market correlation feature

**target**: `BTC_log_return` shifted by -1
- Next-period return to predict
- **NOT** used as input feature

**Stationarity Check**:
- ADF test confirms log returns stationary
- Raw prices non-stationary

### 2. Volume Features

**BTC_vol_log_return**: `ln(volume_t / volume_{t-1})`
- Volume momentum
- Captures trading activity changes

**log_rvol**: Log of relative volume
```python
rvol = volume / volume_ma20
log_rvol = ln(rvol + EPS)
```
- Normalized volume vs 20-period MA
- Log transform reduces skew

### 3. Volatility Features

**vol_gk**: Garman-Klass volatility
```python
log_hl = ln(high / low)^2
log_co = ln(close / open)^2
rv_gk = 0.5 * log_hl - (2*ln(2) - 1) * log_co
vol_gk = sqrt(max(rv_gk, 0))
```
- OHLC-based intrabar volatility
- More efficient than close-to-close

**vol_gk_z**: Z-score of vol_gk
```python
roll_mean_50 = vol_gk.rolling(50).mean().shift(1)
roll_std_50 = vol_gk.rolling(50).std().shift(1)
vol_gk_z = (vol_gk - roll_mean_50) / (roll_std_50 + EPS)
```
- Regime-normalized volatility
- Identifies volatility shocks (>3σ)

**vol_signed**: Directional volatility
```python
vol_signed = vol_gk * sign(BTC_log_return)
```
- Green: buy pressure (positive return)
- Red: sell pressure (negative return)

### 4. Microstructure Features

**clv**: Close Location Value
```python
rng = high - low
clv = ((close - low) - (high - close)) / rng
```
- Position of close within candle range
- Range: [-1, 1] (bottom to top)
- Predictive of next return

**wick_imbalance**: Wick asymmetry
```python
upper_wick = high - max(close, open)
lower_wick = min(close, open) - low
wick_imbalance = (upper_wick - lower_wick) / rng
```
- Upper wick dominance = selling pressure
- Lower wick dominance = buying pressure

### 5. Technical Indicators

**bb_pct_b**: Bollinger %B
```python
ma20 = close.rolling(20).mean().shift(1)
std20 = close.rolling(20).std().shift(1)
bb_upper = ma20 + 2 * std20
bb_lower = ma20 - 2 * std20
bb_pct_b = (close - bb_lower) / (bb_upper - bb_lower)
```
- Price position within bands
- >1: Overbought/breakout
- <0: Oversold/breakdown

**bb_width**: Bollinger Band width
```python
bb_width = (bb_upper - bb_lower) / (ma20 + EPS)
```
- Volatility level indicator
- Wide bands = high volatility

### 6. Market Structure Features

**btc_eth_corr**: Rolling correlation (30-day)
```python
btc_eth_corr = BTC_log_return.rolling(180).corr(ETH_log_return)
```
- Inter-market relationship
- High correlation = market regime

**stable_supply_change**: Stablecoin flow
```python
total_stable = USDT_market_cap + USDC_market_cap
stable_supply_change = ln(total_stable_t / total_stable_{t-1})
```
- "Dry powder" entering/leaving market

**ssr_z_score**: Stablecoin Supply Ratio Z
```python
ssr_ratio = BTC_market_cap / total_stable
roll_mean_90 = ssr_ratio.rolling(90).mean()
roll_std_90 = ssr_ratio.rolling(90).std()
ssr_z_score = (ssr_ratio - roll_mean_90) / (roll_std_90 + EPS)
```
- Buying power regime
- High Z: BTC expensive vs stablecoins

**usdt_dom_change**: USDT dominance change
```python
total_cap = BTC + ETH + total_stable
usdt_dom = USDT_market_cap / total_cap
usdt_dom_change = usdt_dom.diff()
```
- Risk-off pressure indicator

### 7. Network Activity Features

**addr_log_growth**: Address growth rate
```python
addr_log_growth = ln(active_addresses_t / active_addresses_{t-1})
```
- Network adoption momentum

**intensity_change**: Transaction intensity change
```python
tx_per_user = tx_count / active_addresses
log_tx_per_user = ln(tx_per_user)
intensity_change = log_tx_per_user.diff()
```
- Activity per user dynamics

**network_valuation_z**: Price-to-address ratio Z
```python
price_to_addr = close / active_addresses
roll_mean_90 = price_to_addr.rolling(90).mean()
roll_std_90 = price_to_addr.rolling(90).std()
network_valuation_z = (price_to_addr - roll_mean_90) / (roll_std_90 + EPS)
```
- Valuation vs usage
- High Z: Overvalued network

### 8. Mining Features

**hash_ribbon_spread**: Hash rate ribbon
```python
hash_ma30 = hash_rate.rolling(30).mean()
hash_ma60 = hash_rate.rolling(60).mean()
hash_ribbon_spread = (hash_ma30 - hash_ma60) / (hash_ma60 + EPS)
```
- Positive: Recovery (short MA above long MA)
- Negative: Capitulation (short MA below long MA)

**log_puell**: Log Puell Multiple
```python
rev_ma365 = miner_revenue.rolling(365).mean()
puell_multiple = miner_revenue / (rev_ma365 + EPS)
log_puell = ln(puell_multiple + EPS)
```
- Miner profitability regime
- High Puell: Overheated mining

### 9. On-chain Features

**onchain_mvrv_z**: MVRV Z-score
```python
roll_mean_730 = mvrv_ratio.rolling(730).mean()
roll_std_730 = mvrv_ratio.rolling(730).std()
onchain_mvrv_z = (mvrv_ratio - roll_mean_730) / (roll_std_730 + EPS)
```
- Valuation regime
- >2.5: Overvalued
- <1: Undervalued

**onchain_netflow_z**: Exchange netflow Z
```python
netflow = inflow_usd - outflow_usd
nf_mean = netflow.rolling(30).mean()
nf_std = netflow.rolling(30).std()
onchain_netflow_z = (netflow - nf_mean) / (nf_std + EPS)
```
- Sell/buy pressure shock
- Positive: Coins to exchanges (selling)
- Negative: Coins from exchanges (holding)

**reserve_ratio_change**: Exchange reserve change
```python
reserve_ratio = exchange_supply / total_supply
reserve_ratio_change = reserve_ratio.diff()
```
- Exchange inventory dynamics

### 10. News Features

**news_article_count**: Number of articles in period
**news_impact_score**: Composite impact
```python
news_impact_score = combined_sent_mean * ln(1 + article_count)
```
- Sentiment weighted by attention

**news_sentiment_decay_slow**: EMA decay
```python
news_sentiment_decay_slow = news_impact_score.ewm(span=6).mean()
```
- Lagged sentiment effect

**news_sentiment_shock**: Sentiment change
```python
news_sentiment_shock = news_impact_score.diff()
```
- Sudden sentiment shifts

### 11. Sentiment Index Features

**fng_change**: Fear & Greed change
```python
fng_change = sentiment_index_value.diff()
```
- Sentiment momentum

**fng_divergence**: F&G divergence from MA7
```python
fng_ma7 = sentiment_index_value.rolling(42).mean()
fng_divergence = sentiment_index_value - fng_ma7
```
- Contrarian signal
- High divergence: Potential reversal

## Feature Selection

### Correlation Analysis

Compute correlation with target:
```python
corr_matrix = train_ready_df.drop(columns=['timestamp']).corr()
target_corr = corr_matrix['target'].drop('target').sort_values(ascending=False)
```

### Multicollinearity Check

Identify high-correlation pairs (>0.9):
- Remove redundant features
- Example: `trades_log_return` removed

### Final Feature Set

**30+ features** selected:
- Price/returns: 2
- Volume: 2
- Volatility: 3
- Microstructure: 2
- Technical: 2
- Market structure: 3
- Network: 3
- Mining: 2
- On-chain: 3
- News: 4
- Sentiment: 2

## Stationarity

All features designed to be stationary:
- Log returns: First-order difference
- Z-scores: Mean-normalized
- Ratios: Relative measures
- Changes: First-order difference

## Visualization

Each feature category includes:
- Time series plots
- Distribution plots (histograms)
- Correlation with target
- Regime identification (thresholds)

## Output

### Final Dataset

**File**: `data/processed/final.pkl`
**Format**: Pickle
**Structure**:
- Column: `timestamp`
- Columns: 30+ engineered features
- Column: `target` (next-period return)

**Also saved as**: `final.csv`

### Data Quality

After feature engineering:
- Infinite values replaced with NaN
- NaNs dropped (from rolling windows)
- No missing values remaining

## Next Steps

After feature engineering, run:
1. [`train.ipynb`](training.md) - Train models
2. Evaluate on validation/test sets
3. Select best model by IC or directional accuracy
