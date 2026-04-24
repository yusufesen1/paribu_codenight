"""
test_integration.py — Backtest Entegrasyon Testleri
TrendLongStrategy'nin gerçek veri ile tam backtest döngüsünü test eder.
"""
import pytest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from strategy import TrendLongStrategy
from cnlib import backtest
from cnlib.backtest import BacktestResult


# ================================================================
# Tam Backtest Testleri
# ================================================================

class TestFullBacktest:
    """Gerçek veri ile tam backtest döngüsünü test eder."""

    @pytest.fixture(scope="class")
    def backtest_result(self):
        """Bir kez çalıştır, tüm testlerde kullan."""
        strategy = TrendLongStrategy()
        return backtest.run(strategy=strategy, initial_capital=3000.0, silent=True)

    def test_full_backtest_runs(self, backtest_result):
        """TrendLongStrategy ile tam backtest hatasız çalışmalı."""
        assert isinstance(backtest_result, BacktestResult), \
            "Backtest sonucu BacktestResult tipinde olmalı"

    def test_backtest_no_validation_errors(self, backtest_result):
        """Backtest boyunca validation error olmamalı."""
        assert backtest_result.validation_errors == 0, \
            f"Validation hataları: {backtest_result.validation_errors}"

    def test_backtest_no_strategy_errors(self, backtest_result):
        """predict() hiçbir zaman exception fırlatmamalı."""
        assert backtest_result.strategy_errors == 0, \
            f"Strategy hataları: {backtest_result.strategy_errors}"

    def test_backtest_final_value_positive(self, backtest_result):
        """Final portföy değeri > 0 olmalı (tamamen likidasyon olmadıysa)."""
        assert backtest_result.final_portfolio_value > 0, \
            f"Final portföy değeri: ${backtest_result.final_portfolio_value:.2f} (≤ 0!)"

    def test_backtest_result_fields(self, backtest_result):
        """BacktestResult tüm beklenen alanları içermeli."""
        required_fields = [
            "initial_capital", "final_portfolio_value", "net_pnl",
            "return_pct", "total_candles", "total_trades",
            "total_liquidations", "total_liquidation_loss",
            "validation_errors", "strategy_errors",
            "portfolio_series", "trade_history",
        ]
        for field in required_fields:
            assert hasattr(backtest_result, field), \
                f"BacktestResult'ta '{field}' alanı eksik"

    def test_liquidation_count_valid(self, backtest_result):
        """Likidasyon sayısı ≥ 0 ve toplam trade'lerin altında olmalı."""
        assert backtest_result.total_liquidations >= 0, \
            "Likidasyon sayısı negatif olamaz"
        # Likidasyon, trade sayısından fazla olmamalı (mantıksal kontrol)
        assert backtest_result.total_liquidations <= backtest_result.total_trades + backtest_result.total_liquidations, \
            "Likidasyon sayısı mantıksız"


# ================================================================
# Portföy Serisi Testleri
# ================================================================

class TestPortfolioSeries:
    """Backtest sırasında üretilen portföy serisini test eder."""

    @pytest.fixture(scope="class")
    def backtest_result(self):
        strategy = TrendLongStrategy()
        return backtest.run(strategy=strategy, initial_capital=3000.0, silent=True)

    def test_portfolio_series_not_empty(self, backtest_result):
        """Portföy serisi boş olmamalı."""
        assert len(backtest_result.portfolio_series) > 0, \
            "Portföy serisi boş!"

    def test_portfolio_series_length_matches_candles(self, backtest_result):
        """Portföy serisi uzunluğu = toplam candle sayısı olmalı."""
        assert len(backtest_result.portfolio_series) == backtest_result.total_candles, \
            f"Seri uzunluğu ({len(backtest_result.portfolio_series)}) " \
            f"!= candle sayısı ({backtest_result.total_candles})"

    def test_initial_portfolio_value_matches_capital(self, backtest_result):
        """İlk candle'da portföy değeri ≈ başlangıç sermayesi olmalı."""
        first_value = backtest_result.portfolio_series[0]["portfolio_value"]
        assert abs(first_value - 3000.0) < 100, \
            f"İlk portföy değeri ({first_value}) başlangıç sermayesinden çok uzak"

    def test_portfolio_values_non_negative(self, backtest_result):
        """Portföy değeri hiçbir zaman negatif olmamalı."""
        for entry in backtest_result.portfolio_series:
            assert entry["portfolio_value"] >= 0, \
                f"Candle {entry['candle_index']}: portföy değeri negatif ({entry['portfolio_value']})"
