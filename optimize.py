"""
Daha agresif leverage ve kısa EMA kombinasyonları.
"""
from cnlib.base_strategy import BaseStrategy
from cnlib import backtest


class TrendLongStrategy(BaseStrategy):
    def __init__(self, fast=5, slow=15, trend=50, lev_kap=2, lev_metu=2, lev_tam=3):
        super().__init__()
        self.FAST = fast
        self.SLOW = slow
        self.TREND = trend
        self.WARMUP = trend + 5
        self.LEV = {
            "kapcoin-usd_train": lev_kap,
            "metucoin-usd_train": lev_metu,
            "tamcoin-usd_train": lev_tam,
        }

    def _signal(self, df):
        if len(df) < self.WARMUP:
            return 0
        closes = df["Close"]
        ef = closes.ewm(span=self.FAST, adjust=False).mean().iloc[-1]
        es = closes.ewm(span=self.SLOW, adjust=False).mean().iloc[-1]
        et = closes.ewm(span=self.TREND, adjust=False).mean().iloc[-1]
        return 1 if ef > es > et else 0

    def predict(self, data):
        sigs = {c: self._signal(df) for c, df in data.items()}
        active = [c for c, s in sigs.items() if s == 1]
        alloc = round(0.9 / len(active), 4) if active else 0.0
        return [
            {"coin": c, "signal": sigs[c], "allocation": alloc if sigs[c] == 1 else 0.0,
             "leverage": self.LEV[c] if sigs[c] == 1 else 1}
            for c in data
        ]


results = []

# Agresif kombinasyonlar
combos = [
    # (fast, slow, trend, kap, metu, tam)
    (5, 15, 50, 3, 3, 5),
    (5, 15, 50, 3, 3, 3),
    (5, 15, 50, 2, 2, 5),
    (5, 15, 50, 2, 2, 3),
    (3, 10, 40, 2, 2, 3),
    (3, 10, 40, 3, 3, 5),
    (3, 10, 40, 2, 2, 5),
    (4, 12, 45, 2, 2, 3),
    (4, 12, 45, 3, 3, 5),
    (5, 12, 40, 2, 2, 3),
    (5, 12, 40, 3, 3, 5),
    (5, 15, 50, 1, 1, 5),
    (5, 15, 50, 3, 3, 10),  # yüksek risk
]

for (fast, slow, trend, kap, metu, tam) in combos:
    s = TrendLongStrategy(fast, slow, trend, kap, metu, tam)
    try:
        r = backtest.run(strategy=s, initial_capital=3000.0, silent=True)
        results.append({
            "params": f"EMA({fast}/{slow}/{trend}) L({kap}/{metu}/{tam})",
            "return_pct": r.return_pct,
            "final": r.final_portfolio_value,
            "liquidations": r.total_liquidations,
            "trades": r.total_trades,
        })
    except Exception as e:
        print(f"Error: {e}")

results.sort(key=lambda x: x["return_pct"], reverse=True)
print(f"{'Parametreler':<35} {'return%':>10} {'final$':>14} {'liq':>4} {'trades':>7}")
print("-" * 75)
for r in results[:15]:
    print(f"{r['params']:<35} {r['return_pct']:>10.1f} {r['final']:>14,.0f} "
          f"{r['liquidations']:>4} {r['trades']:>7}")
