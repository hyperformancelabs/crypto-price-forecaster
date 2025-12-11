"""
Time utilities for crypto data collectors
Common functions for handling time ranges, incremental collection, and data processing
"""

import pandas as pd
from datetime import datetime, timedelta
from typing import Optional, Tuple
import os


def parse_end_time(end_time_config: str) -> datetime:
    """
    Parse end time configuration string to datetime object with hour-level support

    Args:
        end_time_config: 'now', 'YYYY-MM-DD', or 'YYYY-MM-DD HH:MM' format

    Returns:
        datetime: Parsed end time (timezone-aware for consistency)

    Raises:
        ValueError: If the format is invalid
    """
    import pytz

    if end_time_config.lower() == 'now':
        return datetime.now(pytz.UTC)
    else:
        # Try different time formats
        formats = [
            '%Y-%m-%d %H:%M',  # Date and hour:minute
            '%Y-%m-%d %H',     # Date and hour only
            '%Y-%m-%d'         # Date only
        ]

        for fmt in formats:
            try:
                # Parse as naive datetime, then make it timezone-aware
                parsed_time = datetime.strptime(end_time_config.strip(), fmt)
                return pytz.UTC.localize(parsed_time)
            except ValueError:
                continue

        raise ValueError(f"Invalid END_TIME format: {end_time_config}. Use 'now', 'YYYY-MM-DD', or 'YYYY-MM-DD HH:MM'")


def get_default_start_date(data_type: str, coin: Optional[str] = None) -> datetime:
    """
    Get default start date for all-time collection

    Args:
        data_type: Type of data being collected
        coin: Optional cryptocurrency symbol

    Returns:
        datetime: Default start date for the data type/coin (timezone-aware)
    """
    import pytz

    try:
        from config import DEFAULT_START_DATES

        if coin and coin in DEFAULT_START_DATES:
            return pytz.UTC.localize(DEFAULT_START_DATES[coin])
        elif data_type in DEFAULT_START_DATES:
            return pytz.UTC.localize(DEFAULT_START_DATES[data_type])
        else:
            return pytz.UTC.localize(datetime(2009, 1, 1))  # Fallback to Bitcoin inception
    except ImportError:
        return pytz.UTC.localize(datetime(2009, 1, 1))  # Fallback if config not available


def get_existing_data_range(file_path: str, timestamp_column: str = 'timestamp') -> Tuple[Optional[datetime], Optional[datetime]]:
    """
    Get the start and end timestamps from existing data file

    Args:
        file_path: Path to the CSV file
        timestamp_column: Name of the timestamp column

    Returns:
        Tuple of (min_timestamp, max_timestamp) or (None, None) if file doesn't exist/can't be read
    """
    import pytz

    if not os.path.exists(file_path):
        return None, None

    try:
        df = pd.read_csv(file_path)
        if df.empty or timestamp_column not in df.columns:
            return None, None

        df[timestamp_column] = pd.to_datetime(df[timestamp_column])
        min_timestamp = df[timestamp_column].min()
        max_timestamp = df[timestamp_column].max()

        # Ensure both timestamps are timezone-aware
        if min_timestamp.tzinfo is None:
            min_timestamp = pytz.UTC.localize(min_timestamp)
        if max_timestamp.tzinfo is None:
            max_timestamp = pytz.UTC.localize(max_timestamp)

        return min_timestamp, max_timestamp
    except Exception as e:
        print(f"Warning: Could not read existing data file {file_path}: {e}")
        return None, None


