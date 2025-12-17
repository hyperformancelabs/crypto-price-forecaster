"""
On-chain Metrics Daily Data Collector from CoinMetrics
Fetches historical on-chain valuation and holder metrics for BTC and ETH with daily interval
Collects: Total Supply, MVRV Ratio, Exchange Flows, Exchange Supply (Free tier metrics)
Note: Advanced holder metrics (HODL Waves, Illiquid Supply, Coin Days Destroyed, Whale Holdings)
      require paid APIs and are not available in free tiers.
No API key required - uses free Community API with comprehensive on-chain metrics.
"""

import sys
import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import (
    COINS, NETWORK_API_BASE, ONCHAINMETRICS_METRICS,
    ONCHAINMETRICS_CHUNK_DAYS, ONCHAINMETRICS_RATE_LIMIT,
    ensure_directories, get_onchainmetrics_file, END_TIME
)

import requests
import pandas as pd
import time
from datetime import datetime, timedelta
from utils.time_utils import calculate_collection_range, format_time_range_for_display, merge_dataframes, parse_end_time, truncate_dataset_to_end_time
import os


class CoinMetricsFetcher:
    def __init__(self):
        self.base_url = NETWORK_API_BASE

    def fetch_onchain_metrics(self, coin, metrics, start_date, end_date):
        """Fetch on-chain metrics for a specific date range"""
        url = f"{self.base_url}/timeseries/asset-metrics"

        params = {
            'assets': coin.lower(),
            'metrics': ','.join(metrics),
            'start_time': start_date.strftime('%Y-%m-%d'),
            'end_time': end_date.strftime('%Y-%m-%d'),
            'frequency': '1d',
            'page_size': 10000
        }

        try:
            response = requests.get(url, params=params, timeout=60)

            if response.status_code != 200:
                print(f"  ❌ HTTP {response.status_code}")
                return pd.DataFrame()

            data = response.json()

            if 'data' not in data or not data['data']:
                print(f"  ⚠️ No data in response")
                return pd.DataFrame()

            records = []
            for item in data['data']:
                record = {'timestamp': pd.to_datetime(item['time'])}

                # Map API metric names to readable column names
                for metric in metrics:
                    if metric in item:
                        value = float(item[metric]) if item[metric] else 0
                        if metric == 'SplyCur':
                            record['total_supply'] = value
                        elif metric == 'CapMVRVCur':
                            record['mvrv_ratio'] = value
                        elif metric == 'FlowInExNtv':
                            record['exchange_inflow_native'] = value
                        elif metric == 'FlowInExUSD':
                            record['exchange_inflow_usd'] = value
                        elif metric == 'FlowOutExNtv':
                            record['exchange_outflow_native'] = value
                        elif metric == 'FlowOutExUSD':
                            record['exchange_outflow_usd'] = value
                        elif metric == 'SplyExNtv':
                            record['exchange_supply_native'] = value
                        elif metric == 'SplyExUSD':
                            record['exchange_supply_usd'] = value
                        else:
                            record[metric.lower()] = value


                records.append(record)

            df = pd.DataFrame(records)
            print(f"  ✅ {len(df)} daily records")

            return df

        except Exception as e:
            print(f"  ❌ Error: {e}")
            return pd.DataFrame()


