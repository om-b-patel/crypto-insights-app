import streamlit as st
import yfinance as yf
import pandas as pd
import sqlite3
from datetime import datetime, UTC


def log_usage() -> None:
    conn = sqlite3.connect("insights_usage.db")
    cur = conn.cursor()
    cur.execute("CREATE TABLE IF NOT EXISTS usage_log (id INTEGER PRIMARY KEY AUTOINCREMENT, timestamp TEXT)")
    cur.execute("INSERT INTO usage_log (timestamp) VALUES (?)", (datetime.now(UTC).isoformat(),))
    conn.commit()
    conn.close()


def parse_holdings(s: str) -> dict:
    out = {}
    if not s:
        return out
    for part in [p.strip() for p in s.split(",") if p.strip()]:
        if ":" not in part:
            continue
        sym, qty = part.split(":", 1)
        try:
            out[sym.strip().upper()] = float(qty.strip())
        except ValueError:
            pass
    return out


def fetch_series(symbol: str) -> pd.Series:
    """Return a 1y adjusted close Series (MultiIndex-safe)."""
    try:
        df = yf.download(symbol, period="1y", auto_adjust=True, progress=False)
        if df is None or df.empty:
            return pd.Series(dtype=float, name=symbol)

        # Handle MultiIndex (('Adj Close','BTC-USD')) or simple columns
        if isinstance(df.columns, pd.MultiIndex):
            lvl0 = df.columns.get_level_values(0)
            if "Adj Close" in lvl0:
                sub = df["Adj Close"]
            elif "Close" in lvl0:
                sub = df["Close"]
            else:
                return pd.Series(dtype=float, name=symbol)
            s = sub if isinstance(sub, pd.Series) else (sub[symbol] if symbol in sub.columns else sub.iloc[:, 0])
        else:
            col = "Adj Close" if "Adj Close" in df.columns else ("Close" if "Close" in df.columns else None)
            if col is None:
                return pd.Series(dtype=float, name=symbol)
            s = df[col]

        s = pd.to_numeric(pd.Series(s), errors="coerce").dropna()
        s.name = symbol
        return s
    except Exception:
        return pd.Series(dtype=float, name=symbol)


def build_portfolio_df(holdings: dict) -> pd.DataFrame:
    """Align on daily frequency, forward-fill gaps, then compute Portfolio."""
    frames = []
    for sym, qty in holdings.items():
        if qty <= 0:
            continue
        s = fetch_series(sym)
        if s.empty:
            continue
        frames.append((sym, s * float(qty)))
    if not frames:
        return pd.DataFrame()

    # Outer-join all series → calendar → daily asfreq → ffill
    df = pd.concat([f[1].rename(f[0]) for f in frames], axis=1, join="outer")
    if df.empty:
        return pd.DataFrame()
    # Ensure DateTimeIndex and daily frequency
    df.index = pd.to_datetime(df.index)
    df = df.sort_index()
    # Reindex to daily calendar covering full span and ffill prices
    daily_index = pd.date_range(df.index.min(), df.index.max(), freq="D")
    df = df.reindex(daily_index).ffill()

    df["Portfolio"] = df.sum(axis=1, skipna=True)
    return df


def main():
    # Log once per session
    if "logged_once" not in st.session_state:
        log_usage()
        st.session_state["logged_once"] = True

    st.title("Crypto Insights App")
    st.write("Enter holdings like `BTC-USD:0.2, ETH-USD:1.5`")

    user_input = st.text_input("Holdings", "BTC-USD:0.2, ETH-USD:1.5")
    holdings = parse_holdings(user_input)

    if not holdings:
        st.warning("Please enter at least one holding.")
        return

    df = build_portfolio_df(holdings)
    if df.empty or "Portfolio" not in df.columns:
        st.error("No data available. Try BTC-USD, ETH-USD, SPY, AAPL.")
        return

    st.subheader("Portfolio Value Index")
    port = pd.to_numeric(df["Portfolio"], errors="coerce").dropna()
    if len(port) >= 2:
        base = float(port.iloc[0]) if float(port.iloc[0]) != 0 else float(port.replace(0, float("nan")).dropna().iloc[0])
        idx = (port / base) * 100.0
        st.line_chart(pd.DataFrame({"Portfolio Index": idx}))
    else:
        st.info("Not enough data points to plot index yet.")

    st.subheader("Current Allocation")
    latest_values = df.iloc[-1].drop(labels=["Portfolio"]).dropna()
    total = float(latest_values.sum()) if not latest_values.empty else 0.0
    if total > 0:
        alloc = (latest_values / total) * 100.0
        st.bar_chart(alloc.to_frame("Weight (%)"))
        st.dataframe(latest_values.sort_values(ascending=False).to_frame("Latest Value"))
    else:
        st.info("No latest values available.")

if __name__ == "__main__":
    main()
