from abc import ABC, abstractmethod
import numpy as np
import talib

class BaseStrategy(ABC):

    def __init__(self, params):
        self.params = params

    @abstractmethod
    def generate_signals(self, data):
        pass
class MovingAverageStrategy(BaseStrategy):
    
    def __init__(self, params):
        super().__init__(params)
        self.short_ma_period, self.long_ma_period, self.stop_loss, self.take_profit = self.params

    def generate_signals(self, data):
        data['short_mavg'] = data['close'].rolling(window=self.short_ma_period).mean()
        data['long_mavg'] = data['close'].rolling(window=self.long_ma_period).mean()
        data['signal'] = 0
        data['stop_loss'] = 0.0
        data['take_profit'] = 0.0

        buy_signals = (data['short_mavg'] > data['long_mavg']) & (data['short_mavg'].shift(1) <= data['long_mavg'].shift(1))
        sell_signals = (data['short_mavg'] < data['long_mavg']) & (data['short_mavg'].shift(1) >= data['long_mavg'].shift(1))

        data.loc[buy_signals, 'signal'] = 1
        data.loc[sell_signals, 'signal'] = -1

        # Define your desired stop-loss and take-profit percentages
        stop_loss_pct = 0.98  # 2% stop-loss
        take_profit_pct = 1.05  # 5% take-profit

        data.loc[buy_signals, 'stop_loss'] = data.loc[buy_signals, 'close'] * stop_loss_pct
        data.loc[buy_signals, 'take_profit'] = data.loc[buy_signals, 'close'] * take_profit_pct

        return data
    
class RSIStrategy(BaseStrategy):

    def __init__(self, params):
        super().__init__(params)
        self.rsi_period, self.overbought_threshold, self.oversold_threshold, self.stop_loss, self.take_profit = self.params

    def generate_signals(self, data):
        data['rsi'] = talib.RSI(data['close'], timeperiod=self.rsi_period)
        data['signal'] = 0
        data['stop_loss'] = 0.0
        data['take_profit'] = 0.0

        buy_signals = data['rsi'] < self.oversold_threshold
        sell_signals = data['rsi'] > self.overbought_threshold

        data.loc[buy_signals, 'signal'] = 1
        data.loc[sell_signals, 'signal'] = -1

        # Define your desired stop-loss and take-profit percentages
        stop_loss_pct = 1 - self.stop_loss  # stop_loss should be provided as a percentage, e.g., 0.02 for 2%
        take_profit_pct = 1 + self.take_profit  # take_profit should be provided as a percentage, e.g., 0.05 for 5%

        data.loc[buy_signals, 'stop_loss'] = data.loc[buy_signals, 'close'] * stop_loss_pct
        data.loc[buy_signals, 'take_profit'] = data.loc[buy_signals, 'close'] * take_profit_pct

        return data
    
class IchimokuStrategy(BaseStrategy):

    def __init__(self, params):
        super().__init__(params)
        self.stop_loss, self.take_profit = self.params

    def generate_signals(self, data):
        data['tenkan_sen'], data['kijun_sen'], data['senkou_span_a'], data['senkou_span_b'], data['chikou_span'] = talib.ICHIMOKU(
            data['high'], data['low'], tenkan_sen_period=9, kijun_sen_period=26, senkou_span_b_period=52, chikou_span_period=26)

        data['signal'] = 0
        data['stop_loss'] = 0.0
        data['take_profit'] = 0.0

        buy_signals = (data['close'].shift(-1) > data['senkou_span_a'].shift(-1)) & (data['close'].shift(-1) > data['senkou_span_b'].shift(-1))
        sell_signals = (data['close'].shift(-1) < data['senkou_span_a'].shift(-1)) & (data['close'].shift(-1) < data['senkou_span_b'].shift(-1))

        data.loc[buy_signals, 'signal'] = 1
        data.loc[sell_signals, 'signal'] = -1

        data.loc[buy_signals, 'stop_loss'] = data.loc[buy_signals, 'close'] * self.stop_loss
        data.loc[buy_signals, 'take_profit'] = data.loc[buy_signals, 'close'] * self.take_profit

        return data

class ROCStrategy(BaseStrategy):
    
    def __init__(self, params):
        super().__init__(params)
        self.roc_period, self.roc_threshold, self.stop_loss, self.take_profit = params

    def generate_signals(self, data):
        data['roc'] = data['close'].pct_change(periods=self.roc_period) * 100
        data['signal'] = 0

        buy_signals = (data['roc'] > self.roc_threshold) & (data['roc'].shift(1) <= self.roc_threshold)
        sell_signals = (data['roc'] < -self.roc_threshold) & (data['roc'].shift(1) >= -self.roc_threshold)

        data.loc[buy_signals, 'signal'] = 1
        data.loc[sell_signals, 'signal'] = -1

        return data
