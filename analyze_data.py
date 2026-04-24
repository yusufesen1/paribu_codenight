"""
Veri analizi: Coin davranislarini derinlemesine analiz et.
"""
import pandas as pd
import numpy as np
from pathlib import Path

data_dir = Path("C:/Users/yusuf/AppData/Local/Programs/Python/Python312/Lib/site-packages/cnlib/data")
coins = ["kapcoin-usd_train", "metucoin-usd_train", "tamcoin-usd_train"]

dfs = {}
for coin in coins:
    dfs[coin] = pd.read_parquet(data_dir / f"{coin}.parquet")

print("=" * 70)
print("DETAYLI VERI ANALIZI")
print("=" * 70)

for coin, df in dfs.items():
    closes = df["Close"]
    returns = closes.pct_change().dropna()
    highs = df["High"]
    lows = df["Low"]

    print(f"\n{'-' * 60}")
    print(f"  {coin}")
    print(f"{'-' * 60}")
    print(f"  Toplam gun: {len(df)}")
    print(f"  Close: start={closes.iloc[0]:.4f}, end={closes.iloc[-1]:.4f}")
    print(f"  Total return: {(closes.iloc[-1]/closes.iloc[0] - 1)*100:.1f}%")

    # Intraday volatilite (liquidation riski icin kritik)
    intraday_range = (highs - lows) / closes

    print(f"\n  VOLATILITE:")
    print(f"    Gunluk return std: {returns.std()*100:.3f}%")
    print(f"    Max tek gun dusus: {returns.min()*100:.2f}%")
    print(f"    Max tek gun artis: {returns.max()*100:.2f}%")
    print(f"    Avg intraday range (H-L)/C: {intraday_range.mean()*100:.2f}%")
    print(f"    Max intraday range: {intraday_range.max()*100:.2f}%")

    # Liquidation risk: prev_close'dan low'a max dusus
    low_vs_prev_close = ((lows - closes.shift(1)) / closes.shift(1)).dropna()

    print(f"\n  LIQUIDATION RISK (Low vs prev Close):")
    print(f"    Max dusus: {low_vs_prev_close.min()*100:.2f}%")
    print(f"    >10% drop gunleri: {(low_vs_prev_close < -0.10).sum()}")
    print(f"    >20% drop gunleri: {(low_vs_prev_close < -0.20).sum()}")
    print(f"    >33% drop gunleri: {(low_vs_prev_close < -0.33).sum()}")
    print(f"    >50% drop gunleri: {(low_vs_prev_close < -0.50).sum()}")

    # EMA trend analizi
    print(f"\n  EMA TREND ANALIZI:")
    for fast, slow, trend in [(3,10,40), (5,15,50), (5,12,40)]:
        ef = closes.ewm(span=fast, adjust=False).mean()
        es = closes.ewm(span=slow, adjust=False).mean()
        et = closes.ewm(span=trend, adjust=False).mean()
        bullish = ((ef > es) & (es > et)).sum()
        bearish = ((ef < es) & (es < et)).sum()
        neutral = len(df) - bullish - bearish
        print(f"    EMA({fast}/{slow}/{trend}): bull={bullish} bear={bearish} neutral={neutral}")

    # Drawdown analizi
    cummax = closes.cummax()
    drawdown = (closes - cummax) / cummax
    print(f"\n  DRAWDOWN:")
    print(f"    Max drawdown: {drawdown.min()*100:.1f}%")

# Korelasyon analizi
print(f"\n{'=' * 60}")
print("KORELASYON MATRISI (Gunluk Returns)")
print(f"{'=' * 60}")
ret_df = pd.DataFrame({
    coin: dfs[coin]["Close"].pct_change().dropna().values
    for coin in coins
}, index=range(len(dfs[coins[0]])-1))
print(ret_df.corr().round(3))

# Performans trendi
print(f"\n{'=' * 60}")
print("PERFORMANS TRENDI (Ceyrek pencereler)")
print(f"{'=' * 60}")
for coin, df in dfs.items():
    closes = df["Close"]
    total = len(closes)
    windows = [(0, total//4), (total//4, total//2), (total//2, 3*total//4), (3*total//4, total)]
    print(f"\n  {coin}:")
    for i, (s, e) in enumerate(windows):
        ret = (closes.iloc[e-1] / closes.iloc[s] - 1) * 100
        print(f"    Q{i+1} ({s}-{e}): {ret:+.1f}%")

# En buyuk tek gunluk dususler (top 5) — liquidation riski
print(f"\n{'=' * 60}")
print("EN BUYUK TEK GUNLUK DUSUSLER (Close-to-Low)")
print(f"{'=' * 60}")
for coin, df in dfs.items():
    closes = df["Close"]
    lows = df["Low"]
    drop = ((lows - closes.shift(1)) / closes.shift(1)).dropna()
    worst = drop.nsmallest(5)
    print(f"\n  {coin}:")
    for idx, val in worst.items():
        print(f"    Day {idx}: {val*100:.2f}%  (10x liq={abs(val)>0.10}, 5x liq={abs(val)>0.20}, 3x liq={abs(val)>0.33})")
