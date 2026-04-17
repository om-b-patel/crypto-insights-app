# Crypto Insights App

A Streamlit app that lets you enter a portfolio of crypto or stock tickers with quantities and see how your holdings have performed over time. It pulls historical price data via `yfinance`, computes your portfolio value day by day, and visualizes current allocations across assets.

Each session logs a timestamp to a local SQLite database, which made this a nice sandbox for getting comfortable with persistent state, data fetching, and interactive charting in Python.

Built as one of my first projects while learning to ship end-to-end: data pipeline, storage, and UI in a single app.

## Stack
Python, Streamlit, yfinance, Pandas, SQLite

## Run it

```bash
pip install -r requirements.txt
streamlit run app.py
```

Enter holdings in the format `TICKER:quantity`, for example:
`BTC-USD:0.2, ETH-USD:1.5, AAPL:10`
