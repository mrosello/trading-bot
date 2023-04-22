import numpy as np
import itertools
from trading import backtest
from strategies import MovingAverageStrategy, ROCStrategy

def define_search_space(strategy_class):
    if strategy_class == "MovingAverageStrategy":
        search_space = [
            range(5, 21),  # Short window periods from 5 to 20
            range(21, 51)  # Long window periods from 21 to 50
        ]
    elif strategy_class == "ROCStrategy":
        search_space = [
            range(5, 21),  # ROC periods from 5 to 20
            [x / 10.0 for x in range(10, 31)]  # ROC thresholds from 1.0 to 3.0 in increments of 0.1
        ]
    else:
        raise ValueError("Invalid strategy type. Please use a supported strategy.")
    return search_space

def optimize_strategy(strategy_class, historical_data, taker_fee, sl_tp_params=None):
    search_space = define_search_space(strategy_class)
    param_combinations = list(itertools.product(*search_space))

    best_params = None
    best_performance = -np.inf

    for params in param_combinations:
        if strategy_class == "MovingAverageStrategy":
            if sl_tp_params:
                extended_params = params + sl_tp_params
                strategy_instance = MovingAverageStrategy(extended_params)
            else:
                raise ValueError("Please provide stop_loss and take_profit parameters for MovingAverageStrategy.")
        elif strategy_class == "ROCStrategy":
            strategy_instance = ROCStrategy(params)
        else:
            raise ValueError("Invalid strategy type. Please use a supported strategy.")
        signal_data = strategy_instance.generate_signals(historical_data)

        trade_report, _ = backtest(strategy_class,signal_data, taker_fee)

        if trade_report["balance"] > best_performance:
            best_performance = trade_report["balance"]
            best_params = params
            optimized_strategy = strategy_instance

    print("Best parameters:", best_params)
    print("Best performance:", best_performance)

    return optimized_strategy
