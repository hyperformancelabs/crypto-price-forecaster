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
    CHUNK_DAYS, RATE_LIMIT_DELAY, REQUEST_DELAY, ensure_directories, get_marketcap_file
)

import requests
import pandas as pd
import time
from datetime import datetime, timedelta


class MarketCapH4Fetcher:
    def __init__(self):
        self.base_url = CMC_API_BASE
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

    def fetch_coin_alltime(self, coin_name, coin_id, start_date=None):
        if start_date is None:
            start_date = datetime(2013, 4, 28)

        end_date = datetime.now()

        print(f"\n📊 Fetching {coin_name} (ID: {coin_id})")
        print(f"   Range: {start_date.date()} → {end_date.date()}")

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
        print(f"{'='*60}")

        all_data = {}

        for coin_name, coin_id in CMC_IDS.items():
            df = self.fetch_coin_alltime(coin_name, coin_id)

            if not df.empty:
                all_data[coin_name] = df

            time.sleep(REQUEST_DELAY)

        if not all_data:
            print("\n❌ No data collected!")
            return None

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

        merged['total_market_cap'] = (
            merged['BTC_market_cap'] +
            merged['ETH_market_cap'] +
            merged['USDT_market_cap'] +
            merged['USDC_market_cap']
        ) * 2.0

        cols = ['timestamp', 'total_market_cap'] + [
            f'{c}_market_cap' for c in CMC_IDS.keys()
        ]
        merged = merged[cols]

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
