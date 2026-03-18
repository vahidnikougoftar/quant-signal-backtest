"""Project-wide configuration for the mean-reversion backtest."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from pathlib import Path


@dataclass(frozen=True)
class BacktestConfig:
    """Container for the parameters that drive the research pipeline."""

    ticker_a: str = "NVDA"
    ticker_b: str = "AMD"
    start_date: str = "2020-01-01"
    end_date: str = "2025-12-31"
    price_field: str = "Adj Close"
    signal_window: int = 20
    hedge_window: int = 60
    entry_zscore: float = 2.0
    exit_zscore: float = 0.5
    min_spread_vol: float = 1e-6
    transaction_cost_bps: float = 5.0
    short_borrow_cost_bps: float = 30.0
    annualization_factor: int = 252

    def __post_init__(self) -> None:
        """Validate parameter choices before the pipeline runs."""

        if self.ticker_a == self.ticker_b:
            raise ValueError("ticker_a and ticker_b must be different symbols.")
        if self.signal_window < 5:
            raise ValueError("signal_window must be at least 5 trading days.")
        if self.hedge_window < self.signal_window:
            raise ValueError("hedge_window must be greater than or equal to signal_window.")
        if self.entry_zscore <= self.exit_zscore:
            raise ValueError("entry_zscore must be greater than exit_zscore.")
        if self.exit_zscore < 0:
            raise ValueError("exit_zscore must be non-negative.")
        if self.transaction_cost_bps < 0 or self.short_borrow_cost_bps < 0:
            raise ValueError("Trading and borrow costs must be non-negative.")
        if self.annualization_factor <= 0:
            raise ValueError("annualization_factor must be positive.")

        start = date.fromisoformat(self.start_date)
        end = date.fromisoformat(self.end_date)
        if start >= end:
            raise ValueError("start_date must be earlier than end_date.")


BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
OUTPUT_DIR = BASE_DIR / "output"

CONFIG = BacktestConfig()
