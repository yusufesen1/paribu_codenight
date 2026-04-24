"""
test_explore_data.py — Veri Kalitesi Testleri
Coin verilerinin tutarlılığını ve kalitesini test eder.
"""
import pytest
import pandas as pd
from pathlib import Path

DATA_DIR = Path("C:/Users/yusuf/AppData/Local/Programs/Python/Python312/Lib/site-packages/cnlib/data")
COINS = ["kapcoin-usd_train", "metucoin-usd_train", "tamcoin-usd_train"]
REQUIRED_COLUMNS = {"Date", "Open", "High", "Low", "Close", "Volume"}


# ================================================================
# Veri Dosyası Testleri
# ================================================================

class TestDataFiles:
    """Parquet dosyalarının varlığını ve formatını test eder."""

    @pytest.mark.parametrize("coin", COINS)
    def test_data_file_exists(self, coin):
        """Her coin'in parquet dosyası mevcut olmalı."""
        path = DATA_DIR / f"{coin}.parquet"
        assert path.exists(), f"Dosya bulunamadı: {path}"

    @pytest.mark.parametrize("coin", COINS)
    def test_data_columns_present(self, coin):
        """OHLCV + Date sütunları bulunmalı."""
        df = pd.read_parquet(DATA_DIR / f"{coin}.parquet")
        missing = REQUIRED_COLUMNS - set(df.columns)
        assert not missing, f"{coin}: eksik sütunlar: {missing}"

    @pytest.mark.parametrize("coin", COINS)
    def test_data_no_nulls_in_ohlcv(self, coin):
        """OHLCV sütunlarında NaN olmamalı."""
        df = pd.read_parquet(DATA_DIR / f"{coin}.parquet")
        for col in ["Open", "High", "Low", "Close", "Volume"]:
            null_count = df[col].isna().sum()
            assert null_count == 0, f"{coin}.{col}: {null_count} adet NaN bulundu"


# ================================================================
# Veri Tutarlılık Testleri
# ================================================================

class TestDataConsistency:
    """Verilerin finansal tutarlılığını test eder."""

    def test_coin_data_equal_length(self):
        """Tüm coin verileri aynı uzunlukta olmalı."""
        lengths = {}
        for coin in COINS:
            df = pd.read_parquet(DATA_DIR / f"{coin}.parquet")
            lengths[coin] = len(df)
        unique_lengths = set(lengths.values())
        assert len(unique_lengths) == 1, \
            f"Coin verileri farklı uzunlukta: {lengths}"

    @pytest.mark.parametrize("coin", COINS)
    def test_prices_positive(self, coin):
        """Tüm Close fiyatları > 0 olmalı."""
        df = pd.read_parquet(DATA_DIR / f"{coin}.parquet")
        non_positive = (df["Close"] <= 0).sum()
        assert non_positive == 0, \
            f"{coin}: {non_positive} adet Close fiyatı <= 0"

    @pytest.mark.parametrize("coin", COINS)
    def test_ohlc_consistency(self, coin):
        """Her candle'da Low ≤ min(Open,Close) ve max(Open,Close) ≤ High olmalı."""
        df = pd.read_parquet(DATA_DIR / f"{coin}.parquet")

        # Low, Open ve Close'un altında olmalı
        low_violations = (df["Low"] > df[["Open", "Close"]].min(axis=1)).sum()
        assert low_violations == 0, \
            f"{coin}: {low_violations} candle'da Low > min(Open, Close)"

        # High, Open ve Close'un üstünde olmalı
        high_violations = (df["High"] < df[["Open", "Close"]].max(axis=1)).sum()
        assert high_violations == 0, \
            f"{coin}: {high_violations} candle'da High < max(Open, Close)"
