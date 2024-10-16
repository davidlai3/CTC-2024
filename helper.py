import numpy as np
from scipy.stats import norm
from datetime import datetime, timedelta

def update_hour(timestamp_str: str) -> str:
    timestamp_str = timestamp_str[:26] + 'Z'
    timestamp = datetime.strptime(timestamp_str, "%Y-%m-%dT%H:%M:%S.%fZ")
    
    # Get the minute part of the timestamp
    minutes = timestamp.minute
    

    # Determine if it should be rounded down to :00 or :30
    if minutes < 30:
        # Round down to :00
        rounded_timestamp = timestamp.replace(minute=30, second=0, microsecond=0)
        rounded_timestamp -= timedelta(hours=1)
        if (rounded_timestamp.hour >= 16):
            rounded_timestamp = rounded_timestamp.replace(hour=15)
    else:
        # Round down to :30
        rounded_timestamp = timestamp.replace(minute=30, second=0, microsecond=0)
        if (rounded_timestamp.hour >= 16):
            rounded_timestamp = rounded_timestamp.replace(hour=15)
    
    formatted_date = rounded_timestamp.strftime("%Y-%m-%d %H:%M:%S-05:00")
    return formatted_date

def time_difference_in_years(date1: str, date2: str) -> float:
    # Parse the first date formatted as "yyyy-mm-dd"
    date1_parsed = datetime.strptime(date1, "%Y-%m-%d")
    
    # Parse the second date formatted as "yymmdd"
    date2_parsed = datetime.strptime(date2, "%y%m%d")
    
    # Calculate the difference in days
    difference_in_days = abs((date1_parsed - date2_parsed).days)
    
    # Convert days to years
    difference_in_years = difference_in_days / 365.25  # Considering leap years
    
    return difference_in_years

def parse_order(row) -> dict:
    """
        "instrument" : row["instrument_id"],
        "bid_size" : row["bid_sz_00"],
        "ask_size" : row["ask_sz_00"],
    """
    data = {
        "bid_price" : row.bid_px_00,
        "ask_price" : row.ask_px_00,
        "date" : row.ts_recv,
        "expiry" : row.symbol[6:12],
        "order_type" : row.symbol[12],
        "strike" : float(row.symbol[13:18])
    }

    for i in range(3):
        data["strike"] += float(row.symbol[18+i]) / 10**(i+1)

    return data


if (__name__ == "__main__"):
    print(update_hour("2024-01-02T14:30:02.402838204Z"))
    print(update_hour("2024-01-02T12:39:02.402838204Z"))
    print(update_hour("2024-01-02T11:16:02.402838204Z"))
    print(update_hour("2024-01-12T14:59:02.402838204Z"))
    print(update_hour("2024-01-12T16:59:02.402838204Z"))
    print(update_hour("2024-01-12T17:19:02.402838204Z"))

    print(time_difference_in_years("2024-10-14", "221014"))
    print(time_difference_in_years("2024-01-01", "220101"))
    print(time_difference_in_years("2024-10-14", "190101"))
    print(time_difference_in_years("2000-12-31", "991231"))
    print(time_difference_in_years("2024-02-28", "220228"))
