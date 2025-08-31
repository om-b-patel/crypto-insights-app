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


def build_portfolio_df(holdings: dict) -> pd.DataFrame:
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
    df = pd.concat([f[1].rename(f[0]) for f in frames], axis=1)
    df = df.dropna(how="all")
    df["Portfolio"] = df.sum(axis=1)
    return df


def main():
    # Log once per browser session
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
    port = df["Portfolio"].astype(float).dropna()
    if not port.empty:
        idx = (port / port.iloc[0]) * 100.0
        st.line_chart(pd.DataFrame({"Portfolio Index": idx}))

    st.subheader("Current Allocation")
    latest_values = df.iloc[-1].drop(labels=["Portfolio"]).dropna()
    total = float(latest_values.sum()) if not latest_values.empty else 0.0
    if total > 0:
        alloc = (latest_values / total) * 100.0
        st.bar_chart(alloc.to_frame("Weight (%)"))
        st.dataframe(latest_values.sort_values(ascending=False).to_frame("Latest Value"))


if __name__ == "__main__":
    main()
