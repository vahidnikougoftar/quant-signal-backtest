"""Signal engineering for the market-neutral mean-reversion strategy."""

from __future__ import annotations

import numpy as np
import pandas as pd


def compute_spread_and_zscore(
    prices: pd.DataFrame,
    ticker_a: str,
    ticker_b: str,
    signal_window: int,
    hedge_window: int,
    min_spread_vol: float = 1e-6,
) -> pd.DataFrame:
    """Construct a rolling-hedge spread and standardized z-score series.

    Financial intuition:
    The strategy trades relative mispricing rather than outright market
    direction. By looking at the difference between two related assets, we aim
    to isolate the idiosyncratic divergence between them and reduce the impact
    of broad market moves.

    Statistical intuition:
    A raw spread is difficult to compare across time because its scale can vary.
    Standardizing by a rolling mean and rolling standard deviation converts the
    spread into a z-score, which measures how unusual the current deviation is
    relative to recent history.

    Args:
        prices: Clean, aligned price DataFrame for the pair.
        ticker_a: First asset in the spread.
        ticker_b: Second asset in the spread.
        signal_window: Window length used to standardize the spread.
        hedge_window: Window length used to estimate the rolling hedge ratio.
        min_spread_vol: Lower bound applied to the rolling spread volatility.

    Returns:
        DataFrame containing prices, spread, rolling statistics, z-score, and
        leg returns.

    Raises:
        ValueError: If there are insufficient rows after rolling-window cleanup
            or if the rolling standard deviation collapses to zero.
    """

    frame = prices.copy()

    # Log prices are common in quantitative research because differences in logs
    # approximate continuously compounded relative moves and behave more
    # naturally across assets with different absolute price levels.
    frame[f"log_{ticker_a}"] = np.log(frame[ticker_a])
    frame[f"log_{ticker_b}"] = np.log(frame[ticker_b])

    # Estimate a rolling hedge ratio from the recent co-movement of the pair.
    # This is still a simple model, but it is materially closer to how relative-
    # value research is usually framed than a permanently fixed 1:1 ratio.
    rolling_cov = frame[f"log_{ticker_a}"].rolling(window=hedge_window).cov(frame[f"log_{ticker_b}"])
    rolling_var = frame[f"log_{ticker_b}"].rolling(window=hedge_window).var()
    frame["hedge_ratio"] = rolling_cov.div(rolling_var.replace(0.0, np.nan))
    frame["hedge_ratio"] = frame["hedge_ratio"].replace([np.inf, -np.inf], np.nan)

    # Rolling estimates define the local equilibrium that the mean-reversion
    # process is judged against. We require a full window before generating
    # signals to avoid unstable early estimates.
    frame["spread"] = frame[f"log_{ticker_a}"] - frame["hedge_ratio"] * frame[f"log_{ticker_b}"]
    frame["spread_mean"] = frame["spread"].rolling(window=signal_window).mean()
    frame["spread_std"] = frame["spread"].rolling(window=signal_window).std()
    frame["spread_std"] = frame["spread_std"].clip(lower=min_spread_vol)

    if frame["spread_std"].dropna().empty:
        raise ValueError("Spread volatility could not be estimated from the available history.")

    frame["zscore"] = (frame["spread"] - frame["spread_mean"]) / frame["spread_std"]

    # Leg returns are stored explicitly so the backtest can express market
    # neutrality as a long/short combination rather than pretending the spread
    # itself is directly tradable.
    frame["return_a"] = frame[ticker_a].pct_change()
    frame["return_b"] = frame[ticker_b].pct_change()

    frame = frame.dropna(how="any").copy()

    if len(frame) == 0:
        raise ValueError(
            "No rows remain after computing rolling statistics. Increase the date range "
            "or decrease the rolling windows."
        )

    return frame


def generate_positions(
    zscore: pd.Series,
    entry_threshold: float,
    exit_threshold: float,
) -> pd.Series:
    """Generate stateful trading positions from the z-score signal.

    Trading logic:
    - If the spread is very high relative to history, short the spread.
    - If the spread is very low relative to history, long the spread.
    - If the spread reverts close enough to its mean, flatten the position.

    The position is expressed in spread units:
    - `+1` means long the spread: long asset A, short asset B
    - `-1` means short the spread: short asset A, long asset B
    - `0` means no active trade

    Args:
        zscore: Standardized spread series.
        entry_threshold: Absolute z-score at which a position is initiated.
        exit_threshold: Absolute z-score below which an open position is closed.

    Returns:
        Stateful position series aligned with the z-score index.
    """

    if entry_threshold <= exit_threshold:
        raise ValueError("entry_threshold must be greater than exit_threshold.")

    positions: list[int] = []
    current_position = 0

    for value in zscore:
        if value <= -entry_threshold:
            current_position = 1
        elif value >= entry_threshold:
            current_position = -1
        elif abs(value) <= exit_threshold:
            current_position = 0

        positions.append(current_position)

    return pd.Series(positions, index=zscore.index, name="position")
