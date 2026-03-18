"""Performance evaluation utilities for the backtest."""

from __future__ import annotations

import numpy as np
import pandas as pd


def compute_performance_metrics(
    strategy_returns: pd.Series,
    turnover: pd.Series,
    positions: pd.Series,
    annualization_factor: int = 252,
) -> pd.DataFrame:
    """Compute standard performance metrics from a strategy return series.

    Args:
        strategy_returns: Daily net returns from the strategy.
        turnover: Daily portfolio turnover.
        positions: Daily executed position state.
        annualization_factor: Number of trading periods per year.

    Returns:
        Single-row DataFrame containing the most common quant performance
        statistics used in an initial research review.

    Raises:
        ValueError: If the return series is empty after dropping missing values.
    """

    clean_returns = strategy_returns.dropna()
    if clean_returns.empty:
        raise ValueError("Strategy return series is empty; cannot compute metrics.")
    aligned_turnover = turnover.reindex(clean_returns.index).fillna(0.0)
    aligned_positions = positions.reindex(clean_returns.index).fillna(0.0)

    equity_curve = (1.0 + clean_returns).cumprod()
    total_return = equity_curve.iloc[-1] - 1.0

    num_periods = len(clean_returns)
    annualized_return = equity_curve.iloc[-1] ** (annualization_factor / num_periods) - 1.0

    daily_mean = clean_returns.mean()
    daily_std = clean_returns.std()
    annualized_volatility = daily_std * np.sqrt(annualization_factor)
    sharpe_ratio = np.nan
    if np.isfinite(daily_std) and not np.isclose(daily_std, 0.0):
        sharpe_ratio = (daily_mean / daily_std) * np.sqrt(annualization_factor)

    running_max = equity_curve.cummax()
    drawdown = equity_curve / running_max - 1.0
    max_drawdown = drawdown.min()

    hit_rate = (clean_returns > 0).mean()
    downside_std = clean_returns[clean_returns < 0].std()
    sortino_ratio = np.nan
    if np.isfinite(downside_std) and not np.isclose(downside_std, 0.0):
        sortino_ratio = (daily_mean / downside_std) * np.sqrt(annualization_factor)

    calmar_ratio = np.nan
    if max_drawdown < 0:
        calmar_ratio = annualized_return / abs(max_drawdown)

    active_fraction = (aligned_positions != 0).mean()
    turnover_mean = aligned_turnover.mean()
    trade_count = int((aligned_positions.diff().fillna(aligned_positions).abs() > 0).sum())

    metrics = pd.DataFrame(
        [
            {
                "total_return": total_return,
                "annualized_return": annualized_return,
                "annualized_volatility": annualized_volatility,
                "sharpe_ratio": sharpe_ratio,
                "sortino_ratio": sortino_ratio,
                "calmar_ratio": calmar_ratio,
                "max_drawdown": max_drawdown,
                "hit_rate": hit_rate,
                "avg_daily_turnover": turnover_mean,
                "active_fraction": active_fraction,
                "trade_count": trade_count,
            }
        ]
    )

    return metrics
