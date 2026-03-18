"""Backtest engine for the market-neutral mean-reversion strategy."""

from __future__ import annotations

import numpy as np
import pandas as pd


def run_backtest(
    signal_frame: pd.DataFrame,
    transaction_cost_bps: float,
    short_borrow_cost_bps: float,
    annualization_factor: int,
) -> pd.DataFrame:
    """Simulate strategy performance with delayed execution and explicit frictions.

    Engineering rationale:
    A common backtesting error is to apply today's signal to today's return. In
    reality, the signal is only fully known after the observation period ends,
    so the strategy can only trade on the next bar. We therefore shift the
    position by one period before multiplying by returns.

    Financial rationale:
    A long spread position means:
    - long asset A
    - short asset B

    A short spread position means the opposite. The daily spread return is thus
    the relative performance difference between the two legs. Transaction costs
    are subtracted whenever the position changes.

    Args:
        signal_frame: DataFrame containing returns and desired positions.
        transaction_cost_bps: Cost in basis points charged per unit of turnover.
        short_borrow_cost_bps: Annualized borrow fee applied to short exposure.
        annualization_factor: Number of trading periods per year.

    Returns:
        DataFrame enriched with backtest columns such as lagged position,
        turnover, costs, strategy returns, equity curve, and drawdown.
    """

    results = signal_frame.copy()

    gross_exposure = 1.0 + results["hedge_ratio"].abs()
    results["target_weight_a"] = results["position"] / gross_exposure
    results["target_weight_b"] = (-results["position"] * results["hedge_ratio"]) / gross_exposure

    # Target weights are decided on day t and assumed to be active on day t+1.
    results["weight_a"] = results["target_weight_a"].shift(1).fillna(0.0)
    results["weight_b"] = results["target_weight_b"].shift(1).fillna(0.0)
    results["position_lagged"] = results["position"].shift(1).fillna(0.0)

    results["gross_exposure"] = results["weight_a"].abs() + results["weight_b"].abs()
    results["net_exposure"] = results["weight_a"] + results["weight_b"]
    results["short_exposure"] = np.clip(-results["weight_a"], a_min=0.0, a_max=None) + np.clip(
        -results["weight_b"], a_min=0.0, a_max=None
    )

    results["spread_return"] = results["weight_a"] * results["return_a"] + results["weight_b"] * results["return_b"]
    results["strategy_return_gross"] = results["spread_return"]

    previous_weight_a = results["weight_a"].shift(1).fillna(0.0)
    previous_weight_b = results["weight_b"].shift(1).fillna(0.0)
    results["turnover"] = (results["weight_a"] - previous_weight_a).abs() + (
        results["weight_b"] - previous_weight_b
    ).abs()
    results["transaction_cost"] = (transaction_cost_bps / 10_000.0) * results["turnover"]

    daily_borrow_cost = short_borrow_cost_bps / 10_000.0 / annualization_factor
    results["borrow_cost"] = daily_borrow_cost * results["short_exposure"]
    results["strategy_return_net"] = (
        results["strategy_return_gross"] - results["transaction_cost"] - results["borrow_cost"]
    )

    results["equity_curve"] = (1.0 + results["strategy_return_net"]).cumprod()
    results["running_max"] = results["equity_curve"].cummax()
    results["drawdown"] = results["equity_curve"] / results["running_max"] - 1.0

    return results
