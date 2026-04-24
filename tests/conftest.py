"""
Ortak test fixture'ları — QA Test Suite
"""
import numpy as np
import pandas as pd
import pytest
from pathlib import Path

DATA_DIR = Path("C:/Users/yusuf/AppData/Local/Programs/Python/Python312/Lib/site-packages/cnlib/data")
COINS = ["kapcoin-usd_train", "metucoin-usd_train", "tamcoin-usd_train"]


def _make_ohlcv(closes: list[float]) -> pd.DataFrame:
    """Close listesinden sentetik OHLCV DataFrame üretir."""
    n = len(closes)
    closes = np.array(closes, dtype=float)
    return pd.DataFrame({
        "Date": pd.date_range("2024-01-01", periods=n, freq="D"),
        "Open": closes * 0.999,
        "High": closes * 1.01,
        "Low": closes * 0.99,
        "Close": closes,
        "Volume": np.random.randint(100, 10000, size=n),
    })


@pytest.fixture
def uptrend_df():
    """Güçlü yükseliş trendi — EMA(3) > EMA(10) > EMA(40) sağlamalı."""
    base = 100.0
    prices = [base * (1.005 ** i) for i in range(80)]
    return _make_ohlcv(prices)


@pytest.fixture
def downtrend_df():
    """Düşüş trendi — EMA hizalaması bozuk olmalı."""
    base = 200.0
    prices = [base * (0.995 ** i) for i in range(80)]
    return _make_ohlcv(prices)


@pytest.fixture
def flat_df():
    """Yatay piyasa — küçük salınımlar."""
    np.random.seed(42)
    prices = [100.0 + np.random.uniform(-0.5, 0.5) for _ in range(80)]
    return _make_ohlcv(prices)


@pytest.fixture
def short_df():
    """Warmup dönemi için yetersiz veri (< TREND + 5)."""
    prices = [100.0 + i * 0.5 for i in range(30)]
    return _make_ohlcv(prices)


@pytest.fixture
def real_coin_data():
    """Gerçek parquet verilerini yükler."""
    data = {}
    for coin in COINS:
        path = DATA_DIR / f"{coin}.parquet"
        if path.exists():
            data[coin] = pd.read_parquet(path)
    return data
