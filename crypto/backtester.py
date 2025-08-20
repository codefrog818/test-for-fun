import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import logging
import os
from datetime import datetime


class Backtester:
    def __init__(self, df: pd.DataFrame, strategy, initial_cash=10000, fee=0.001, result_root="results"):
        self.df = df.copy()
        self.strategy = strategy
        self.initial_cash = initial_cash
        self.fee = fee
        self.result_df = None
        self.metrics_result = None
        self.trade_log = []

        # 每个回测一个独立目录
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.result_dir = os.path.join(result_root, f"{strategy.__class__.__name__}_{timestamp}")
        os.makedirs(self.result_dir, exist_ok=True)

        # log 文件路径
        log_file = os.path.join(self.result_dir, "backtest.log")

        # 设置 logger
        self.logger = logging.getLogger(strategy.__class__.__name__)
        self.logger.setLevel(logging.INFO)
        # 避免重复 handler
        if not self.logger.handlers:
            fh = logging.FileHandler(log_file, mode="w")
            sh = logging.StreamHandler()
            formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s")
            fh.setFormatter(formatter)
            sh.setFormatter(formatter)
            self.logger.addHandler(fh)
            self.logger.addHandler(sh)

        self.logger.info(f"Result directory: {self.result_dir}")

    def run(self):
        signals = self.strategy.generate_signals(self.df)
        cash, position = self.initial_cash, 0
        portfolio_values = []

        for i in range(len(self.df)):
            price = self.df.iloc[i]["close"]
            signal = signals.iloc[i]

            if signal == 1 and cash > 0:
                qty = (cash * (1 - self.fee)) / price
                self.trade_log.append({
                    "time": self.df.iloc[i]["time"],
                    "action": "BUY",
                    "price": price,
                    "qty": qty,
                    "reason": self.strategy.reason(self.df, i)
                })
                position = qty
                cash = 0

            elif signal == 0 and position > 0:
                cash = (position * price) * (1 - self.fee)
                self.trade_log.append({
                    "time": self.df.iloc[i]["time"],
                    "action": "SELL",
                    "price": price,
                    "qty": position,
                    "reason": self.strategy.reason(self.df, i)
                })
                position = 0

            portfolio_values.append(cash + position * price)

        self.df["portfolio"] = portfolio_values
        self.result_df = self.df
        return self.df

    def metrics(self):
        df = self.result_df
        df["returns"] = df["portfolio"].pct_change().fillna(0)

        total_return = df["portfolio"].iloc[-1] / df["portfolio"].iloc[0] - 1
        annualized_return = (1 + total_return) ** (365 / len(df)) - 1
        vol = df["returns"].std() * np.sqrt(252)
        sharpe = (annualized_return / vol) if vol > 0 else np.nan

        cum_max = df["portfolio"].cummax()
        drawdown = df["portfolio"] / cum_max - 1
        max_drawdown = drawdown.min()

        self.metrics_result = {
            "Total Return": total_return,
            "Annualized Return": annualized_return,
            "Annualized Volatility": vol,
            "Sharpe Ratio": sharpe,
            "Max Drawdown": max_drawdown
        }

        self.logger.info(f"=== {self.strategy.__class__.__name__} Metrics ===")
        for k, v in self.metrics_result.items():
            self.logger.info(f"{k}: {v:.4f}")

        return self.metrics_result

    def export_trades(self):
        filename = os.path.join(self.result_dir, "trades.csv")
        pd.DataFrame(self.trade_log).to_csv(filename, index=False)
        self.logger.info(f"Trade log saved to {filename}")

    def plot_trades(self, show_portfolio=True, show=False):
        fig, ax1 = plt.subplots(figsize=(12, 6))
        ax1.plot(self.df["time"], self.df["close"], label="Price", color="black", alpha=0.6)

        buys = [t for t in self.trade_log if t["action"] == "BUY"]
        sells = [t for t in self.trade_log if t["action"] == "SELL"]

        if buys:
            ax1.scatter([t["time"] for t in buys],
                        [t["price"] for t in buys],
                        marker="^", color="green", s=100, label="Buy")
        if sells:
            ax1.scatter([t["time"] for t in sells],
                        [t["price"] for t in sells],
                        marker="v", color="red", s=100, label="Sell")

        ax1.set_xlabel("Date")
        ax1.set_ylabel("Price (USD)")
        ax1.legend(loc="upper left")

        if show_portfolio:
            ax2 = ax1.twinx()
            ax2.plot(self.df["time"], self.df["portfolio"], label="Portfolio Value", color="blue")
            ax2.set_ylabel("Portfolio Value")
            ax2.legend(loc="upper right")

        plt.title(f"{self.strategy.__class__.__name__} Backtest")
        filename = os.path.join(self.result_dir, "plot.png")
        plt.savefig(filename)
        if show:
            plt.show()
        plt.close()
        self.logger.info(f"Plot saved to {filename}")
