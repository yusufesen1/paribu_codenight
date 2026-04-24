"""
test_strategy.py — TrendLongStrategy Birim Testleri
Finans uzmanının önerdiği EMA trend stratejisinin doğruluğunu test eder.
"""
import pytest
import pandas as pd
import numpy as np
import sys
import os

# Proje kök dizinini path'e ekle
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from strategy import TrendLongStrategy
from cnlib.validator import validate, ValidationError

COINS = ["kapcoin-usd_train", "metucoin-usd_train", "tamcoin-usd_train"]


def _make_ohlcv(closes: list[float]) -> pd.DataFrame:
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


def _make_data(closes_func, n=80):
    """3 coin için aynı fiyat serisi oluşturur."""
    closes = closes_func(n)
    return {coin: _make_ohlcv(closes) for coin in COINS}


def _uptrend(n):
    return [100.0 * (1.005 ** i) for i in range(n)]


def _downtrend(n):
    return [200.0 * (0.995 ** i) for i in range(n)]


def _flat(n):
    np.random.seed(42)
    return [100.0 + np.random.uniform(-0.3, 0.3) for _ in range(n)]


# ============================================================
# Sinyal Testleri
# ============================================================

class TestSignalLogic:
    """EMA sinyal üretim mantığını test eder."""

    def test_signal_uptrend_returns_1(self):
        """Güçlü uptrend'de EMA(3) > EMA(10) > EMA(40) → sinyal=1 olmalı."""
        strategy = TrendLongStrategy()
        df = _make_ohlcv(_uptrend(80))
        signal = strategy._signal(df)
        assert signal == 1, f"Uptrend'de sinyal 1 olmalıydı, {signal} döndü"

    def test_signal_downtrend_returns_0(self):
        """Downtrend'de EMA hizalaması bozulur → sinyal=0 (long-only, short yok)."""
        strategy = TrendLongStrategy()
        df = _make_ohlcv(_downtrend(80))
        signal = strategy._signal(df)
        assert signal == 0, f"Downtrend'de sinyal 0 olmalıydı, {signal} döndü"

    def test_signal_warmup_returns_0(self):
        """Yetersiz veri (< TREND + 5 bar) → sinyal=0 dönmeli."""
        strategy = TrendLongStrategy()
        df = _make_ohlcv(_uptrend(30))  # 30 < 40 + 5 = 45
        signal = strategy._signal(df)
        assert signal == 0, f"Warmup döneminde sinyal 0 olmalıydı, {signal} döndü"

    def test_signal_only_returns_0_or_1(self):
        """Long-only strateji: sinyal sadece 0 veya 1 olabilir (-1 olmamalı)."""
        strategy = TrendLongStrategy()
        for closes_fn in [_uptrend, _downtrend, _flat]:
            df = _make_ohlcv(closes_fn(80))
            signal = strategy._signal(df)
            assert signal in (0, 1), f"Sinyal sadece 0 veya 1 olmalı, {signal} döndü"


# ============================================================
# Predict Çıktısı Testleri
# ============================================================

class TestPredictOutput:
    """predict() metodunun çıktı formatını ve değerlerini test eder."""

    def test_predict_returns_all_coins(self):
        """predict() her zaman 3 coin döndürmeli."""
        strategy = TrendLongStrategy()
        data = _make_data(_uptrend)
        decisions = strategy.predict(data)
        returned_coins = {d["coin"] for d in decisions}
        assert returned_coins == set(COINS), f"Eksik coin: {set(COINS) - returned_coins}"

    def test_predict_all_active_allocation(self):
        """3 coin aktif → her birine 0.9/3 = 0.3 allocation verilmeli."""
        strategy = TrendLongStrategy()
        data = _make_data(_uptrend)
        decisions = strategy.predict(data)
        active = [d for d in decisions if d["signal"] == 1]
        if len(active) == 3:
            for d in active:
                assert abs(d["allocation"] - 0.3) < 0.001, \
                    f"{d['coin']}: allocation {d['allocation']}, beklenen 0.3"

    def test_predict_none_active_allocation(self):
        """Hiçbir coin aktif değil → tüm allocation=0.0."""
        strategy = TrendLongStrategy()
        data = _make_data(_downtrend)
        decisions = strategy.predict(data)
        for d in decisions:
            if d["signal"] == 0:
                assert d["allocation"] == 0.0, \
                    f"{d['coin']}: signal=0 ama allocation={d['allocation']}"

    def test_predict_output_validation_compatible(self):
        """predict() çıktısı cnlib validator'dan hatasız geçmeli."""
        strategy = TrendLongStrategy()
        for closes_fn in [_uptrend, _downtrend, _flat]:
            data = _make_data(closes_fn)
            decisions = strategy.predict(data)
            try:
                validate(decisions)
            except ValidationError as e:
                pytest.fail(f"Validation hatası ({closes_fn.__name__}): {e}")

    def test_total_allocation_never_exceeds_1(self):
        """Toplam allocation hiçbir zaman 1.0'ı geçmemeli."""
        strategy = TrendLongStrategy()
        for closes_fn in [_uptrend, _downtrend, _flat]:
            data = _make_data(closes_fn)
            decisions = strategy.predict(data)
            total = sum(d["allocation"] for d in decisions if d["signal"] != 0)
            assert total <= 1.0 + 1e-9, \
                f"Toplam allocation {total} > 1.0 ({closes_fn.__name__})"


# ============================================================
# Kaldıraç Testleri
# ============================================================

class TestLeverage:
    """Kaldıraç değerlerinin doğruluğunu test eder."""

    def test_leverage_values_correct(self):
        """tamcoin=5x, kapcoin=3x, metucoin=3x olmalı."""
        strategy = TrendLongStrategy()
        data = _make_data(_uptrend)
        decisions = strategy.predict(data)
        active = {d["coin"]: d["leverage"] for d in decisions if d["signal"] == 1}
        if "tamcoin-usd_train" in active:
            assert active["tamcoin-usd_train"] == 5, \
                f"tamcoin kaldıracı 5 olmalı, {active['tamcoin-usd_train']} döndü"
        if "kapcoin-usd_train" in active:
            assert active["kapcoin-usd_train"] == 3, \
                f"kapcoin kaldıracı 3 olmalı, {active['kapcoin-usd_train']} döndü"
        if "metucoin-usd_train" in active:
            assert active["metucoin-usd_train"] == 3, \
                f"metucoin kaldıracı 3 olmalı, {active['metucoin-usd_train']} döndü"

    def test_inactive_coin_leverage_is_1(self):
        """Sinyal=0 olan coin'de leverage=1 olmalı."""
        strategy = TrendLongStrategy()
        data = _make_data(_downtrend)
        decisions = strategy.predict(data)
        for d in decisions:
            if d["signal"] == 0:
                assert d["leverage"] == 1, \
                    f"{d['coin']}: signal=0 ama leverage={d['leverage']}, beklenen 1"

    def test_leverage_in_valid_set(self):
        """Tüm kaldıraç değerleri {1, 2, 3, 5, 10} setinde olmalı."""
        valid_leverages = {1, 2, 3, 5, 10}
        strategy = TrendLongStrategy()
        for closes_fn in [_uptrend, _downtrend, _flat]:
            data = _make_data(closes_fn)
            decisions = strategy.predict(data)
            for d in decisions:
                assert d["leverage"] in valid_leverages, \
                    f"{d['coin']}: geçersiz kaldıraç {d['leverage']}"
