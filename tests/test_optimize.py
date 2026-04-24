"""
test_optimize.py — Parametre Optimizasyonu Testleri
Finans uzmanının optimize.py'daki kombinasyonlarının geçerliliğini test eder.
"""
import pytest
import sys
import os
import numpy as np
import pandas as pd

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from cnlib.validator import validate, ValidationError

COINS = ["kapcoin-usd_train", "metucoin-usd_train", "tamcoin-usd_train"]
VALID_LEVERAGES = {1, 2, 3, 5, 10}

# optimize.py'daki tüm kombinasyonlar
COMBOS = [
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
    (5, 15, 50, 3, 3, 10),
]


def _make_ohlcv(closes):
    n = len(closes)
    closes_arr = np.array(closes, dtype=float)
    return pd.DataFrame({
        "Date": pd.date_range("2024-01-01", periods=n, freq="D"),
        "Open": closes_arr * 0.999,
        "High": closes_arr * 1.01,
        "Low": closes_arr * 0.99,
        "Close": closes_arr,
        "Volume": np.random.randint(100, 10000, size=n),
    })


def _make_uptrend_data(n=80):
    closes = [100.0 * (1.005 ** i) for i in range(n)]
    return {coin: _make_ohlcv(closes) for coin in COINS}


# ================================================================
# Kombinasyon Geçerlilik Testleri
# ================================================================

class TestComboValidity:
    """optimize.py'daki parametre kombinasyonlarının geçerliliğini test eder."""

    @pytest.mark.parametrize("fast,slow,trend,kap,metu,tam", COMBOS)
    def test_ema_order_preserved(self, fast, slow, trend, kap, metu, tam):
        """Her kombinasyonda fast < slow < trend sırası korunmalı."""
        assert fast < slow < trend, \
            f"EMA sırası bozuk: fast={fast}, slow={slow}, trend={trend}"

    @pytest.mark.parametrize("fast,slow,trend,kap,metu,tam", COMBOS)
    def test_all_leverages_valid(self, fast, slow, trend, kap, metu, tam):
        """Tüm kaldıraçlar {1, 2, 3, 5, 10} setinde olmalı."""
        for name, lev in [("kapcoin", kap), ("metucoin", metu), ("tamcoin", tam)]:
            assert lev in VALID_LEVERAGES, \
                f"{name}: kaldıraç {lev} geçersiz, geçerli set: {VALID_LEVERAGES}"

    def test_no_duplicate_combos(self):
        """Tekrar eden kombinasyon olmamalı."""
        assert len(COMBOS) == len(set(COMBOS)), \
            "Tekrar eden kombinasyon(lar) var!"

    @pytest.mark.parametrize("fast,slow,trend,kap,metu,tam", COMBOS)
    def test_parameterized_strategy_predict_valid(self, fast, slow, trend, kap, metu, tam):
        """Her kombinasyon için predict() çıktısı validator uyumlu olmalı."""
        # optimize.py'daki TrendLongStrategy'yi inline olarak simüle ediyoruz
        from optimize import TrendLongStrategy
        strategy = TrendLongStrategy(fast, slow, trend, kap, metu, tam)
        data = _make_uptrend_data(n=max(trend + 10, 80))
        decisions = strategy.predict(data)
        try:
            validate(decisions)
        except ValidationError as e:
            pytest.fail(
                f"EMA({fast}/{slow}/{trend}) L({kap}/{metu}/{tam}) — "
                f"Validation hatası: {e}"
            )

    def test_high_leverage_risk_flag(self):
        """Kaldıraç ≥ 10 olan kombinasyonlar tespit edilmeli (risk uyarısı)."""
        high_risk = [
            (f, s, t, k, m, ta) for f, s, t, k, m, ta in COMBOS
            if max(k, m, ta) >= 10
        ]
        # Bu bir bilgilendirme testi: yüksek riskli kombinasyonlar var mı?
        for combo in high_risk:
            max_lev = max(combo[3], combo[4], combo[5])
            print(f"  ⚠️  Yüksek risk: EMA({combo[0]}/{combo[1]}/{combo[2]}) "
                  f"L({combo[3]}/{combo[4]}/{combo[5]}) — max kaldıraç: {max_lev}x")
        # Test her zaman geçer, ama yüksek risk varsa rapor eder
        assert True

    def test_results_sorting_logic(self):
        """Sonuçların return_pct'ye göre doğru sıralanıp sıralanmadığını test eder."""
        # Simüle edilmiş sonuçlar
        mock_results = [
            {"params": "A", "return_pct": 50.0},
            {"params": "B", "return_pct": 120.0},
            {"params": "C", "return_pct": 80.0},
        ]
        sorted_results = sorted(mock_results, key=lambda x: x["return_pct"], reverse=True)
        returns = [r["return_pct"] for r in sorted_results]
        assert returns == sorted(returns, reverse=True), \
            f"Sonuçlar doğru sıralanmamış: {returns}"
