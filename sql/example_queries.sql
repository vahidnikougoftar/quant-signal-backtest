-- Example schema and research queries for storing and analyzing equity prices.

-- 1. Table schema for price data
CREATE TABLE IF NOT EXISTS daily_prices (
    trade_date DATE NOT NULL,
    ticker VARCHAR(16) NOT NULL,
    open_price NUMERIC(18, 6),
    high_price NUMERIC(18, 6),
    low_price NUMERIC(18, 6),
    close_price NUMERIC(18, 6),
    adj_close NUMERIC(18, 6),
    volume BIGINT,
    PRIMARY KEY (trade_date, ticker)
);

-- 2. Query to join two tickers into a spread
WITH pair_prices AS (
    SELECT
        a.trade_date,
        a.ticker AS ticker_a,
        b.ticker AS ticker_b,
        a.adj_close AS price_a,
        b.adj_close AS price_b
    FROM daily_prices a
    INNER JOIN daily_prices b
        ON a.trade_date = b.trade_date
    WHERE a.ticker = 'NVDA'
      AND b.ticker = 'AMD'
)
SELECT
    trade_date,
    ticker_a,
    ticker_b,
    LN(price_a) - LN(price_b) AS log_spread
FROM pair_prices
ORDER BY trade_date;

-- 3. Data quality checks
-- Find duplicated rows that would violate uniqueness expectations before
-- constraints are enforced in a staging table.
SELECT
    trade_date,
    ticker,
    COUNT(*) AS duplicate_count
FROM daily_prices
GROUP BY trade_date, ticker
HAVING COUNT(*) > 1;

-- Find missing or invalid adjusted close values.
SELECT
    trade_date,
    ticker,
    adj_close,
    volume
FROM daily_prices
WHERE adj_close IS NULL
   OR adj_close <= 0
   OR volume IS NULL
   OR volume < 0
ORDER BY trade_date, ticker;

-- 4. Anomaly detection query
-- Flag unusually large one-day moves using a simple threshold on absolute
-- daily returns. In production, this can be a first pass for bad ticks.
WITH returns AS (
    SELECT
        trade_date,
        ticker,
        adj_close,
        adj_close / LAG(adj_close) OVER (
            PARTITION BY ticker
            ORDER BY trade_date
        ) - 1.0 AS daily_return
    FROM daily_prices
)
SELECT
    trade_date,
    ticker,
    adj_close,
    daily_return
FROM returns
WHERE ABS(daily_return) > 0.15
ORDER BY trade_date, ticker;

-- 5. Rolling average example
SELECT
    trade_date,
    ticker,
    adj_close,
    AVG(adj_close) OVER (
        PARTITION BY ticker
        ORDER BY trade_date
        ROWS BETWEEN 19 PRECEDING AND CURRENT ROW
    ) AS rolling_20d_avg
FROM daily_prices
WHERE ticker IN ('NVDA', 'AMD')
ORDER BY ticker, trade_date;
