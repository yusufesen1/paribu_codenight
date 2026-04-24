"""
FINAL SUBMISSION STRATEGY - Paribu CodeNight
=============================================
Tasarim kriterleri (egitim + test verisi dengesi):

1. Stop-Loss kaldirildi:
   Sabit ATR stop, EMA tersine donmeden once fiyat geri cekildiginde
   "stop cascade" yaratiyordu: kapat -> ayni EMA sinyaliyle yeniden ac
   -> tekrar kapat. EMA cikisi yeterli risk yonetimi sagliyor.

2. EMA(5/20/50) uclu hizalama:
   EMA(3/10/40)  -> egitim verisine asiri optimize, gec/yanlis cikis.
   EMA(20/50)    -> cok yavas, trend yakalamiyor, buy-and-hold altinda.
   EMA(5/20/50)  -> dengeyi sagliyor: az gurultu, erken giris.

3. Uniform 3x leverage (tamcoin dahil):
   Tamcoin'e 5x vermek gecmis 4 yilin performansini gelecege yayiyor.
   Test verisinde tamcoin farkli davranabilir. 3x tum coinler icin
   guveli ust sinir: %33 dususe kadar likidite yok.

4. Rebalancing (her 20 candle):
   portfolio.py allocation'i cash degil portfolio_value uzerinden hesaplar.
   Pozisyonlar leverage ile buyuyunce cash sabit, pv >> cash -> Failed Open.
   Rebalancing: cash = pv'ye esitlenir, sonraki aciluslar dogru olceklenir.
   Bu bir "trick" degil, compounding'in dogru calismasi icin gerekli.

5. %30 per coin, max %90 toplam:
   Yeterli maruz kalma, yeterli nakit tamponu.
   Rebalancing sonrasi 3 coin * %30 = %90 < %100 (gecerli).
"""
import pandas as pd
from cnlib.base_strategy import BaseStrategy
from cnlib import backtest


class FinalStrategy(BaseStrategy):
    """
    Uclu EMA trend-following, Long+Short, periyodik rebalancing.
    Egitim ve test verisi dengesi gozeterek tasarlandi.
    """

    FAST         = 5
    SLOW         = 20
    TREND        = 50
    CONFIRM_F    = 5
    CONFIRM_S    = 15
    MIN_CANDLES  = 55

    LEVERAGE     = 3           # Tum coinler icin esit; %33 dususse likidite yok
    ALLOC        = 0.30        # 3 * 0.30 = 0.90 < 1.0
    REBALANCE_EVERY = 20       # cash = pv periyodik sifirlama

    def _signal(self, closes: pd.Series) -> int:
        if len(closes) < self.MIN_CANDLES:
            return 0

        ef = closes.ewm(span=self.FAST,    adjust=False).mean().iloc[-1]
        es = closes.ewm(span=self.SLOW,    adjust=False).mean().iloc[-1]
        et = closes.ewm(span=self.TREND,   adjust=False).mean().iloc[-1]
        cf = closes.ewm(span=self.CONFIRM_F, adjust=False).mean().iloc[-1]
        cs = closes.ewm(span=self.CONFIRM_S, adjust=False).mean().iloc[-1]

        if ef > es > et and cf > cs:
            return 1
        if ef < es < et and cf < cs:
            return -1
        return 0

    def predict(self, data: dict) -> list[dict]:
        # Rebalancing: tum pozisyonlari kapat.
        # Bir sonraki candle'da yeniden acilusla cash = pv olur,
        # pozisyon buyuklugu portfolyo ile orantili olur (gercek compounding).
        if self.candle_index > 0 and self.candle_index % self.REBALANCE_EVERY == 0:
            return [
                {"coin": c, "signal": 0, "allocation": 0.0, "leverage": 1}
                for c in data
            ]

        signals = {c: self._signal(df["Close"]) for c, df in data.items()}

        # Kapama sinyallerini once isle: cash serbest kalsin, ardindan aciluslar gelsin
        decisions = []
        for coin in sorted(data, key=lambda c: (0 if signals[c] == 0 else 1)):
            sig = signals[coin]
            if sig != 0:
                decisions.append({
                    "coin":       coin,
                    "signal":     sig,
                    "allocation": self.ALLOC,
                    "leverage":   self.LEVERAGE,
                })
            else:
                decisions.append({
                    "coin":       coin,
                    "signal":     0,
                    "allocation": 0.0,
                    "leverage":   1,
                })
        return decisions


if __name__ == "__main__":
    strategy = FinalStrategy()
    result = backtest.run(strategy=strategy, initial_capital=3000.0)
    result.print_summary()

    pdf = result.portfolio_dataframe()
    q = len(pdf) // 4
    print("\nQUARTERLY BREAKDOWN:")
    for i in range(4):
        s, e = i * q, min((i + 1) * q - 1, len(pdf) - 1)
        sv = pdf.iloc[s]["portfolio_value"]
        ev = pdf.iloc[e]["portfolio_value"]
        print(f"  Q{i+1}: ${sv:>12,.0f} -> ${ev:>12,.0f}  ({(ev/sv-1)*100:>+8.1f}%)")
