import sqlite3
import streamlit as st
from datetime import datetime, UTC

def log_usage() -> None:
    conn = sqlite3.connect("insights_usage.db")
    cur = conn.cursor()
    cur.execute("CREATE TABLE IF NOT EXISTS usage_log (id INTEGER PRIMARY KEY AUTOINCREMENT, timestamp TEXT)")
    cur.execute("INSERT INTO usage_log (timestamp) VALUES (?)", (datetime.now(UTC).isoformat(),))
    conn.commit()
    conn.close()

def main():
    if "logged_once" not in st.session_state:
        log_usage()
        st.session_state["logged_once"] = True
    st.title("Crypto Insights App")
    st.write("Enter holdings like `BTC-USD:0.2, ETH-USD:1.5`")
    user_input = st.text_input("Holdings", "BTC-USD:0.2, ETH-USD:1.5")
    # (rest of your existing code here…)