class OnchainMetricsCollector:
    def __init__(self, end_time=None):
        # Use config default if not provided
        if end_time is None:
            end_time = END_TIME

        self.end_time_config = end_time
        self.fetcher = CoinMetricsFetcher()
        self.base_url = NETWORK_API_BASE

        print("📊 ON-CHAIN METRICS DATA COLLECTION")
        print("   Available metrics (Free Tier):")
        print("     • SplyCur - Total Supply (BTC only)")
        print("     • CapMVRVCur - MVRV Ratio (Market Value/Realized Value)")
        print("     • FlowInEx/Out - Exchange Flows (proxy for holder behavior)")
        print("     • SplyEx - Exchange Supply (proxy for holder positioning)")
        print("")
        print("   ❌ Premium metrics (Paid tiers only):")
        print("     • HODL Waves - Supply by age bands")
        print("     • Illiquid Supply - Non-liquid supply metrics")
        print("     • Coin Days Destroyed - Economic activity metric")
        print("     • Whale Holdings - Large holder concentrations")
        print("   Sources requiring payment: Glassnode, CryptoQuant, Kaiko")
        print("")

    def fetch_coin_alltime(self, coin, file_path):
        """Fetch all historical on-chain metrics data for a coin"""
        metrics = ONCHAINMETRICS_METRICS.get(coin, [])
        if not metrics:
            print(f"  ⚠️ No metrics configured for {coin}")
            return pd.DataFrame()

        # Calculate time range based on config
        start_date, end_date = calculate_collection_range(
            self.end_time_config,
            data_type='onchainmetrics',
            coin=coin,
            file_path=file_path
        )

        print(f"\n📊 Fetching {coin} on-chain metrics")
        print(f"   Available Metrics: {', '.join(metrics)}")
        print(f"   Time Range: {format_time_range_for_display(start_date, end_date)}")

        all_data = []
        current_start = start_date
        chunk_days = ONCHAINMETRICS_CHUNK_DAYS

        while current_start < end_date:
            current_end = min(
                current_start + timedelta(days=chunk_days),
                end_date
            )

            print(f"   ⏳ {current_start.date()} → {current_end.date()}", end="")

            df_chunk = self.fetcher.fetch_onchain_metrics(
                coin, metrics, current_start, current_end
            )

            if not df_chunk.empty:
                all_data.append(df_chunk)

            current_start = current_end + timedelta(days=1)

            # Rate limiting - CoinMetrics allows 10 requests per 6 seconds
            time.sleep(ONCHAINMETRICS_RATE_LIMIT)

        if not all_data:
            print(f"\n   ⚠️ No data collected for {coin}")
            return pd.DataFrame()

        df_full = pd.concat(all_data, ignore_index=True)
        df_full = df_full.drop_duplicates(
            subset=['timestamp']).sort_values('timestamp')
        df_full = df_full.reset_index(drop=True)

        # Forward-fill missing values and handle NaN values
        numeric_cols = df_full.select_dtypes(include=['number']).columns
        df_full[numeric_cols] = df_full[numeric_cols].ffill().fillna(0)

        print(f"\n   ✅ Total: {len(df_full)} daily records")
        print(f"   📅 {df_full['timestamp'].min()} → {df_full['timestamp'].max()}")

        return df_full

    def fetch_all_coins(self):
        """Fetch on-chain metrics data for all configured coins"""
        print(f"\n{'='*60}")
        print(f"FETCH ON-CHAIN METRICS DAILY DATA")
        print(f"{'='*60}")

        all_data = {}

        for coin in COINS:
            file_path = get_onchainmetrics_file(coin)

            # Load existing data if file exists
            existing_df = None
            if os.path.exists(file_path):
                try:
                    existing_df = pd.read_csv(file_path)
                    existing_df['timestamp'] = pd.to_datetime(existing_df['timestamp'])

                    # Apply END_TIME truncation to existing data
                    existing_df = truncate_dataset_to_end_time(existing_df, self.end_time_config)

                    print(f"Found existing {coin} data: {len(existing_df)} records")
                    print(f"Date range: {existing_df['timestamp'].min()} → {existing_df['timestamp'].max()}")
                except Exception as e:
                    print(f"Warning: Could not load existing data: {e}")
                    existing_df = None

            df = self.fetch_coin_alltime(coin, file_path)

            if not df.empty:
                # Merge with existing data if file exists
                if existing_df is not None:
                    try:
                        df = merge_dataframes(existing_df, df)
                        print(f"Merged with existing data. Total records: {len(df)}")
                    except Exception as e:
                        print(f"Warning: Could not merge with existing data: {e}")

                # Apply END_TIME truncation to final merged data
                df = truncate_dataset_to_end_time(df, self.end_time_config)

                all_data[coin] = df
                # Save individual coin file
                self.save_coin_csv(df, coin)

            time.sleep(1)  # Small delay between coins

        return all_data

    def save_coin_csv(self, df, coin):
        """Save on-chain metrics data for a single coin"""
        if df.empty:
            return

        # Apply END_TIME truncation
        df = truncate_dataset_to_end_time(df, self.end_time_config)

        filepath = get_onchainmetrics_file(coin)
        df.to_csv(filepath, index=False)

        print(f"\n💾 Saved {coin}: {filepath}")
        print(f"   Size: {os.path.getsize(filepath) / 1024:.1f} KB")
        print(f"   Rows: {len(df):,}")
        print(f"   Date range: {df['timestamp'].min()} → {df['timestamp'].max()}")

    def generate_summary(self):
        """Generate summary of collected on-chain metrics data"""
        print(f"\n{'='*60}")
        print(f"ON-CHAIN METRICS DATA SUMMARY")
        print(f"{'='*60}")

        from pathlib import Path
        onchain_files = list(Path("data/raw/onchainmetrics").glob("*.csv"))

        print(f"On-chain metrics files: {len(onchain_files)}")
        print(f"Location: {os.path.abspath('data/raw/onchainmetrics')}/")

        for file in onchain_files:
            df = pd.read_csv(file)
            print(f"  - {file.name}: {len(df):,} records")

            # Show latest values for key metrics
            if not df.empty:
                latest = df.iloc[-1]
                print(f"    Latest ({latest['timestamp'].split()[0]}):")

                if 'total_supply' in df.columns and pd.notna(latest['total_supply']):
                    print(f"      Total Supply: {latest['total_supply']:,.0f}")

                if 'mvrv_ratio' in df.columns and pd.notna(latest['mvrv_ratio']):
                    print(f"      MVRV Ratio: {latest['mvrv_ratio']:.2f}")

                if 'exchange_inflow_usd' in df.columns and 'exchange_outflow_usd' in df.columns:
                    net_flow = latest['exchange_inflow_usd'] - latest['exchange_outflow_usd']
                    flow_color = "📈" if net_flow > 0 else "📉"
                    print(f"      Net Flow USD: {flow_color} ${net_flow:,.0f}")

        print(f"\n📊 On-Chain Metrics Analysis Notes:")
        print(f"   • MVRV > 2.5: Typically overvalued (distribution phase)")
        print(f"   • MVRV < 1: Typically undervalued (accumulation phase)")
        print(f"   • Positive Net Flow: Coins moving to exchanges (selling pressure)")
        print(f"   • Negative Net Flow: Coins leaving exchanges (holding)")
        print(f"   • Total Supply: Circulating supply metrics (BTC only)")

        print(f"\n⚠️  Data Limitations:")
        print(f"   • HODL Waves, Illiquid Supply, CDD, Whale data require paid APIs")
        print(f"   • Current metrics serve as proxies for on-chain behavior")
        print(f"   • For comprehensive analysis, consider Glassnode/CryptoQuant subscriptions")

        print(f"\n✅ On-chain metrics data collection complete!")

    def run(self):
        """Main execution method"""
        print("ON-CHAIN METRICS DAILY DATA COLLECTOR")
        print("Starting data collection with free tier metrics...")

        start_time = time.time()

        all_data = self.fetch_all_coins()

        if all_data:
            self.generate_summary()

        elapsed = time.time() - start_time

        print(f"\n{'='*60}")
        print(f"✅ DONE!")
        print(f"{'='*60}")
        print(f"\n⏱️  Time: {elapsed/60:.2f} minutes")
        print(f"\n💡 Load data:")
        print(f"   import pandas as pd")
        print(f"   df_btc = pd.read_csv('data/raw/onchainmetrics/BTC_onchainmetrics.csv')")
        print(f"   df_eth = pd.read_csv('data/raw/onchainmetrics/ETH_onchainmetrics.csv')")
        print(f"   df_btc['timestamp'] = pd.to_datetime(df_btc['timestamp'])")
        print(f"   df_eth['timestamp'] = pd.to_datetime(df_eth['timestamp'])")
        print(f"\n🎉 Ready for on-chain metrics analysis!\n")


if __name__ == "__main__":
    try:
        collector = OnchainMetricsCollector()
        collector.run()

    except KeyboardInterrupt:
        print("\n\n⚠️ Stopped (Ctrl+C)")
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()