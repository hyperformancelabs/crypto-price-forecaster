"""
Network Activity Daily Data Collector from CoinMetrics
Fetches historical network activity metrics for BTC and ETH with daily interval
Collects: Active Addresses, New Addresses, Tx Count, Tx Volume (USD), Gas Fees (ETH)
No API key required - uses free Community API
"""

import sys
import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import (
    COINS, NETWORK_API_BASE, NETWORK_ACTIVITY_METRICS,
    NETWORK_CHUNK_DAYS, NETWORK_RATE_LIMIT,
    ensure_directories, get_networkactivity_file
)

import requests
import pandas as pd
import time
from datetime import datetime, timedelta


class CoinMetricsFetcher:
    def __init__(self):
        self.base_url = NETWORK_API_BASE
        ensure_directories()

    def fetch_network_metrics(self, coin, metrics, start_date, end_date):
        """Fetch network metrics for a specific date range"""
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
                        if metric == 'AdrActCnt':
                            record['active_addresses'] = value
                        elif metric == 'AdrNewCnt':
                            record['new_addresses'] = value
                        elif metric == 'TxCnt':
                            record['tx_count'] = value
                        elif metric == 'TxVolUSD':
                            record['tx_volume_usd'] = value
                        elif metric == 'GasPriceUSD':
                            record['gas_fees_usd'] = value
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
        """Fetch all historical network activity data for a coin"""
        metrics = NETWORK_ACTIVITY_METRICS.get(coin, [])
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

        print(f"\n📊 Fetching {coin} network activity")
        print(f"   Metrics: {', '.join(metrics)}")
        print(f"   Range: {start_date.date()} → {end_date.date()}")

        all_data = []
        current_start = start_date
        chunk_days = NETWORK_CHUNK_DAYS

        while current_start < end_date:
            current_end = min(
                current_start + timedelta(days=chunk_days),
                end_date
            )

            print(f"   ⏳ {current_start.date()} → {current_end.date()}", end="")

            df_chunk = self.fetch_network_metrics(
                coin, metrics, current_start, current_end
            )

            if not df_chunk.empty:
                all_data.append(df_chunk)

            current_start = current_end + timedelta(days=1)

            # Rate limiting - CoinMetrics allows 10 requests per 6 seconds
            time.sleep(NETWORK_RATE_LIMIT)

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
        """Fetch network activity data for all configured coins"""
        print(f"\n{'='*60}")
        print(f"FETCH NETWORK ACTIVITY DAILY DATA")
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
        """Save network activity data for a single coin"""
        if df.empty:
            return

        filepath = get_networkactivity_file(coin)
        df.to_csv(filepath, index=False)

        print(f"\n💾 Saved {coin}: {filepath}")
        print(f"   Size: {os.path.getsize(filepath) / 1024:.1f} KB")
        print(f"   Rows: {len(df):,}")
        print(f"   Date range: {df['timestamp'].min()} → {df['timestamp'].max()}")

    def generate_summary(self):
        """Generate summary of collected network activity data"""
        print(f"\n{'='*60}")
        print(f"SUMMARY")
        print(f"{'='*60}")

        from pathlib import Path
        network_files = list(Path("data/raw/networkactivity").glob("*.csv"))

        print(f"Network activity files: {len(network_files)}")
        print(f"Location: {os.path.abspath('data/raw/networkactivity')}/")

        for file in network_files:
            df = pd.read_csv(file)
            print(f"  - {file.name}: {len(df):,} records")

            # Show latest values for each metric
            if not df.empty:
                latest = df.iloc[-1]
                print(f"    Latest ({latest['timestamp'].split()[0]}):")
                for col in df.columns:
                    if col != 'timestamp' and pd.notna(latest[col]):
                        if 'volume' in col.lower() or 'fees' in col.lower():
                            print(f"      {col}: ${latest[col]:,.2f}")
                        else:
                            print(f"      {col}: {latest[col]:,.0f}")

        print(f"\n✅ Network activity data collection complete!")

    def run(self):
        """Main execution method"""
        print("NETWORK ACTIVITY DAILY DATA COLLECTOR")
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
        print(f"   df_btc = pd.read_csv('data/raw/networkactivity/BTC_networkactivity.csv')")
        print(f"   df_eth = pd.read_csv('data/raw/networkactivity/ETH_networkactivity.csv')")
        print(f"   df_btc['timestamp'] = pd.to_datetime(df_btc['timestamp'])")
        print(f"   df_eth['timestamp'] = pd.to_datetime(df_eth['timestamp'])")
        print(f"\n🎉 Ready for analysis!\n")


if __name__ == "__main__":
    try:
        fetcher = CoinMetricsFetcher()
        fetcher.run()

    except KeyboardInterrupt:
        print("\n\n⚠️ Stopped (Ctrl+C)")
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()