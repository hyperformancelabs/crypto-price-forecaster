"""
Crypto Data Collector - OHLCV Data from Binance
Fetches H4 OHLCV data for BTC and ETH
"""

import sys
import os
import time
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import (
    COINS, BINANCE_BASE_URL, ensure_directories, get_ohlcv_file,
    END_TIME
)

import requests
import pandas as pd
import numpy as np
from utils.time_utils import calculate_collection_range, format_time_range_for_display, merge_dataframes
import os


class BinanceFetcher:
    def __init__(self):
        self.base_url = BINANCE_BASE_URL

    def get_earliest_timestamp(self, symbol):
        url = f"{self.base_url}/klines"
        params = {
            'symbol': f"{symbol}USDT",
            'interval': '1d',
            'limit': 1,
            'startTime': 0
        }
        try:
            response = requests.get(url, params=params)
            data = response.json()
            if data and len(data) > 0:
                return data[0][0]
        except:
            pass
        return None

    def fetch_h4_ohlcv(self, symbol, start_time_ms=None, end_time_ms=None):
        """
        Fetch H4 OHLCV data for given time range

        Args:
            symbol: Trading symbol (e.g., 'BTC', 'ETH')
            start_time_ms: Start time in milliseconds (optional)
            end_time_ms: End time in milliseconds (optional)

        Returns:
            List of OHLCV klines data
        """
        url = f"{self.base_url}/klines"
        all_klines = []

        # If no start time provided, get earliest available
        if start_time_ms is None:
            start_time_ms = self.get_earliest_timestamp(symbol)
            if start_time_ms is None:
                print(f"Cannot fetch data for {symbol}")
                return []

        # If no end time provided, use current time
        if end_time_ms is None:
            end_time_ms = int(time.time() * 1000)

        current_start = start_time_ms

        print(f"Fetching {symbol}/USDT H4 OHLCV from {start_time_ms} to {end_time_ms}")

        while current_start < end_time_ms:
            params = {
                'symbol': f"{symbol}USDT",
                'interval': '4h',
                'startTime': current_start,
                'endTime': end_time_ms,
                'limit': 1000
            }

            try:
                response = requests.get(url, params=params)
                data = response.json()

                if not data or len(data) == 0:
                    break

                all_klines.extend(data)
                current_start = data[-1][0] + 1
                time.sleep(0.1)

            except Exception as e:
                print(f"Error: {e}")
                time.sleep(1)
                continue

        print(f"{symbol}: {len(all_klines)} H4 candles")
        return all_klines

    def klines_to_df(self, klines):
        if not klines:
            return pd.DataFrame()

        df = pd.DataFrame(klines, columns=[
            'timestamp', 'open', 'high', 'low', 'close', 'volume',
            'close_time', 'quote_volume', 'trades', 'taker_buy_base',
            'taker_buy_quote', 'ignore'
        ])

        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')

        for col in ['open', 'high', 'low', 'close', 'volume', 'quote_volume']:
            df[col] = df[col].astype(float)

        df = df[['timestamp', 'open', 'high', 'low', 'close', 'volume',
                 'quote_volume', 'trades']]

        return df


class CryptoDataCollector:
    def __init__(self, end_time=None):
        self.binance = BinanceFetcher()

        # Use config default if not provided
        if end_time is None:
            end_time = END_TIME

        self.end_time_config = end_time
        ensure_directories()

    def collect_ohlcv_data(self):
        print("COLLECTING OHLCV DATA (BTC, ETH)")
        print(f"End Time: {self.end_time_config}\n")

        for coin in COINS:
            print(f"Fetching {coin} H4 OHLCV...")

            # Calculate time range
            file_path = get_ohlcv_file(coin)
            start_time, end_time = calculate_collection_range(
                self.end_time_config,
                data_type='ohlcv',
                coin=coin,
                file_path=file_path
            )

            print(f"Time Range: {format_time_range_for_display(start_time, end_time)}")

            # Convert to milliseconds for Binance API
            start_time_ms = int(start_time.timestamp() * 1000)
            end_time_ms = int(end_time.timestamp() * 1000)

            # Fetch data
            klines = self.binance.fetch_h4_ohlcv(coin, start_time_ms, end_time_ms)
            df = self.binance.klines_to_df(klines)

            if not df.empty:
                # Merge with existing data if file exists
                if os.path.exists(file_path):
                    try:
                        existing_df = pd.read_csv(file_path)
                        existing_df['timestamp'] = pd.to_datetime(existing_df['timestamp'])
                        df = merge_dataframes(existing_df, df)
                        print(f"Merged with existing data. Total records: {len(df)}")
                    except Exception as e:
                        print(f"Warning: Could not merge with existing data: {e}")

                # Save data
                df.to_csv(file_path, index=False)
                print(f"Saved: {file_path}")
                print(f"Range: {df['timestamp'].min()} → {df['timestamp'].max()}")
                print(f"Candles: {len(df)}\n")
            else:
                print(f"No data collected for {coin}\n")

            time.sleep(1)

    def generate_summary(self):
        print("SUMMARY")
        print("=" * 50)

        from pathlib import Path
        h4_files = list(Path("data/raw/ohlcv").glob("*.csv"))

        print(f"OHLCV files: {len(h4_files)}")
        print(f"Location: {os.path.abspath('data/raw/ohlcv')}/")

        for file in h4_files:
            print(f"  - {file.name}")

        print("\n✅ OHLCV data collection complete!")

    def run(self):
        print("CRYPTO DATA COLLECTOR - OHLCV")
        print("Starting data collection...")

        start_time = time.time()

        self.collect_ohlcv_data()
        self.generate_summary()

        elapsed = time.time() - start_time
        print(f"Time: {elapsed/60:.2f} minutes")


if __name__ == "__main__":
    try:
        collector = CryptoDataCollector()
        collector.run()

    except KeyboardInterrupt:
        print("\nStopped (Ctrl+C)")
    except Exception as e:
        print(f"\nERROR: {e}")
        import traceback
        traceback.print_exc()
