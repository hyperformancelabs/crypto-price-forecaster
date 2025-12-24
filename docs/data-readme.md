# Data Dictionary

This document describes the meaning of columns in:
- `data/processed/master_dataset_h4_cleaned_v1.csv` (original cleaned dataset)
- `data/processed/final.csv` (feature-engineered/target dataset)

Notes:
- Some on-chain/news columns depend on data providers and the processing pipeline; the descriptions below follow the most common definitions.
- H4 dataset: each row typically represents one 4-hour candle (if your pipeline follows the filename naming).

## 1) `master_dataset_h4_cleaned_v1.csv`

| Column | Meaning |
|---|---|
| `timestamp` | Time point of the period (candle timestamp). |
| `BTC_open` | BTC opening price in the period. |
| `BTC_high` | BTC highest price in the period. |
| `BTC_low` | BTC lowest price in the period. |
| `BTC_close` | BTC closing price in the period. |
| `BTC_volume` | BTC trading volume (base volume). |
| `BTC_quote_volume` | BTC trading volume in quote currency (quote volume, typically USD/USDT). |
| `BTC_trades` | Number of trades/matched orders for BTC in the period. |
| `ETH_open` | ETH opening price in the period. |
| `ETH_high` | ETH highest price in the period. |
| `ETH_low` | ETH lowest price in the period. |
| `ETH_close` | ETH closing price in the period. |
| `ETH_volume` | ETH trading volume (base volume). |
| `ETH_quote_volume` | ETH trading volume in quote currency (quote volume). |
| `ETH_trades` | Number of trades/matched orders for ETH in the period. |
| `BTC_market_cap` | BTC market capitalization at that time. |
| `ETH_market_cap` | ETH market capitalization at that time. |
| `USDT_market_cap` | USDT market cap (approximately total supply since price is usually ~1). |
| `USDC_market_cap` | USDC market cap (approximately total supply since price is usually ~1). |
| `BTC_active_addresses` | Number of active BTC addresses (typically: those with send/receive on-chain) in the period. |
| `BTC_tx_count` | Number of BTC on-chain transactions in the period. |
| `ETH_active_addresses` | Number of active ETH addresses in the period. |
| `ETH_tx_count` | Number of ETH on-chain transactions in the period. |
| `mining_difficulty` | Mining difficulty (BTC). |
| `hash_rate_ths` | Network hashrate (in TH/s). |
| `miner_revenue_usd` | Miner revenue (USD) in the period (typically includes block reward + fees). |
| `BTC_onchain_total_supply` | BTC total on-chain supply (circulating/issued supply depending on source). |
| `BTC_onchain_mvrv_ratio` | MVRV = Market Value / Realized Value (on-chain valuation indicator). |
| `BTC_onchain_exchange_inflow_native` | Amount of BTC deposited to exchanges (exchange inflow) in BTC units. |
| `BTC_onchain_exchange_inflow_usd` | Exchange inflow converted to USD. |
| `BTC_onchain_exchange_outflow_native` | Amount of BTC withdrawn from exchanges (exchange outflow) in BTC units. |
| `BTC_onchain_exchange_outflow_usd` | Exchange outflow converted to USD. |
| `BTC_onchain_exchange_supply_native` | Balance of BTC held on exchange wallets (BTC). |
| `BTC_onchain_exchange_supply_usd` | BTC balance on exchanges converted to USD. |
| `news_article_count` | Number of news articles collected in the period. |
| `news_log_article_count` | Log-transform of article count (typically `log(1 + count)` to reduce skew). |
| `has_news` | Flag 0/1: whether there was news in the period. |
| `news_combined_sent_mean` | Mean of combined sentiment for news in the period. |
| `news_combined_sent_std` | Standard deviation of combined sentiment. |
| `news_combined_sent_max` | Maximum combined sentiment. |
| `news_combined_sent_min` | Minimum combined sentiment. |
| `news_combined_sent_max_abs` | Maximum absolute value of sentiment (strongest "extreme" level). |
| `news_combined_sent_sum_abs` | Sum of absolute sentiment (total "intensity" of sentiment). |
| `news_bull_ratio` | Ratio of bullish (positive) news in the period. |
| `news_bear_ratio` | Ratio of bearish (negative) news in the period. |
| `news_p_bull_mean` | Mean probability of news being bullish (from classification model). |
| `news_p_bear_mean` | Mean probability of news being bearish. |
| `news_p_neu_mean` | Mean probability of news being neutral. |
| `news_max_p_bull_bucket` | Bucket/label based on maximum `p_bull` level (typically probability bin). |
| `news_max_p_bear_bucket` | Bucket/label based on maximum `p_bear` level (typically probability bin). |
| `news_is_conflict` | Flag 0/1: conflicting/divergent news signals (e.g., both strong bull and bear). |
| `news_head_sent_mean` | Mean sentiment calculated separately on headlines. |
| `news_head_sent_std` | Standard deviation of headline sentiment. |
| `news_head_sent_max` | Maximum headline sentiment. |
| `news_head_sent_min` | Minimum headline sentiment. |
| `news_head_global_diff_mean` | Mean difference between headline sentiment and content/"global" sentiment (depends on pipeline). |
| `news_head_global_abs_diff_mean` | Mean absolute difference between headline and global sentiment. |
| `news_head_exag_ratio` | "Clickbait" ratio: headline more extreme than content (typically based on diff/abs diff). |
| `sentiment_index_value` | Value of composite sentiment index (your own index/source). |
| `sentiment_index_classification` | Classification from sentiment index (e.g., Fear/Neutral/Greed or Bear/Neutral/Bull). |

