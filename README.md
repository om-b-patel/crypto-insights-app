# Crypto Insights App

This Streamlit app allows you to enter a portfolio of crypto or stock tickers with quantities and see how your holdings have performed over the past year.  It aggregates price data using [`yfinance`](https://pypi.org/project/yfinance/), calculates your portfolio value through time, and displays allocation breakdowns.

Each session logs a timestamp to a local SQLite database (`insights_usage.db`) to help you track usage and demonstrate engagement.

## Installation

1. Navigate into the `crypto_insights_app` directory.
2. Install dependencies with pip:

```bash
pip install -r requirements.txt
```

## Running the App

Start the app locally with:

```bash
streamlit run app.py
```

When prompted, enter your holdings in the format `TICKER:quantity` separated by commas, for example:

```
BTC-USD:0.2, ETH-USD:1.5, AAPL:10
```

The app will fetch historical price data for each ticker, compute daily portfolio value, and display a line chart.  It also shows your current allocation across each asset.

## Proving Usage

To verify that the app has been executed, inspect the `insights_usage.db` database.  Each time the app runs it appends a row to the `usage_log` table with a timestamp.  You can view the log with:

```bash
python -c "import sqlite3; conn = sqlite3.connect('insights_usage.db'); print(conn.execute('SELECT * FROM usage_log').fetchall())"
```

Taking a screenshot of this table or including a record count is a simple way to demonstrate user engagement.