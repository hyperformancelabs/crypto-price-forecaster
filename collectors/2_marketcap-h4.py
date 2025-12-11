"""
Market Cap H4 Data Collector from CoinMarketCap
Fetches historical market cap data for BTC, ETH, USDT, USDC with H4 interval
No API key required - uses internal API
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import (
    CMC_IDS, CMC_API_BASE, DEFAULT_TIMEFRAME,
    CHUNK_DAYS, RATE_LIMIT_DELAY, REQUEST_DELAY, ensure_directories, get_marketcap_file,
    END_TIME
)

import requests
import pandas as pd
import time
from datetime import datetime, timedelta
from utils.time_utils import calculate_collection_range, format_time_range_for_display, merge_dataframes, parse_end_time
import os


class MarketCapH4Fetcher:
    def __init__(self, end_time=None):
        self.base_url = CMC_API_BASE

        # Use config default if not provided
        if end_time is None:
            end_time = END_TIME

        self.end_time_config = end_time
        ensure_directories()

    def fetch_h4_data(self, coin_id, coin_name, start_date, end_date):
        url = f"{self.base_url}/cryptocurrency/historical"

        start_ts = int(start_date.timestamp())
        end_ts = int(end_date.timestamp())

        params = {
            'id': coin_id,
            'convertId': 2781,
            'timeStart': start_ts,
            'timeEnd': end_ts,
            'interval': DEFAULT_TIMEFRAME
        }

        try:
            response = requests.get(url, params=params)

            if response.status_code != 200:
                print(f"  ❌ HTTP {response.status_code}")
                return pd.DataFrame()

            data = response.json()

            if 'data' not in data or 'quotes' not in data['data']:
                print(f"  ⚠️ No data in response")
                return pd.DataFrame()

            quotes = data['data']['quotes']

            if not quotes:
                print(f"  ⚠️ Empty quotes")
                return pd.DataFrame()

            records = []
            for quote in quotes:
                q = quote['quote']
                records.append({
                    'timestamp': pd.to_datetime(q['timestamp']),
                    f'{coin_name}_market_cap': q.get('marketCap', 0)
                })

            df = pd.DataFrame(records)
            print(f"  ✅ {len(df)} H4 candles")

            return df

        except Exception as e:
            print(f"  ❌ Error: {e}")
            return pd.DataFrame()

    def fetch_coin_data(self, coin_name, coin_id):
        """
        Fetch market cap data for a coin based on collection configuration

        Args:
            coin_name: Name of the coin (e.g., 'BTC')
            coin_id: CoinMarketCap ID for the coin

        Returns:
            DataFrame with market cap data
        """
        # Calculate time range
        file_path = get_marketcap_file()
        start_date, end_date = calculate_collection_range(
            self.end_time_config,
            data_type='market_cap',
            coin=coin_name,
            file_path=file_path
        )

        print(f"\n📊 Fetching {coin_name} (ID: {coin_id})")
        print(f"   Range: {format_time_range_for_display(start_date, end_date)}")

        all_data = []
        current_start = start_date
        chunk_days = CHUNK_DAYS

        while current_start < end_date:
            current_end = min(
                current_start + timedelta(days=chunk_days),
                end_date
            )

            print(f"   ⏳ {current_start.date()} → {current_end.date()}", end="")

            df_chunk = self.fetch_h4_data(
                coin_id, coin_name, current_start, current_end
            )

            if not df_chunk.empty:
                all_data.append(df_chunk)

            current_start = current_end + timedelta(hours=4)

            time.sleep(RATE_LIMIT_DELAY)

        if not all_data:
            print(f"\n   ⚠️ No data collected for {coin_name}")
            return pd.DataFrame()

        df_full = pd.concat(all_data, ignore_index=True)
        df_full = df_full.drop_duplicates(
            subset=['timestamp']).sort_values('timestamp')
        df_full = df_full.reset_index(drop=True)

        print(f"\n   ✅ Total: {len(df_full)} H4 candles")
        print(f"   📅 {df_full['timestamp'].min()} → {df_full['timestamp'].max()}")

        return df_full

    def fetch_all_coins(self):
        print(f"\n{'='*60}")
        print(f"FETCH MARKET CAP H4 DATA")
        print(f"End Time: {self.end_time_config}")
        print(f"{'='*60}")

        all_data = {}

        for coin_name, coin_id in CMC_IDS.items():
            df = self.fetch_coin_data(coin_name, coin_id)

            if not df.empty:
                all_data[coin_name] = df

            time.sleep(REQUEST_DELAY)

        if not all_data:
            print("\n❌ No data collected!")
            return None

        # Merge with existing data if file exists
        file_path = get_marketcap_file()
        if os.path.exists(file_path):
            try:
                existing_df = pd.read_csv(file_path)
                existing_df['timestamp'] = pd.to_datetime(existing_df['timestamp'])

                print(f"\n{'='*60}")
                print(f"MERGING WITH EXISTING DATA")
                print(f"{'='*60}")

                # Start with existing data
                merged = existing_df.copy()

                # Add new data for each coin
                for coin_name, df in all_data.items():
                    if f'{coin_name}_market_cap' in merged.columns:
                        # Merge new data with existing data for this coin
                        merged = merged.drop(columns=[f'{coin_name}_market_cap'])
                        merged = pd.merge(
                            merged,
                            df[['timestamp', f'{coin_name}_market_cap']],
                            on='timestamp',
                            how='outer'
                        )
                    else:
                        # Add new column
                        merged = pd.merge(
                            merged,
                            df[['timestamp', f'{coin_name}_market_cap']],
                            on='timestamp',
                            how='outer'
                        )

                print(f"Merged with existing {len(existing_df)} records")
            except Exception as e:
                print(f"Warning: Could not merge with existing data: {e}")
                # Fall back to creating new merged dataset
                merged = list(all_data.values())[0][['timestamp']].copy()

                for coin_name, df in all_data.items():
                    merged = pd.merge(
                        merged,
                        df[['timestamp', f'{coin_name}_market_cap']],
                        on='timestamp',
                        how='outer'
                    )
        else:
            # Create new merged dataset
            print(f"\n{'='*60}")
            print(f"MERGING DATA")
            print(f"{'='*60}\n")

            print("🔗 Merging all market cap columns...")
            merged = list(all_data.values())[0][['timestamp']].copy()

            for coin_name, df in all_data.items():
                merged = pd.merge(
                    merged,
                    df[['timestamp', f'{coin_name}_market_cap']],
                    on='timestamp',
                    how='outer'
                )

        merged = merged.sort_values('timestamp').reset_index(drop=True)
        merged = merged.ffill().fillna(0)

        cols = ['timestamp'] + [
            f'{c}_market_cap' for c in CMC_IDS.keys()
        ]
        merged = merged[cols]

        # Apply END_TIME filtering to final merged dataset
        end_time = parse_end_time(self.end_time_config)
        merged = merged[merged['timestamp'] <= end_time]

        print(f"✅ Merged dataset:")
        print(f"   Rows: {len(merged):,} H4 candles")
        print(f"   Columns: {list(merged.columns)}")
        print(f"   Date range: {merged['timestamp'].min()} → {merged['timestamp'].max()}")

        return merged

    def save_to_csv(self, df):
        if df is None or df.empty:
            print("\n⚠️ No data to save!")
            return

        filepath = get_marketcap_file()
        df.to_csv(filepath, index=False)

        print(f"\n{'='*60}")
        print(f"💾 SAVED")
        print(f"{'='*60}")
        print(f"\nFile: {filepath}")
        print(f"Size: {os.path.getsize(filepath) / 1024:.1f} KB")
        print(f"Rows: {len(df):,}")
        print(f"Date range: {df['timestamp'].min()} → {df['timestamp'].max()}")

        print(f"\n📊 Market Cap Stats (latest):")
        latest = df.iloc[-1]
        for col in df.columns[1:]:
            val = latest[col]
            print(f"   {col:25s}: ${val/1e9:>10,.2f}B")

    def run(self):
        print("MARKET CAP H4 DATA COLLECTOR")
        print("Starting data collection...")

        start_time = time.time()

        df = self.fetch_all_coins()

        if df is not None:
            self.save_to_csv(df)

        elapsed = time.time() - start_time

        print(f"\n{'='*60}")
        print(f"✅ DONE!")
        print(f"{'='*60}")
        print(f"\n⏱️  Time: {elapsed/60:.2f} minutes")
        print(f"\n💡 Load data:")
        print(f"   import pandas as pd")
        print(f"   df = pd.read_csv('data/raw/marketcap/market_cap_h4.csv')")
        print(f"   df['timestamp'] = pd.to_datetime(df['timestamp'])")
        print(f"\n🎉 Ready for analysis!\n")


if __name__ == "__main__":
    try:
        fetcher = MarketCapH4Fetcher()
        fetcher.run()

    except KeyboardInterrupt:
        print("\n\n⚠️ Stopped (Ctrl+C)")
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
