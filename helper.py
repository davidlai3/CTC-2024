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

def parse_order(row) -> dict:
    """
        "date" : row["ts_recv"],
        "instrument" : row["instrument_id"],
        "bid_price" : row["bid_px_00"],
        "ask_price" : row["ask_px_00"],
        "bid_size" : row["bid_sz_00"],
        "ask_size" : row["ask_sz_00"],
    """
    data = {
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

