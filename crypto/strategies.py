import pandas as pd
import numpy as np


class Strategy:
    def generate_signals(self, df: pd.DataFrame) -> pd.Series:
        """Return pd.Series of signals (1=long, 0=cash)"""
        raise NotImplementedError
    
    def reason(self, df, i):
        return "N/A"  # 默认没有理由

class BuyHoldStrategy(Strategy):
    """基准：从头买入，一直持有"""
    def generate_signals(self, df):
        return pd.Series(1, index=df.index)  # 永远是 1（持仓）

    def reason(self, df, i):
        return "Buy & Hold baseline"

class MAStrategy(Strategy):
    def __init__(self, short=5, long=20):
        self.short = short
        self.long = long

    def generate_signals(self, df):
        ma_short = df["close"].rolling(self.short).mean()
        ma_long = df["close"].rolling(self.long).mean()
        return (ma_short > ma_long).astype(int)

    def reason(self, df, i):
        return f"MA{self.short}={df['close'].rolling(self.short).mean().iloc[i]:.2f}, " \
                f"MA{self.long}={df['close'].rolling(self.long).mean().iloc[i]:.2f}"


class RSIStrategy(Strategy):
    def __init__(self, period=14, low=30, high=70):
        self.period = period
        self.low = low
        self.high = high

    def generate_signals(self, df):
        delta = df["close"].diff()
        gain = np.where(delta > 0, delta, 0)
        loss = np.where(delta < 0, -delta, 0)

        avg_gain = pd.Series(gain).rolling(self.period).mean()
        avg_loss = pd.Series(loss).rolling(self.period).mean()

        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))

        signal = pd.Series(0, index=df.index)
        signal[rsi < self.low] = 1
        signal[rsi > self.high] = 0
        return signal.ffill().fillna(0)
