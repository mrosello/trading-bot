import os
import numpy as np
import pandas as pd
import ccxt
from trading import fetch_historical_data, backtest, get_fees
from plot import plot_candlestick_chart
from strategies import MovingAverageStrategy, ROCStrategy
from optimization import optimize_strategy
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Configure Binance exchange
binance = ccxt.binance({
    'apiKey': os.getenv('BINANCE_API_KEY'),
    'secret': os.getenv('BINANCE_API_SECRET'),
})

symbol = 'ETHUSDT'
interval = '1h'
start_date = '2022-01-01'
end_date = '2022-01-23'

taker_fee, maker_fee = get_fees(binance, symbol)

# Fetch historical data
historical_data = fetch_historical_data(binance, symbol, interval, start_date, end_date)

df = pd.DataFrame(historical_data)
df.to_csv('historical_data.csv')

# Do you want to optimize your strategy parameters? It might take longer
optimize_parameters = False

# Choose the strategy you want to use
strategy = MovingAverageStrategy((11, 21, 0.02, 0.05))
# signal_data = strategy.generate_signals(historical_data)

if optimize_parameters:
    # Run the optimization process
    print("-----------------------")
    print("Running Optimization")
    print("-----------------------")
    optimized_strategy = optimize_strategy(strategy.__class__.__name__, historical_data, taker_fee, sl_tp_params=(0.03, 0.06))
    # Use the strategy with best parameters to generate signals
    signal_data = optimized_strategy.generate_signals(historical_data.copy())
else:
    # Run the backtest without optimization
    signal_data = strategy.generate_signals(historical_data.copy())

# Run backtesting and print results
print("-----------------------")
print("Running Final Backtest")
print("-----------------------")
trade_report, trade_history = backtest(strategy.__class__.__name__, signal_data, taker_fee)
print("Strategy:", trade_report["strategy-name"])
print("Pair:", symbol)
print("Start Time:", historical_data.iloc[0]['timestamp'])
print("End Time:", historical_data.iloc[-1]['timestamp'])
print("Final balance (USD):", trade_report["balance"])
print("Performance (%):", trade_report["performance"])
print("Just-hold Performance (%):", trade_report["just-hold-performance"])
print("Amount of trades", len(trade_history))
print("Total fees (USD)", trade_report["total_fees"])

plot_candlestick_chart(historical_data, trade_history, plot_ichimoku=False)
