# Drop-in replacement for fetch_series (handles MultiIndex from yfinance)
import pandas as pd
import yfinance as yf

def fetch_series(symbol: str) -> pd.Series:
    try:
        df = yf.download(symbol, period="1y", auto_adjust=True, progress=False)
        if df is None or df.empty:
            return pd.Series(dtype=float)

        # MultiIndex (e.g., ('Close','BTC-USD'))
        if isinstance(df.columns, pd.MultiIndex):
            lv0 = df.columns.get_level_values(0)
            # Prefer Adj Close, else Close
            if "Adj Close" in lv0:
                sub = df["Adj Close"]
                # sub may be a Series (single symbol) or DataFrame (multi)
                s = sub if isinstance(sub, pd.Series) else (
                    sub[symbol] if symbol in sub.columns else sub.iloc[:, 0]
                )
            elif "Close" in lv0:
                sub = df["Close"]
                s = sub if isinstance(sub, pd.Series) else (
                    sub[symbol] if symbol in sub.columns else sub.iloc[:, 0]
                )
            else:
                return pd.Series(dtype=float)
        else:
            # Simple columns
            col = "Adj Close" if "Adj Close" in df.columns else ("Close" if "Close" in df.columns else None)
            if col is None:
                return pd.Series(dtype=float)
            s = df[col]

        return pd.Series(pd.to_numeric(s, errors="coerce").dropna(), name=symbol)
    except Exception:
        return pd.Series(dtype=float)
