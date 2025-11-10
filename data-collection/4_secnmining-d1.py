"""
Mining Metrics Daily Data Collector from Blockchain.info
Fetches historical mining metrics for BTC with daily interval
Collects: Hash Rate, Mining Difficulty, Miner Revenue
No API key required - uses free public API
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import (
    BLOCKCHAIN_API_BASE, MINING_METRICS, ensure_directories, get_mining_file, SECNMINING_DIR
)

import requests
import pandas as pd
import time
from datetime import datetime


class BlockchainInfoFetcher:
    def __init__(self):
        self.base_url = BLOCKCHAIN_API_BASE
        ensure_directories()

    def fetch_mining_metric(self, metric_key, start_timestamp=None, end_timestamp=None):
        """Fetch mining metric data from Blockchain.info API"""
        url = f"{self.base_url}/{metric_key}"

        # For historical data, use timespan=all to get full dataset
        if start_timestamp is None and end_timestamp is None:
            params = {
                'format': 'json',
                'timespan': 'all'
            }
        else:
            params = {
                'format': 'json',
                'start_time': start_timestamp,
                'end_time': end_timestamp
            }

        try:
            response = requests.get(url, params=params, timeout=60)

            if response.status_code != 200:
                print(f"  ❌ HTTP {response.status_code} for {metric_key}")
                return pd.DataFrame()

            data = response.json()

            if 'status' not in data or data['status'] != 'ok':
                print(f"  ❌ API error for {metric_key}: {data.get('description', 'Unknown error')}")
                return pd.DataFrame()

            if 'values' not in data or not data['values']:
                print(f"  ⚠️ No data in response for {metric_key}")
                return pd.DataFrame()

            records = []
            metric_info = MINING_METRICS.get(metric_key, {})

            for item in data['values']:
                record = {
                    'timestamp': pd.to_datetime(item['x'], unit='s'),
                    'metric': metric_key,
                    'value': float(item['y']) if item['y'] else 0,
                    'unit': metric_info.get('unit', ''),
                    'name': metric_info.get('name', metric_key)
                }
                records.append(record)

            df = pd.DataFrame(records)
            print(f"  ✅ {len(df)} daily records for {metric_info.get('name', metric_key)}")

            return df

        except Exception as e:
            print(f"  ❌ Error fetching {metric_key}: {e}")
            return pd.DataFrame()

    def fetch_all_mining_metrics(self):
        """Fetch all configured mining metrics"""
        print(f"\n{'='*60}")
        print(f"FETCH MINING METRICS DAILY DATA")
        print(f"{'='*60}")

        print(f"Collecting BTC mining metrics")
        print(f"Metrics: {', '.join(MINING_METRICS.keys())}")
        print(f"Range: All available historical data")

        all_data = []

        for metric_key in MINING_METRICS.keys():
            print(f"\n📊 Fetching {MINING_METRICS[metric_key]['name']}", end="")

            # Fetch all historical data in one request
            df_metric = self.fetch_mining_metric(metric_key)

            if not df_metric.empty:
                df_metric = df_metric.drop_duplicates(
                    subset=['timestamp']).sort_values('timestamp')
                df_metric = df_metric.reset_index(drop=True)

                print(f"  ✅ {len(df_metric)} daily records")
                print(f"   📅 {df_metric['timestamp'].min()} → {df_metric['timestamp'].max()}")

                all_data.append(df_metric)
            else:
                print(f"  ⚠️ No data collected for {metric_key}")

        if not all_data:
            print(f"\n⚠️ No mining data collected")
            return pd.DataFrame()

        # Pivot data to have metrics as columns
        df_full = pd.concat(all_data, ignore_index=True)
        df_pivot = df_full.pivot_table(
            index='timestamp',
            columns='metric',
            values='value',
            aggfunc='first'
        ).reset_index()

        # Rename columns to be more readable
        column_mapping = {}
        for metric_key in MINING_METRICS.keys():
            if metric_key in df_pivot.columns:
                if metric_key == 'hash-rate':
                    column_mapping[metric_key] = 'hash_rate_ths'
                elif metric_key == 'difficulty':
                    column_mapping[metric_key] = 'mining_difficulty'
                elif metric_key == 'miners-revenue':
                    column_mapping[metric_key] = 'miner_revenue_usd'

        df_pivot = df_pivot.rename(columns=column_mapping)

        # Forward-fill missing values and handle NaN values
        numeric_cols = df_pivot.select_dtypes(include=['number']).columns
        df_pivot[numeric_cols] = df_pivot[numeric_cols].ffill().fillna(0)

        print(f"\n📊 Final dataset: {len(df_pivot)} daily records")
        print(f"Columns: {list(df_pivot.columns)}")

        return df_pivot

    def save_mining_data(self, df):
        """Save mining data to CSV file"""
        if df.empty:
            return

        filepath = get_mining_file()
        df.to_csv(filepath, index=False)

        print(f"\n💾 Saved mining data: {filepath}")
        print(f"   Size: {os.path.getsize(filepath) / 1024:.1f} KB")
        print(f"   Rows: {len(df):,}")
        print(f"   Date range: {df['timestamp'].min()} → {df['timestamp'].max()}")

    def generate_summary(self):
        """Generate summary of collected mining data"""
        print(f"\n{'='*60}")
        print(f"SUMMARY")
        print(f"{'='*60}")

        from pathlib import Path
        mining_files = list(Path(SECNMINING_DIR).glob("*.csv"))

        print(f"Mining files: {len(mining_files)}")
        print(f"Location: {os.path.abspath(SECNMINING_DIR)}/")

        for file in mining_files:
            df = pd.read_csv(file)
            print(f"  - {file.name}: {len(df):,} records")

            # Show latest values for each metric
            if not df.empty:
                latest = df.iloc[-1]
                print(f"    Latest ({latest['timestamp'].split()[0]}):")
                for col in df.columns:
                    if col != 'timestamp' and pd.notna(latest[col]):
                        if 'revenue' in col.lower():
                            print(f"      {col}: ${latest[col]:,.2f}")
                        elif 'hash_rate' in col.lower():
                            print(f"      {col}: {latest[col]:,.2f} TH/s")
                        else:
                            print(f"      {col}: {latest[col]:,.0f}")

        print(f"\n✅ Mining metrics data collection complete!")

    def run(self):
        """Main execution method"""
        print("MINING METRICS DAILY DATA COLLECTOR")
        print("Starting data collection...")

        start_time = time.time()

        df = self.fetch_all_mining_metrics()

        if not df.empty:
            self.save_mining_data(df)
            self.generate_summary()

        elapsed = time.time() - start_time

        print(f"\n{'='*60}")
        print(f"✅ DONE!")
        print(f"{'='*60}")
        print(f"\n⏱️  Time: {elapsed/60:.2f} minutes")
        print(f"\n💡 Load data:")
        print(f"   import pandas as pd")
        print(f"   df = pd.read_csv('data/raw/secnmining/BTC_mining_d1.csv')")
        print(f"   df['timestamp'] = pd.to_datetime(df['timestamp'])")
        print(f"\n🎉 Ready for analysis!\n")


if __name__ == "__main__":
    try:
        fetcher = BlockchainInfoFetcher()
        fetcher.run()

    except KeyboardInterrupt:
        print("\n\n⚠️ Stopped (Ctrl+C)")
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()