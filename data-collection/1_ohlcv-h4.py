"""
Crypto Data Collector - OHLCV Data from Binance
Fetches H4 OHLCV data for BTC and ETH
"""

import sys
import os
import time
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import (
    COINS, BINANCE_BASE_URL, ensure_directories, get_ohlcv_file
)

import requests
import pandas as pd
import numpy as np


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

    def fetch_h4_ohlcv(self, symbol):
        url = f"{self.base_url}/klines"
        all_klines = []

        start_time = self.get_earliest_timestamp(symbol)
        if start_time is None:
            print(f"Cannot fetch data for {symbol}")
            return []

        end_time = int(time.time() * 1000)
        current_start = start_time

        print(f"Fetching {symbol}/USDT H4 OHLCV...")

        while current_start < end_time:
            params = {
                'symbol': f"{symbol}USDT",
                'interval': '4h',
                'startTime': current_start,
                'endTime': end_time,
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

        df['log_returns'] = np.log(df['close'] / df['close'].shift(1))
        df['log_returns'] = df['log_returns'].fillna(0)

        df = df[['timestamp', 'open', 'high', 'low', 'close', 'volume',
                 'quote_volume', 'log_returns', 'trades']]

        return df


class CryptoDataCollector:
    def __init__(self):
        self.binance = BinanceFetcher()
        ensure_directories()

    def collect_ohlcv_data(self):
        print("COLLECTING OHLCV DATA (BTC, ETH)\n")

        for coin in COINS:
            print(f"Fetching {coin} H4 OHLCV...")
            klines = self.binance.fetch_h4_ohlcv(coin)
            df = self.binance.klines_to_df(klines)

            if not df.empty:
                filename = get_ohlcv_file(coin)
                df.to_csv(filename, index=False)
                print(f"Saved: {filename}")
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
