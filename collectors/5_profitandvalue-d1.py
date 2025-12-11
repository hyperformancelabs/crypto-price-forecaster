"""
Profit and Value Daily Data Collector from CoinMetrics
Fetches historical profit and value metrics for BTC and ETH with daily interval
Collects: MVRV Ratio, Exchange Inflows/Outflows, Exchange Supply, calculates Realized Price
No API key required - uses free Community API
"""

import sys
import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import (
    COINS, NETWORK_API_BASE, PROFITANDVALUE_METRICS,
    PROFITANDVALUE_CHUNK_DAYS, PROFITANDVALUE_RATE_LIMIT,
    ensure_directories, get_profitandvalue_file,
    END_TIME
)

import requests
import pandas as pd
import time
from datetime import datetime, timedelta
from utils.time_utils import calculate_collection_range, format_time_range_for_display, merge_dataframes, parse_end_time
import os


class CoinMetricsProfitAndValueFetcher:
    def __init__(self, end_time=None):
        self.base_url = NETWORK_API_BASE

        # Use config default if not provided
        if end_time is None:
            end_time = END_TIME

        self.end_time_config = end_time
        ensure_directories()

    def fetch_profit_and_value_metrics(self, coin, metrics, start_date, end_date):
        """Fetch profit and value metrics for a specific date range"""
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
                        value = float(item[metric]) if item[metric] is not None else 0

                        if metric == 'CapMVRVCur':
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

    def fetch_coin_alltime(self, coin):
        """Fetch all historical profit and value data for a coin"""
        metrics = PROFITANDVALUE_METRICS.get(coin, [])
        if not metrics:
            print(f"  ⚠️ No metrics configured for {coin}")
            return pd.DataFrame()

        # Set appropriate start dates based on coin history
        if coin == 'BTC':
            start_date = datetime(2009, 1, 1)  # Bitcoin inception
        elif coin == 'ETH':
            start_date = datetime(2015, 7, 30)  # Ethereum launch
        else:
            start_date = datetime(2015, 1, 1)  # Default for other coins

        end_date = datetime.now()

        print(f"\n📊 Fetching {coin} profit and value metrics")
        print(f"   Metrics: {', '.join(metrics)}")
        print(f"   Range: {start_date.date()} → {end_date.date()}")

        all_data = []
        current_start = start_date
        chunk_days = PROFITANDVALUE_CHUNK_DAYS

        while current_start < end_date:
            current_end = min(
                current_start + timedelta(days=chunk_days),
                end_date
            )

            print(f"   ⏳ {current_start.date()} → {current_end.date()}", end="")

            df_chunk = self.fetch_profit_and_value_metrics(
                coin, metrics, current_start, current_end
            )

            if not df_chunk.empty:
                all_data.append(df_chunk)

            current_start = current_end + timedelta(days=1)

            # Rate limiting - CoinMetrics allows 10 requests per 6 seconds
            time.sleep(PROFITANDVALUE_RATE_LIMIT)

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
        """Fetch profit and value data for all configured coins"""
        print(f"\n{'='*60}")
        print(f"FETCH PROFIT AND VALUE DAILY DATA")
        print(f"{'='*60}")

        all_data = {}

        for coin in COINS:
            df = self.fetch_coin_alltime(coin)

            if not df.empty:
                all_data[coin] = df
                # Save individual coin file
                self.save_coin_csv(df, coin)

            time.sleep(1)  # Small delay between coins

        return all_data

    def save_coin_csv(self, df, coin):
        """Save profit and value data for a single coin"""
        if df.empty:
            return

        # Apply END_TIME filtering
        end_time = parse_end_time(self.end_time_config)
        df_filtered = df[df['timestamp'] <= end_time]

        filepath = get_profitandvalue_file(coin)
        df_filtered.to_csv(filepath, index=False)

        print(f"\n💾 Saved {coin}: {filepath}")
        print(f"   Size: {os.path.getsize(filepath) / 1024:.1f} KB")
        print(f"   Rows: {len(df):,}")
        print(f"   Date range: {df['timestamp'].min()} → {df['timestamp'].max()}")

    def generate_summary(self):
        """Generate summary of collected profit and value data"""
        print(f"\n{'='*60}")
        print(f"SUMMARY")
        print(f"{'='*60}")

        from pathlib import Path
        exchange_files = list(Path("data/raw/profitandvalue").glob("*.csv"))

        print(f"Profit and value files: {len(exchange_files)}")
        print(f"Location: {os.path.abspath('data/raw/profitandvalue')}/")

        for file in exchange_files:
            df = pd.read_csv(file)
            print(f"  - {file.name}: {len(df):,} records")

            # Show latest values for key metrics
            if not df.empty:
                latest = df.iloc[-1]
                print(f"    Latest ({latest['timestamp'].split()[0]}):")
                for col in df.columns:
                    if col != 'timestamp' and pd.notna(latest[col]):
                        if 'price' in col.lower() or 'usd' in col.lower():
                            if col in ['realized_price_usd']:
                                print(f"      {col}: ${latest[col]:,.2f}")
                            else:
                                print(f"      {col}: ${latest[col]:,.0f}")
                        elif 'ratio' in col.lower():
                            print(f"      {col}: {latest[col]:.3f}")
                        else:
                            print(f"      {col}: {latest[col]:,.2f}")

        print(f"\n✅ Profit and value data collection complete!")

    def run(self):
        """Main execution method"""
        print("PROFIT AND VALUE DAILY DATA COLLECTOR")
        print("Starting data collection...")

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
        print(f"   df_btc = pd.read_csv('data/raw/profitandvalue/BTC_profitandvalue.csv')")
        print(f"   df_eth = pd.read_csv('data/raw/profitandvalue/ETH_profitandvalue.csv')")
        print(f"   df_btc['timestamp'] = pd.to_datetime(df_btc['timestamp'])")
        print(f"   df_eth['timestamp'] = pd.to_datetime(df_eth['timestamp'])")
        print(f"\n🎉 Ready for analysis!\n")


if __name__ == "__main__":
    try:
        fetcher = CoinMetricsProfitAndValueFetcher()
        fetcher.run()

    except KeyboardInterrupt:
        print("\n\n⚠️ Stopped (Ctrl+C)")
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()