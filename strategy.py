"""
FINAL SUBMISSION STRATEGY - Paribu CodeNight
=============================================
Config: EMA(5/20/50) + Onay(5/15), 3x leverage, %70 allocation
Secim nedeni: En yuksek consistency score (296), 0 liquidation,
tum ceyreklerde pozitif, en guclu Q2 performansi.
"""
import numpy as np
import pandas as pd
from cnlib.base_strategy import BaseStrategy
from cnlib import backtest


class RobustStrategy(BaseStrategy):
    """
    Cift katmanli EMA trend-following strateji.
    Long/Short + adaptif leverage + volatilite filtresi.

    Neden bu parametreler:
    - EMA(5/20/50): Ne cok hizli (noise) ne cok yavas (gec kalma)
    - 3x base leverage: %33 dususe kadar liquidation yok (data'daki max ~%20)
    - %70 allocation: Tamamen all-in degil, ama yeterli risk
    - Short sinyal: Bearish donemlerden de kazanc (Q2/Q4 pozitif yapiyor)
    - Volatilite filtresi: Tehlikeli donemde leverage dusur
    """

    COIN_WEIGHT = {
        "kapcoin-usd_train": 1.0,
        "metucoin-usd_train": 1.0,
        "tamcoin-usd_train": 1.2,
    }

    def __init__(self):
        super().__init__()
        # Ana trend EMA'lari
        self.FAST = 5
        self.SLOW = 20
        self.TREND_SPAN = 50

        # Onay katmani EMA'lari
        self.CONFIRM_FAST = 5
        self.CONFIRM_SLOW = 15

        # Risk parametreleri
        self.BASE_LEV = 3
        self.VOL_WINDOW = 30
        self.VOL_HIGH = 0.035
        self.TOTAL_ALLOC = 0.70
        self.USE_SHORT = True
        self.MIN_TREND_DAYS = 55  # TREND_SPAN + 5

    def _ema_signal(self, closes):
        """
        Cift katmanli EMA sinyal sistemi.
        Ana trend (5/20/50) + Momentum onay (5/15).
        """
        if len(closes) < self.MIN_TREND_DAYS:
            return 0, 0.0

        ef = closes.ewm(span=self.FAST, adjust=False).mean().iloc[-1]
        es = closes.ewm(span=self.SLOW, adjust=False).mean().iloc[-1]
        et = closes.ewm(span=self.TREND_SPAN, adjust=False).mean().iloc[-1]
        cf = closes.ewm(span=self.CONFIRM_FAST, adjust=False).mean().iloc[-1]
        cs = closes.ewm(span=self.CONFIRM_SLOW, adjust=False).mean().iloc[-1]

        price = closes.iloc[-1]
        spread = abs(ef - et) / price

        if ef > es > et and cf > cs:
            return 1, spread
        elif ef > es > et:
            return 1, spread * 0.5
        elif ef < es < et and cf < cs and self.USE_SHORT:
            return -1, spread
        elif ef < es < et and self.USE_SHORT:
            return -1, spread * 0.5
        else:
            return 0, 0.0

    def _get_volatility(self, closes):
        if len(closes) < self.VOL_WINDOW + 2:
            return 0.02
        return closes.pct_change().dropna().tail(self.VOL_WINDOW).std()

    def _adaptive_leverage(self, vol, confidence):
        if vol > self.VOL_HIGH * 1.5:
            lev = 1
        elif vol > self.VOL_HIGH:
            lev = 2
        else:
            lev = self.BASE_LEV
        if confidence < 0.02:
            lev = min(lev, 2)
        valid = [1, 2, 3, 5, 10]
        return min(valid, key=lambda x: abs(x - lev))

    def predict(self, data):
        signals = {}
        leverages = {}
        confidences = {}

        for coin, df in data.items():
            closes = df["Close"]
            sig, conf = self._ema_signal(closes)
            vol = self._get_volatility(closes)
            lev = self._adaptive_leverage(vol, conf)
            signals[coin] = sig
            leverages[coin] = lev
            confidences[coin] = conf

        # Allocation: aktif coinlere agirlikli dagitim
        active = [c for c, s in signals.items() if s != 0]
        if not active:
            allocs = {c: 0.0 for c in data}
        else:
            weights = {c: self.COIN_WEIGHT.get(c, 1.0) * (confidences[c] + 0.01) for c in active}
            total_w = sum(weights.values())
            allocs = {c: round(self.TOTAL_ALLOC * weights[c] / total_w, 4) if c in active else 0.0 for c in data}

        # Decisions: ONCE close sinyallerini koy (cash serbest kalsin)
        decisions = []
        coins_sorted = sorted(data.keys(), key=lambda c: (0 if signals[c] == 0 else 1))

        for coin in coins_sorted:
            sig = signals[coin]
            decisions.append({
                "coin": coin,
                "signal": sig,
                "allocation": allocs[coin] if sig != 0 else 0.0,
                "leverage": leverages[coin] if sig != 0 else 1,
            })

        return decisions


if __name__ == "__main__":
    strategy = RobustStrategy()
    result = backtest.run(strategy=strategy, initial_capital=3000.0)
    result.print_summary()

    # Quarterly breakdown
    pdf = result.portfolio_dataframe()
    total = len(pdf)
    q_size = total // 4
    print("\nQUARTERLY BREAKDOWN:")
    for q in range(4):
        s_idx = q * q_size
        e_idx = min((q+1) * q_size - 1, total - 1)
        s_val = pdf.iloc[s_idx]["portfolio_value"]
        e_val = pdf.iloc[e_idx]["portfolio_value"]
        q_ret = (e_val / s_val - 1) * 100
        print(f"  Q{q+1}: ${s_val:>12,.0f} -> ${e_val:>12,.0f}  ({q_ret:>+7.1f}%)")
