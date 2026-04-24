import numpy as np
import pandas as pd
from cnlib.base_strategy import BaseStrategy
from cnlib import backtest


class TrendLongStrategy(BaseStrategy):
    """
    Long-only EMA trend strateji.
    - EMA(3/10/40) üçlü hizalamasıyla trend belirlenir
    - Short yok: downtrend veya düz piyasada nakde geçilir
    - tamcoin 5x, diğerleri 3x kaldıraç
    """

    FAST = 3
    SLOW = 10
    TREND = 40

    LEVERAGE = {
        "kapcoin-usd_train": 3,
        "metucoin-usd_train": 3,
        "tamcoin-usd_train": 5,
    }

    def _signal(self, df: pd.DataFrame) -> int:
        warmup = self.TREND + 5
        if len(df) < warmup:
            return 0
        closes = df["Close"]
        ef = closes.ewm(span=self.FAST, adjust=False).mean().iloc[-1]
        es = closes.ewm(span=self.SLOW, adjust=False).mean().iloc[-1]
        et = closes.ewm(span=self.TREND, adjust=False).mean().iloc[-1]
        return 1 if ef > es > et else 0

    def predict(self, data: dict) -> list[dict]:
        signals = {coin: self._signal(df) for coin, df in data.items()}

        active = [c for c, s in signals.items() if s == 1]
        n = len(active)
        alloc = round(0.9 / n, 4) if n > 0 else 0.0

        decisions = []
        for coin in data:
            sig = signals[coin]
            if sig == 1:
                decisions.append({
                    "coin": coin,
                    "signal": 1,
                    "allocation": alloc,
                    "leverage": self.LEVERAGE[coin],
                })
            else:
                decisions.append({
                    "coin": coin,
                    "signal": 0,
                    "allocation": 0.0,
                    "leverage": 1,
                })
        return decisions


if __name__ == "__main__":
    strategy = TrendLongStrategy()
    result = backtest.run(strategy=strategy, initial_capital=3000.0)
    result.print_summary()

    # Detaylı trade özeti
    print(f"\nIlk 5 trade:")
    for t in result.trade_history[:5]:
        print(f"  Candle {t['candle_index']:>4} | {str(t['timestamp'])[:10]} | "
              f"opened={t['opened']} closed={t['closed']} | portfolio=${t['portfolio_value']:,.0f}")
