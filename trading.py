import pandas as pd
import numpy as np
import time
from utils import date_to_milliseconds, milliseconds_to_date

def fetch_balance(exchange):
    balance = exchange.fetch_balance()
    return balance['total']

def get_fees(exchange, symbol):
    exchange.load_markets()
    market = exchange.market(symbol)
    taker_fee = market['taker']
    maker_fee = market['maker']
    return taker_fee, maker_fee

def calculate_hold_performance(historical_data, initial_balance=1000):
    start_price = historical_data.iloc[0]['close']
    end_price = historical_data.iloc[-1]['close']
    performance_ratio = end_price / start_price
    performance_percentage = (performance_ratio - 1) * 100
    return performance_percentage


def fetch_historical_data(exchange, symbol, timeframe, start_date, end_date):
    since = date_to_milliseconds(start_date)
    end_time_milliseconds = date_to_milliseconds(end_date)

    interval_milliseconds = exchange.parse_timeframe(timeframe) * 1000
    
    all_data = []

    while since < end_time_milliseconds:
        limit = (end_time_milliseconds - since) // interval_milliseconds
        ohlcv = exchange.fetch_ohlcv(symbol, timeframe, since, limit)
        
        # If there's no more data, break the loop
        if not ohlcv:
            break

        # Convert the data to a pandas DataFrame and append it to the all_data list
        df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        all_data.append(df)

        # Set the new since to the timestamp of the last data point + interval
        since = int(df.iloc[-1]['timestamp']) + exchange.parse_timeframe(timeframe) * 1000

        # Sleep to avoid hitting the API rate limit (if necessary)
        time.sleep(exchange.rateLimit / 1000)

    # Concatenate all the DataFrames in the all_data list
    historical_data = pd.concat(all_data, ignore_index=True)

    # Convert the timestamp column to datetime objects
    historical_data['timestamp'] = pd.to_datetime(historical_data['timestamp'], unit='ms')

    return historical_data

def execute_trade(exchange, symbol, side, amount, price):
    order_type = 'limit'  # or 'market' depending on your strategy
    params = {'test': True}  # Remove this line for real trades
    order = exchange.create_order(symbol, order_type, side, amount, price, params)
    return order

def backtest(strategy, data, taker_fee, initial_balance=1000):
    balance = initial_balance
    position = 0
    trade_history = []
    trade_report = {
        "strategy-name": strategy,
        "balance": 0,
        "performance": 0,
        "just-hold-performance": 0,
        "total_fees": 0
    }
    stop_loss = 0
    take_profit = 0

    for index, row in data.iterrows():
        signal = row['signal']

        if signal == 1:  # Buy
            trade_cost = balance / float(row['close'])
            fees = trade_cost * taker_fee
            position = (balance - fees) / float(row['close'])
            balance = 0
            trade_history.append(('buy', row['timestamp'], row['close'], None))
            trade_report["total_fees"] += fees
            stop_loss = row['stop_loss']
            take_profit = row['take_profit']

        elif position > 0:
            sell_reason = None

            if row['low'] <= stop_loss:
                sell_reason = 'stop_loss'
            elif row['high'] >= take_profit:
                sell_reason = 'take_profit'
            elif signal == -1:
                sell_reason = 'sell_signal'

            if sell_reason:
                trade_value = position * float(row['close'])
                fees = trade_value * taker_fee
                balance = trade_value - fees
                position = 0
                trade_history.append(('sell', row['timestamp'], row['close'], sell_reason))
                trade_report["total_fees"] += fees
                stop_loss = 0
                take_profit = 0

    if position > 0:
        balance = position * data.iloc[-1]['close']
    trade_report['balance'] = balance

    performance_ratio = balance / initial_balance
    performance_percentage = (performance_ratio - 1) * 100
    trade_report['performance'] = performance_percentage
    trade_report['just-hold-performance'] = calculate_hold_performance(data)

    df = pd.DataFrame(trade_history) 
    df.to_csv('trade_history.csv')

    return trade_report, trade_history

def ichimoku_cloud(data, conversion_line_period=9, base_line_period=26, lagging_span2_period=52, displacement=26):
    high_prices = data['high']
    low_prices = data['low']

    # Tenkan-sen (Conversion Line)
    conversion_line_high = high_prices.rolling(window=conversion_line_period).max()
    conversion_line_low = low_prices.rolling(window=conversion_line_period).min()
    conversion_line = (conversion_line_high + conversion_line_low) / 2

    # Kijun-sen (Base Line)
    base_line_high = high_prices.rolling(window=base_line_period).max()
    base_line_low = low_prices.rolling(window=base_line_period).min()
    base_line = (base_line_high + base_line_low) / 2

    # Senkou Span A (Leading Span A)
    leading_span_a = ((conversion_line + base_line) / 2).shift(displacement)

    # Senkou Span B (Leading Span B)
    leading_span_b_high = high_prices.rolling(window=lagging_span2_period).max()
    leading_span_b_low = low_prices.rolling(window=lagging_span2_period).min()
    leading_span_b = ((leading_span_b_high + leading_span_b_low) / 2).shift(displacement)

    # Chikou Span (Lagging Span)
    lagging_span = data['close'].shift(-displacement)

    return conversion_line, base_line, leading_span_a, leading_span_b, lagging_span


def run_trading_bot(symbol, strategy, interval, short_window=20, long_window=50, update_interval=60):
    while True:
        # Fetch the latest historical data
        start_time = f"{long_window + 1} {interval} ago UTC"
        historical_data = fetch_historical_data(symbol, interval, start_time)
        
        # Generate signals
        signal_data = strategy.generate_signals(historical_data, short_window, long_window)

        # Check the latest signal
        latest_signal = signal_data.iloc[-1]['signal']

        if latest_signal == 1:  # Buy
            print("Buy signal detected")
            # Check if you have enough balance to buy
            wallet_balance = fetch_balance()
            base_currency, quote_currency = symbol[:3], symbol[3:]
            quote_currency_balance = float(wallet_balance[quote_currency]['free'])
            if quote_currency_balance > 0:
                execute_trade(symbol, 'buy', quote_currency_balance)
                print("Executed buy order")

        elif latest_signal == -1:  # Sell
            print("Sell signal detected")
            # Check if you have enough balance to sell
            wallet_balance = fetch_balance()
            base_currency, quote_currency = symbol[:3], symbol[3:]
            base_currency_balance = float(wallet_balance[base_currency]['free'])
            if base_currency_balance > 0:
                execute_trade(symbol, 'sell', base_currency_balance)
                print("Executed sell order")

        # Wait for the specified update interval before fetching new data
        time.sleep(update_interval)
