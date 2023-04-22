import matplotlib.pyplot as plt
import mplfinance as mpf
import pandas as pd
import numpy as np
from trading import ichimoku_cloud 

def plot_candlestick_chart(historical_data, trade_history=None, plot_ichimoku=False):
    # Reformat historical_data for mplfinance
    historical_data = historical_data.set_index('timestamp')

    # Calculate Ichimoku Cloud components
    if plot_ichimoku:
        tenkan_sen, kijun_sen, senkou_span_a, senkou_span_b, chikou_span = ichimoku_cloud(historical_data)
        
        historical_data['senkou_span_a'] = senkou_span_a
        historical_data['senkou_span_b'] = senkou_span_b
        historical_data['chikou_span'] = chikou_span
        historical_data['tenkan_sen'] = tenkan_sen
        historical_data['kijun_sen'] = kijun_sen

        historical_data = historical_data.dropna(subset=['senkou_span_a', 'senkou_span_b', 'chikou_span', 'tenkan_sen', 'kijun_sen'])  # Drop rows containing NaN values only in the Ichimoku Cloud components
    
    additional_plots = []

    if plot_ichimoku:
        ichimoku_plots = [
            mpf.make_addplot(historical_data['senkou_span_a'], color='blue', panel=0),
            mpf.make_addplot(historical_data['senkou_span_b'], color='red', panel=0),
            mpf.make_addplot(historical_data['chikou_span'], color='green', panel=0),
            mpf.make_addplot(historical_data['tenkan_sen'], color='orange', panel=0),
            mpf.make_addplot(historical_data['kijun_sen'], color='purple', panel=0),
        ]
        additional_plots.extend(ichimoku_plots)
    
    if trade_history:
        historical_data['buy'] = np.nan
        historical_data['sell_signal'] = np.nan
        historical_data['stop_loss'] = np.nan
        historical_data['take_profit'] = np.nan

        for action, timestamp, price, reason in trade_history:
            if timestamp in historical_data.index:
                if action == 'buy':
                    historical_data.loc[timestamp, 'buy'] = price
                elif action == 'sell':
                    historical_data.loc[timestamp, reason] = price

        additional_plots.extend([mpf.make_addplot(historical_data['buy'], type='scatter', marker='^', markersize=100, color='g', panel=0),
                                mpf.make_addplot(historical_data['sell_signal'], type='scatter', marker='v', markersize=100, color='r', panel=0),
                                mpf.make_addplot(historical_data['stop_loss'], type='scatter', marker='v', markersize=100, color='purple', panel=0),
                                mpf.make_addplot(historical_data['take_profit'], type='scatter', marker='v', markersize=100, color='purple', panel=0)])
        
    df = pd.DataFrame(additional_plots)
    df.to_csv('additional_plots.csv')
    df = pd.DataFrame(historical_data)
    df.to_csv('historical_data.csv')

    if historical_data.empty:
        print("No data to plot.")
        return
    
    if additional_plots == []:
        mpf.plot(historical_data, type='candle', style='charles', title='Candlestick Chart', ylabel='Price', figsize=(12, 6))
    else:
        mpf.plot(historical_data, type='candle', style='charles', title='Candlestick Chart', ylabel='Price', figsize=(12, 6), addplot=additional_plots)