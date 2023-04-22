import datetime

def display_non_null_balances(wallet_balance):
    print("Balance:")
    for asset, total in wallet_balance.items():
        if total > 0.0001:
            print(f"{asset}: {total}")

def date_to_milliseconds(date_str):
    # Helper function to convert a date string (format: 'YYYY-MM-DD') to milliseconds
    epoch = datetime.datetime.utcfromtimestamp(0)
    date_obj = datetime.datetime.strptime(date_str, '%Y-%m-%d')
    return int((date_obj - epoch).total_seconds() * 1000)

def milliseconds_to_date(milliseconds):
    # Helper function to convert milliseconds to a date string (format: 'YYYY-MM-DD')
    date_obj = datetime.datetime.utcfromtimestamp(milliseconds / 1000)
    return date_obj.strftime('%Y-%m-%d')

def convert_time_seconds(time_str: str) -> int:
    time_units = {
        's': 1,
        'm': 60,
        'h': 3600,
        'd': 86400,
        'w': 604800,
        'M': 2592000,
        'y': 31536000
    }

    value, unit = int(time_str[:-1]), time_str[-1]

    if unit not in time_units:
        raise ValueError("Invalid time format. Please use s (seconds), m (minutes), h (hours), d (days), w (weeks), M (months), or y (years).")

    return value * time_units[unit]