"""
Test verisinin baslangic noktasini anlama:
Egitim verisi 2027-03-15'te bitiyor.
Test verisi buradan devam edecek.
Stratejimiz bu noktada ne durumda?
"""
import pandas as pd
import numpy as np
from pathlib import Path

DATA_DIR = Path("C:/Users/yusuf/AppData/Local/Programs/Python/Python312/Lib/site-packages/cnlib/data")

coins = {
    "kapcoin-usd_train":  pd.read_parquet(DATA_DIR / "kapcoin-usd_train.parquet"),
    "metucoin-usd_train": pd.read_parquet(DATA_DIR / "metucoin-usd_train.parquet"),
    "tamcoin-usd_train":  pd.read_parquet(DATA_DIR / "tamcoin-usd_train.parquet"),
}

FAST, SLOW, TREND = 5, 20, 50

print("=" * 60)
print("EGITIM VERISININ SON 90 GUNU — TEST BASLANGIC DURUMU")
print("=" * 60)

for name, df in coins.items():
    closes = df["Close"]
    coin_short = name.replace("-usd_train", "").upper()

    # EMA hesapla
    ema_f = closes.ewm(span=FAST,  adjust=False).mean()
    ema_s = closes.ewm(span=SLOW,  adjust=False).mean()
    ema_t = closes.ewm(span=TREND, adjust=False).mean()
    ema_cf = closes.ewm(span=5,  adjust=False).mean()
    ema_cs = closes.ewm(span=15, adjust=False).mean()

    # Son deger
    ef, es, et = ema_f.iloc[-1], ema_s.iloc[-1], ema_t.iloc[-1]
    cf, cs = ema_cf.iloc[-1], ema_cs.iloc[-1]
    price = closes.iloc[-1]
    peak  = closes.max()
    peak_date = df["Date"].iloc[closes.argmax()]

    # Sinyal
    if ef > es > et and cf > cs:
        signal = "LONG"
    elif ef < es < et and cf < cs:
        signal = "SHORT"
    else:
        signal = "NOTR"

    drawdown = (price - peak) / peak * 100

    print(f"\n{coin_short}")
    print(f"  Tepe noktasi : {peak:>10.2f}  ({str(peak_date)[:10]})")
    print(f"  Son fiyat    : {price:>10.2f}  ({str(df['Date'].iloc[-1])[:10]})")
    print(f"  Tepeden dusus: {drawdown:>+9.1f}%")
    print(f"  EMA(5) : {ef:>10.2f}  {'>' if ef > es else '<'} EMA(20): {es:>10.2f}  {'>' if es > et else '<'} EMA(50): {et:>10.2f}")
    print(f"  Conf(5): {cf:>10.2f}  {'>' if cf > cs else '<'} Conf(15): {cs:>10.2f}")
    print(f"  *** SINYAL: {signal} ***")

print()
print("=" * 60)
print("SON 6 AYLIK FIYAT HAREKETI OZETI")
print("=" * 60)

for name, df in coins.items():
    coin_short = name.replace("-usd_train", "").upper()
    last_180 = df.tail(180)
    print(f"\n{coin_short} — Son 6 ay:")
    for _, row in last_180[last_180["Date"].dt.month.isin([10, 11, 12]) & (last_180["Date"].dt.year == 2026)].groupby(last_180["Date"].dt.to_period("M")).last().iterrows():
        pass  # just showing monthly

    # Aylik kapanislar
    monthly = df.copy()
    monthly["Month"] = df["Date"].dt.to_period("M")
    monthly_close = monthly.groupby("Month")["Close"].last().tail(8)
    for period, close in monthly_close.items():
        print(f"  {period}: {close:>10.2f}")

print()
print("=" * 60)
print("TEST YILI BASLANGIÇ SENARYOSU")
print("=" * 60)
print()
print("Tum coinler PEAK'ten dususte:")
print("  kapcoin : 572 → 381  (-%33)")
print("  metucoin: 11387 → 5748 (-%49)")
print("  tamcoin : 8755 → 7474 (-%15)")
print()
print("EMA sinyalleri bize ne soyluyor:")
for name, df in coins.items():
    closes = df["Close"]
    coin_short = name.replace("-usd_train", "").upper()
    ema_f = closes.ewm(span=5,  adjust=False).mean().iloc[-1]
    ema_s = closes.ewm(span=20, adjust=False).mean().iloc[-1]
    ema_t = closes.ewm(span=50, adjust=False).mean().iloc[-1]
    cf = closes.ewm(span=5,  adjust=False).mean().iloc[-1]
    cs = closes.ewm(span=15, adjust=False).mean().iloc[-1]

    if ema_f > ema_s > ema_t and cf > cs:
        sig = "LONG — yukarı trend"
    elif ema_f < ema_s < ema_t and cf < cs:
        sig = "SHORT — asagi trend"
    else:
        sig = "NOTR — karasiz"
    print(f"  {coin_short}: {sig}")

print()
print("SONUC: Short sinyali olan stratejimiz doğru yonlendirilmis.")
print("Test yili buyuk ihtimalle dusus veya yatay hareketle basliyor.")
