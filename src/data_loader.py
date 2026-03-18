"""Utilities for downloading and preparing historical price data."""

from __future__ import annotations

from typing import Iterable

import pandas as pd
import yfinance as yf


def download_price_data(
    tickers: Iterable[str],
    start_date: str,
    end_date: str,
    price_field: str = "Adj Close",
) -> pd.DataFrame:
    """Download historical prices for the requested tickers.

    The research pipeline starts with reliable, aligned price histories. In
    practice, external market data APIs can return surprising shapes depending
    on the number of tickers requested and the fields available. This function
    normalizes those variations into a simple DataFrame with one column per
    ticker and a DatetimeIndex.

    Args:
        tickers: Collection of ticker symbols to download.
        start_date: Inclusive start date in YYYY-MM-DD format.
        end_date: Inclusive end date in YYYY-MM-DD format.
        price_field: The column to extract from the Yahoo Finance payload.

    Returns:
        DataFrame of prices indexed by date.

    Raises:
        ValueError: If no data is returned or the expected price field is
            missing.
    """

    ticker_list = list(tickers)
    if not ticker_list:
        raise ValueError("At least one ticker is required to download market data.")

    downloaded = yf.download(
        tickers=ticker_list,
        start=start_date,
        end=end_date,
        auto_adjust=False,
        progress=False,
    )

    if downloaded.empty:
        raise ValueError("No market data was returned. Check tickers and date range.")

    if isinstance(downloaded.columns, pd.MultiIndex):
        if price_field not in downloaded.columns.get_level_values(0):
            available_fields = sorted(set(downloaded.columns.get_level_values(0)))
            raise ValueError(
                f"Price field '{price_field}' not found. Available fields: {available_fields}"
            )
        prices = downloaded[price_field].copy()
    else:
        if price_field not in downloaded.columns:
            available_fields = downloaded.columns.tolist()
            raise ValueError(
                f"Price field '{price_field}' not found. Available fields: {available_fields}"
            )
        prices = downloaded[[price_field]].copy()
        prices.columns = ticker_list

    prices.index = pd.to_datetime(prices.index)
    prices = prices.sort_index()

    return prices


def build_research_frame(
    prices: pd.DataFrame,
    ticker_a: str,
    ticker_b: str,
    minimum_history: int,
) -> pd.DataFrame:
    """Clean and align the pair's price history for downstream research.

    Statistical signals only make sense when both assets are observed on the
    same dates. A spread built from misaligned timestamps can produce false
    signals, so the function removes rows where either leg is missing.

    Args:
        prices: Raw price table containing at least the requested tickers.
        ticker_a: First asset in the pair.
        ticker_b: Second asset in the pair.
        minimum_history: Minimum number of aligned rows needed for downstream
            rolling estimators.

    Returns:
        A clean two-column DataFrame with aligned prices.

    Raises:
        ValueError: If the requested tickers are missing or there are too few
            aligned observations to support the rolling calculations.
    """

    missing_columns = [ticker for ticker in [ticker_a, ticker_b] if ticker not in prices.columns]
    if missing_columns:
        raise ValueError(f"Missing required ticker columns: {missing_columns}")

    clean_prices = prices[[ticker_a, ticker_b]].copy()
    clean_prices = clean_prices.dropna(how="any")

    if clean_prices.empty:
        raise ValueError("All rows were removed during alignment. Data is unusable.")

    if len(clean_prices) <= minimum_history:
        raise ValueError(
            "Insufficient aligned rows for rolling calculations. "
            f"Need more than {minimum_history}, found {len(clean_prices)}."
        )

    return clean_prices
