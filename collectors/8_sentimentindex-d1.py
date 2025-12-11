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
    ensure_directories, get_sentimentindex_file, END_TIME
)

import requests
import pandas as pd
import time
import os
from datetime import datetime, timedelta
from utils.time_utils import calculate_collection_range, format_time_range_for_display, merge_dataframes


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
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='s', utc=True)

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


class SentimentIndexCollector:
    def __init__(self, end_time=None):
        self.fetcher = SentimentIndexFetcher()

        # Use config default if not provided
        if end_time is None:
            end_time = END_TIME

        self.end_time_config = end_time

    def fetch_and_save_alltime(self):
        """Fetch all historical Fear & Greed data and save to file"""
        print("\n📊 Sentiment Index Collector - Fear & Greed Index")
        print("=" * 50)

        file_path = get_sentimentindex_file()

        # Load existing data if file exists
        existing_df = None
        if os.path.exists(file_path):
            try:
                existing_df = pd.read_csv(file_path)
                existing_df['timestamp'] = pd.to_datetime(existing_df['timestamp'], utc=True)
                print(f"Found existing data: {len(existing_df)} records")
            except Exception as e:
                print(f"Warning: Could not load existing data: {e}")

        # Calculate time range based on config
        start_time, end_time = calculate_collection_range(
            self.end_time_config,
            data_type='sentimentindex',
            file_path=file_path
        )

        print(f"Time Range: {format_time_range_for_display(start_time, end_time)}")

        # For sentiment index, we always get all data from API
        df_all = self.fetcher.fetch_fear_greed_data(limit=0)

        if df_all.empty:
            print("❌ No data collected")
            return False

        print(f"Fetched {len(df_all)} total records from API")

        # If we have existing data, find what's new
        if existing_df is not None:
            # Find the latest timestamp in existing data
            latest_existing = existing_df['timestamp'].max()
            print(f"Latest existing data: {latest_existing}")

            # Only keep records newer than what we have
            df_new = df_all[df_all['timestamp'] > latest_existing]
            print(f"Found {len(df_new)} new records")

            # Merge existing with new
            df = merge_dataframes(existing_df, df_new)
            print(f"Merged with existing data. Total records: {len(df)}")

            # Apply END_TIME filter to merged dataset
            df = df[df['timestamp'] <= end_time]
            print(f"Applied END_TIME filter. Records after filtering: {len(df)}")
        else:
            # No existing data, keep all records up to END_TIME
            df = df_all[df_all['timestamp'] <= end_time]
            print(f"No existing data, keeping {len(df)} records up to END_TIME")

        # Save to file
        success = self.fetcher.save_data(df, file_path)

        if success:
            print(f"\n✅ Fear & Greed Index collection complete!")
            print(f"   📈 Total records: {len(df)}")
            print(f"   📅 Date range: {df['timestamp'].min().date()} → {df['timestamp'].max().date()}")
            print(f"   💾 File: {file_path}")

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

    collector = SentimentIndexCollector()

    try:
        success = collector.fetch_and_save_alltime()

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