## 2) `final.csv`

| Column | Meaning |
|---|---|
| `timestamp` | Time point corresponding to the feature row. |
| `BTC_log_return` | BTC log return: `ln(C_t / C_{t-1})` (typically using close price). |
| `ETH_log_return` | ETH log return: `ln(C_t / C_{t-1})`. |
| `target` | Target variable for forecasting (typically future return/price according to forecast horizon in pipeline). |
| `BTC_vol_log_return` | Volatility of `BTC_log_return` (typically rolling std; sometimes log-vol). |
| `log_rvol` | Log of realized volatility (actual measured volatility from rolling returns). |
| `vol_gk` | Garman-Klass volatility (volatility estimate based on OHLC). |
| `vol_gk_z` | Z-score of `vol_gk` (standardized by rolling mean/std). |
| `vol_signed` | Signed volatility (typically signed according to return direction to distinguish rise/fall). |
| `clv` | Close Location Value: position of close price within candle range (typically normalized to [-1, 1]). |
| `wick_imbalance` | Candle wick imbalance (upper wick vs lower wick), representing buy/sell pressure. |
| `bb_pct_b` | Bollinger %B: price position relative to Bollinger Bands (0-1, can exceed boundaries). |
| `bb_width` | Bollinger Band width (represents volatility level). |
| `btc_eth_corr` | Rolling correlation between BTC and ETH returns. |
| `log_rel_ats` | Log "relative average trade size" (typically based on `quote_volume / trades`, can be relative ratio). |
| `stable_supply_change` | Change in stablecoin supply (typically from `USDT_market_cap`/`USDC_market_cap` or total). |
| `ssr_z_score` | Z-score of Stablecoin Supply Ratio (SSR typically is BTC market cap / stablecoin market cap). |
| `usdt_dom_change` | Change in "USDT dominance" (USDT weight in total market or within stablecoin group). |
| `addr_log_growth` | Log growth of active addresses (typically: `ln(A_t/A_{t-1})`). |
| `intensity_change` | Change in network activity intensity (typically based on tx_count or tx/addr). |
| `network_valuation_z` | Z-score of network valuation indicator (typically NVT or variant). |
| `hash_ribbon_spread` | Hash Ribbon spread (typically: short-term MA hashrate − long-term MA). |
| `log_puell` | Log of Puell Multiple (miner revenue / long-term MA of miner revenue). |
| `onchain_mvrv_z` | Z-score of MVRV (standardized by rolling). |
| `onchain_netflow_z` | Z-score of exchange netflow (inflow − outflow), standardized. |
| `reserve_ratio_change` | Change in "reserve ratio" (depends on on-chain/pipeline definition). |
| `news_article_count` | Number of articles in period (used directly as feature). |
| `news_impact_score` | Composite "news impact" score (typically combines article count + sentiment level + weights). |
| `news_sentiment_decay_slow` | Sentiment smoothed/decayed over time (EMA/slow decay). |
| `news_sentiment_shock` | Sentiment "shock": sudden change compared to baseline/decay. |
| `fng_change` | Change in Fear & Greed Index (if FNG source available). |
| `fng_divergence` | Divergence between FNG and price/return (or between FNG and baseline; depends on pipeline). |

