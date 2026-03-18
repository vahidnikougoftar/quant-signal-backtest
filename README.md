# Quantitative Signal Research & Backtesting Pipeline

A recruiter-focused project demonstrating an end-to-end workflow for **statistical signal design, financial time series analysis, and backtesting** using Python and SQL.

## 🧠 Motivation

I built this project to better understand how quantitative investment firms transform raw market data into statistically grounded signals.

The focus was not on finding alpha, but on building a clean, reproducible pipeline that reflects real-world workflows:
data → hypothesis → signal → backtest → evaluation → monitoring.
---

## 🔍 Overview

This project builds a **market-neutral mean-reversion strategy** using historical equity price data.

It simulates a real-world quant research workflow:

- Data ingestion and cleaning  
- Feature engineering (spread, rolling statistics)  
- Statistical signal construction (z-score normalization)  
- Hypothesis-driven strategy design  
- Backtesting with transaction costs  
- Performance evaluation (Sharpe, drawdown, hit rate)  
- Visualization and diagnostics  

---

## 📈 Example Outputs

### Equity Curve
![Equity Curve](output/equity_curve.png)

### Drawdown
![Drawdown](output/drawdown.png)

### Signal Diagnostics (Z-score & Position)
![Signal](output/zscore_positions.png)

---

## 🧠 Methodology

### 1. Spread Construction
We construct a simple spread between two correlated assets:
spread = price_A - price_B

### 2. Statistical Normalization
We compute a rolling z-score: 
z = (spread - rolling_mean) / rolling_std

### 3. Trading Logic (Mean Reversion)

- Long spread when z < -threshold  
- Short spread when z > +threshold  
- Exit when z reverts toward 0  

### 4. Backtesting

- Positions are **lagged** to avoid lookahead bias  
- Transaction costs are included  
- Returns are compounded into an equity curve  

---

## 📊 Performance Metrics

- Total Return  
- Annualized Return  
- Sharpe Ratio  
- Maximum Drawdown  
- Hit Rate  

---

## 🧪 Key Findings

- Demonstrates a full research pipeline from raw data to performance evaluation  
- Highlights how rolling statistics can be used to construct interpretable signals  
- Shows importance of transaction costs and position timing  
- Provides a framework for extending into more advanced quant strategies  

---

## ⚠️ Disclaimer

This is a **research demonstration project**, not a production trading system.  
It does not claim to produce profitable or deployable strategies.

---

## ⚙️ Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
