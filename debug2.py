"""
Temel sorunun koku tespiti: Failed Opens neden oluyor?
portfolio.py'nin allocation mantigi ne?
"""
import pandas as pd
from pathlib import Path

# portfolio.py'nin allocation logicini simule et
print("=" * 60)
print("FAILED OPENS KOK NEDEN ANALIZI")
print("=" * 60)
print()
print("portfolio.py line 131:")
print("  allocated_capital = self.portfolio_value * allocation")
print("  if allocated_capital > self.cash: -> HATA")
print()
print("CASE ACIKLAMASI ise diyor ki:")
print("  allocation = 'Mevcut CASH'in ne kadari'")
print()
print("=> BUYUK CELISMA:")
print("   Case: allocation = cash * oran")
print("   Kod:  allocation = portfolio_value * oran")
print()
print("portfolio_value = cash + pozisyonlarin_degeri")
print("Pozisyonlar 5x leverage ile buyuyunce:")
print("  portfolio_value >> cash")
print("  portfolio_value * 0.28 >> cash")
print("  => FAILED OPEN")
print()

# Sayisal ornek
initial = 3000
alloc_per_coin = 0.28
lev = {"kap": 3, "metu": 3, "tam": 5}

# 3 coin acildiginda cash degisimi
cash = initial
positions = {}

# Coin A ac
needed = initial * alloc_per_coin
cash -= needed
positions["tam"] = {"capital": needed, "entry": 300, "lev": 5}
print(f"tam acildi: capital=${needed:.0f}, cash=${cash:.0f}, pv=${initial:.0f}")

needed = initial * alloc_per_coin
cash -= needed
positions["kap"] = {"capital": needed, "entry": 60, "lev": 3}
print(f"kap acildi: capital=${needed:.0f}, cash=${cash:.0f}, pv=${initial:.0f}")

needed = initial * alloc_per_coin
cash -= needed
positions["metu"] = {"capital": needed, "entry": 900, "lev": 3}
print(f"metu acildi: capital=${needed:.0f}, cash=${cash:.0f}, pv=${initial:.0f}")
print()

# Simdi fiyatlar 5x artti (gercekci: tamcoin 25x, biz 5x alalim)
price_mult = 5
tam_pnl = positions["tam"]["capital"] * 5 * (price_mult - 1)
kap_pnl = positions["kap"]["capital"] * 3 * (price_mult - 1)
metu_pnl = positions["metu"]["capital"] * 3 * (price_mult - 1)

pv = (cash
      + positions["tam"]["capital"] + tam_pnl
      + positions["kap"]["capital"] + kap_pnl
      + positions["metu"]["capital"] + metu_pnl)

print(f"Fiyatlar {price_mult}x artti:")
print(f"  PnL: tam=${tam_pnl:.0f}, kap=${kap_pnl:.0f}, metu=${metu_pnl:.0f}")
print(f"  Portfolio value: ${pv:,.0f}")
print(f"  Cash (DEGISMEDI): ${cash:.0f}")
print()

# Simdi coin A neutral olup tekrar aktif olursa
needed_new = pv * alloc_per_coin
print(f"Yeni open denenirse: portfolio_value * {alloc_per_coin} = ${needed_new:,.0f}")
print(f"Elimizde cash: ${cash:.0f}")
print(f"SONUC: {'BASARILI' if cash >= needed_new else 'FAILED OPEN!'}")
print()
print(f"Cash / PV orani: {cash/pv*100:.1f}%")
print(f"Gereken oran: {alloc_per_coin*100:.1f}%")
print()

print("=" * 60)
print("COZUM: PERIYODIK YENIDEN DENGELEME (REBALANCING)")
print("=" * 60)
print()
print("Her N candle'da signal=0 gonder → pozisyonlar kapanir")
print("Sonraki candle'da sinyal varsa yeniden ac")
print("Boylece cash = tam portfolio_value olur")
print("Yeni aciluslar dogru buyuklukle olur (portfolio ile orantili)")
print()
print("Maliyet: N candle'da 1 gun piyasa disinda")
print("Kazanim: Her yeniden acilusta portfolio buyuklugune gore pozisyon")
