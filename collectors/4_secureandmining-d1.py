#!/usr/bin/env python
"""
Security and Mining Metrics Daily Data Collector from Blockchain.info
Fetches historical security and mining metrics for BTC with daily interval
Collects: Hash Rate, Mining Difficulty, Miner Revenue
No API key required - uses free public API
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import (
    BLOCKCHAIN_API_BASE, MINING_METRICS, ensure_directories, get_mining_file, SECUREANDMINING_DIR,
    END_TIME
)

import requests
import pandas as pd
import time
from datetime import datetime
from utils.time_utils import calculate_collection_range, format_time_range_for_display, merge_dataframes, parse_end_time, truncate_dataset_to_end_time
import os


class BlockchainInfoFetcher:
    def __init__(self, end_time=None):
        self.base_url = BLOCKCHAIN_API_BASE

        # Use config default if not provided
        if end_time is None:
            end_time = END_TIME

        self.end_time_config = end_time
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
                    'timestamp': pd.to_datetime(item['x'], unit='s', utc=True),
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
        print(f"FETCH SECURITY AND MINING METRICS DAILY DATA")
        print(f"End Time: {self.end_time_config}")
        print(f"{'='*60}")

        # Get file path and check existing data
        file_path = get_mining_file()

        # Load existing data if file exists
        existing_df = None
        if os.path.exists(file_path):
            try:
                existing_df = pd.read_csv(file_path)
                existing_df['timestamp'] = pd.to_datetime(existing_df['timestamp'])

                # Apply END_TIME truncation to existing data
                existing_df = truncate_dataset_to_end_time(existing_df, self.end_time_config)

                print(f"Found existing data: {len(existing_df)} records")
                print(f"Date range: {existing_df['timestamp'].min()} → {existing_df['timestamp'].max()}")
            except Exception as e:
                print(f"Warning: Could not load existing data: {e}")
                existing_df = None

        # Calculate time range based on config
        start_time, end_time = calculate_collection_range(
            self.end_time_config,
            data_type='secureandmining',
            file_path=file_path
        )

        print(f"Collecting BTC mining metrics")
        print(f"Metrics: {', '.join(MINING_METRICS.keys())}")
        print(f"Time Range: {format_time_range_for_display(start_time, end_time)}")

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

        # Merge with existing data if applicable
        if existing_df is not None:
            df_pivot = merge_dataframes(existing_df, df_pivot)
            print(f"Merged with existing data. Total records: {len(df_pivot)}")

        return df_pivot

    def save_mining_data(self, df):
        """Save mining data to CSV file"""
        if df.empty:
            return

        # Apply END_TIME truncation
        df = truncate_dataset_to_end_time(df, self.end_time_config)

        filepath = get_mining_file()
        df.to_csv(filepath, index=False)

        print(f"\n💾 Saved security and mining data: {filepath}")
        print(f"   Size: {os.path.getsize(filepath) / 1024:.1f} KB")
        print(f"   Rows: {len(df):,}")
        print(f"   Date range: {df['timestamp'].min()} → {df['timestamp'].max()}")

    def generate_summary(self):
        """Generate summary of collected security and mining data"""
        print(f"\n{'='*60}")
        print(f"SUMMARY")
        print(f"{'='*60}")

        from pathlib import Path
        mining_files = list(Path(SECUREANDMINING_DIR).glob("*.csv"))

        print(f"Security and mining files: {len(mining_files)}")
        print(f"Location: {os.path.abspath(SECUREANDMINING_DIR)}/")

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

        print(f"\n✅ Security and mining metrics data collection complete!")

    def run(self):
        """Main execution method"""
        print("SECURITY AND MINING METRICS DAILY DATA COLLECTOR")
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
        print(f"   df = pd.read_csv('data/raw/secureandmining/BTC_mining_d1.csv')")
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