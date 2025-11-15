"""
Sentiment Index Daily Data Collector from Alternative.me
Fetches historical Fear & Greed Index data with daily interval
Collects: Fear & Greed Index value and classification
No API key required - uses free public API
"""

import sys
import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import (
    SENTIMENTINDEX_API_BASE, SENTIMENTINDEX_RATE_LIMIT,
    ensure_directories, get_sentimentindex_file
)

import requests
import pandas as pd
import time
from datetime import datetime, timedelta


class SentimentIndexFetcher:
    def __init__(self):
        self.base_url = SENTIMENTINDEX_API_BASE
        ensure_directories()

    def fetch_fear_greed_data(self, limit=0):
        """Fetch Fear & Greed Index historical data"""
        url = f"{self.base_url}/"

        params = {
            'limit': limit,  # 0 = all available data
            'format': 'json'  # JSON format with timestamps
        }

        try:
            print(f"  📡 Fetching Fear & Greed Index data...")
            response = requests.get(url, params=params, timeout=60)

            if response.status_code != 200:
                print(f"  ❌ HTTP {response.status_code}")
                return pd.DataFrame()

            data = response.json()

            if 'data' not in data or not data['data']:
                print(f"  ❌ No data found")
                return pd.DataFrame()

            # Convert to DataFrame
            df = pd.DataFrame(data['data'])

            # Rename columns to match our format
            df = df.rename(columns={
                'timestamp': 'timestamp',
                'value': 'value',
                'value_classification': 'classification'
            })

            # Convert timestamp to datetime
            # Alternative.me provides timestamps as Unix timestamps (strings)
            # Handle both string and numeric formats
            df['timestamp'] = pd.to_numeric(df['timestamp'], errors='coerce')
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='s')

            # Convert value to numeric
            df['value'] = pd.to_numeric(df['value'], errors='coerce')

            # Reorder columns
            df = df[['timestamp', 'value', 'classification']]

            # Sort by timestamp
            df = df.sort_values('timestamp').reset_index(drop=True)

            print(f"  ✅ {len(df)} daily records")
            print(f"  📅 Date range: {df['timestamp'].min().date()} → {df['timestamp'].max().date()}")

            return df

        except Exception as e:
            print(f"  ❌ Error: {e}")
            return pd.DataFrame()

    def save_data(self, df, file_path):
        """Save DataFrame to CSV file"""
        try:
            df.to_csv(file_path, index=False)
            print(f"  💾 Saved to {file_path}")
            return True
        except Exception as e:
            print(f"  ❌ Save error: {e}")
            return False

    def fetch_and_save_alltime(self):
        """Fetch all historical Fear & Greed data and save to file"""
        print("\n📊 Sentiment Index Collector - Fear & Greed Index")
        print("=" * 50)

        # Fetch all historical data
        df = self.fetch_fear_greed_data(limit=0)

        if df.empty:
            print("❌ No data collected")
            return False

        # Save to file
        output_file = get_sentimentindex_file()
        success = self.save_data(df, output_file)

        if success:
            print(f"\n✅ Fear & Greed Index collection complete!")
            print(f"   📈 Total records: {len(df)}")
            print(f"   📅 Date range: {df['timestamp'].min().date()} → {df['timestamp'].max().date()}")
            print(f"   💾 File: {output_file}")

            # Show sample data
            print(f"\n📋 Sample data:")
            print(df.head())

            # Show classification distribution
            classification_counts = df['classification'].value_counts()
            print(f"\n📊 Classification distribution:")
            for classification, count in classification_counts.items():
                print(f"   {classification}: {count} days")

        return success


def main():
    """Main execution function"""
    print("\n" + "="*60)
    print("🎭 SENTIMENT INDEX DAILY DATA COLLECTOR - FEAR & GREED")
    print("="*60)

    fetcher = SentimentIndexFetcher()

    try:
        success = fetcher.fetch_and_save_alltime()

        if success:
            print(f"\n🎉 Sentiment Index data collection completed successfully!")
        else:
            print(f"\n❌ Sentiment Index data collection failed!")

    except KeyboardInterrupt:
        print(f"\n⏹️ Collection interrupted by user")
    except Exception as e:
        print(f"\n💥 Unexpected error: {e}")

    print("\n" + "="*60)


if __name__ == "__main__":
    main()