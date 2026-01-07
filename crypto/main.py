from backtester import Backtester
from strategies import BuyHoldStrategy, MAStrategy
from utils import fetch_ohlcv
import pandas as pd

if __name__ == "__main__":
    df = fetch_ohlcv("BTC-USD", 86400)

    strategies = {
        "BuyHold": BuyHoldStrategy(),
        "MA": MAStrategy(short=5, long=20)
    }

    all_metrics = {}

    for name, strat in strategies.items():
        bt = Backtester(df, strat, initial_cash=10000, fee=0.001)
        bt.run()
        bt.metrics()
        bt.export_trades()
        bt.plot_trades(show=False)  # 保存，不弹窗
        all_metrics[name] = bt.metrics_result

    df_metrics = pd.DataFrame(all_metrics).T
    print("\n=== Strategy Comparison ===")
    print(df_metrics)