def calculate_collection_range(end_time_config: str,
                            data_type: str, coin: Optional[str] = None,
                            file_path: Optional[str] = None,
                            buffer_hours: int = 24) -> Tuple[datetime, datetime]:
    """
    Calculate start and end time for data collection based on configuration

    Args:
        end_time_config: 'now', 'YYYY-MM-DD', or 'YYYY-MM-DD HH:MM'
        data_type: Type of data being collected
        coin: Optional cryptocurrency symbol
        file_path: Path to existing data file (optional)
        buffer_hours: Hours to add as buffer before last timestamp when continuing from existing data

    Returns:
        Tuple of (start_time, end_time) for collection
    """
    end_time = parse_end_time(end_time_config)

    # Check for existing data to continue from
    if file_path and os.path.exists(file_path):
        _, last_timestamp = get_existing_data_range(file_path)
        if last_timestamp:
            # Continue from existing data with buffer to avoid gaps
            start_time = last_timestamp - timedelta(hours=buffer_hours)
            print(f"Continuing from existing data: {start_time} (last: {last_timestamp})")
        else:
            # No existing data, use default start date
            start_time = get_default_start_date(data_type, coin)
            print(f"No existing data, collecting from: {start_time}")
    else:
        # No file or doesn't exist, use default start date
        start_time = get_default_start_date(data_type, coin)
        print(f"Collecting from: {start_time}")

    # Ensure start_time is not after end_time
    if start_time > end_time:
        print(f"Warning: Start time {start_time} is after end time {end_time}")
        # Make fallback also timezone-aware
        import pytz
        fallback_start = end_time - timedelta(days=1)
        if fallback_start.tzinfo is None:
            fallback_start = pytz.UTC.localize(fallback_start)
        start_time = fallback_start

    return start_time, end_time


def remove_duplicates_and_sort(df: pd.DataFrame, timestamp_column: str = 'timestamp') -> pd.DataFrame:
    """
    Remove duplicate timestamps and sort by timestamp

    Args:
        df: DataFrame to process
        timestamp_column: Name of the timestamp column

    Returns:
        Processed DataFrame with unique timestamps sorted in ascending order
    """
    if df.empty:
        return df

    df = df.copy()
    df[timestamp_column] = pd.to_datetime(df[timestamp_column])
    df = df.drop_duplicates(subset=[timestamp_column], keep='last')
    df = df.sort_values(timestamp_column).reset_index(drop=True)
    return df


def merge_dataframes(existing_df: pd.DataFrame, new_df: pd.DataFrame,
                    timestamp_column: str = 'timestamp') -> pd.DataFrame:
    """
    Merge existing and new data, removing duplicates and maintaining sort order

    Args:
        existing_df: Existing DataFrame
        new_df: New DataFrame with additional data
        timestamp_column: Name of the timestamp column

    Returns:
        Merged DataFrame with unique timestamps
    """
    if existing_df.empty:
        return remove_duplicates_and_sort(new_df, timestamp_column)
    if new_df.empty:
        return remove_duplicates_and_sort(existing_df, timestamp_column)

    combined_df = pd.concat([existing_df, new_df], ignore_index=True)
    return remove_duplicates_and_sort(combined_df, timestamp_column)


def format_time_range_for_display(start_time: datetime, end_time: datetime) -> str:
    """
    Format time range for display purposes

    Args:
        start_time: Start datetime
        end_time: End datetime

    Returns:
        Formatted string representation of the time range
    """
    return f"{start_time.strftime('%Y-%m-%d %H:%M')} → {end_time.strftime('%Y-%m-%d %H:%M')}"


def validate_time_range(start_time: datetime, end_time: datetime) -> bool:
    """
    Validate that the time range is reasonable

    Args:
        start_time: Start datetime
        end_time: End datetime

    Returns:
        bool: True if the time range is valid
    """
    if start_time > end_time:
        return False

    # Check if the range is not too far in the future
    future_limit = datetime.now() + timedelta(days=1)
    if end_time > future_limit:
        print(f"Warning: End time {end_time} is in the future, capping to current time")
        return False

    return True


def adjust_for_api_limits(start_time: datetime, end_time: datetime, max_days: int = 365) -> Tuple[datetime, datetime]:
    """
    Adjust time range to respect API limits

    Args:
        start_time: Original start time
        end_time: Original end time
        max_days: Maximum number of days per API request

    Returns:
        Tuple of (adjusted_start_time, adjusted_end_time) for single API request
    """
    max_timedelta = timedelta(days=max_days)

    if end_time - start_time > max_timedelta:
        adjusted_end_time = start_time + max_timedelta
        return start_time, adjusted_end_time

    return start_time, end_time