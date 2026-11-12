"""Données de marché (yfinance), portefeuille local, indicateurs techniques/fondamentaux."""
import json, pathlib
import numpy as np, pandas as pd, yfinance as yf, streamlit as st

FILE = pathlib.Path("data/portfolio.json")  # NB: éphémère sur Streamlit Cloud (voir README)

def load_portfolio() -> pd.DataFrame:
    if FILE.exists():
        return pd.DataFrame(json.loads(FILE.read_text()))
    return pd.DataFrame([{"Ticker": "MRNA", "Quantité": 10.0, "PRU": 100.0}])

def save_portfolio(df: pd.DataFrame):
    FILE.parent.mkdir(exist_ok=True)
    df = df.dropna(subset=["Ticker"]).copy()
    df["Ticker"] = df["Ticker"].str.upper().str.strip()
    FILE.write_text(df.to_json(orient="records"))

@st.cache_data(ttl=900)  # 15 min
def get_quotes(tickers: tuple) -> dict:
    out = {}
    for t in tickers:
        try:
            h = yf.Ticker(t).history(period="5d")["Close"].dropna()
            out[t] = {"prix": float(h.iloc[-1]),
                      "var": float((h.iloc[-1] / h.iloc[-2] - 1) * 100) if len(h) > 1 else 0.0}
        except Exception:
            out[t] = {"prix": np.nan, "var": np.nan}
    return out

def enrich(df: pd.DataFrame) -> pd.DataFrame:
    """Ajoute cours, variation, valorisation et PV latente."""
    q = get_quotes(tuple(df["Ticker"]))
    d = df.copy()
    d["Cours"] = d["Ticker"].map(lambda t: q[t]["prix"])
    d["Var %"] = d["Ticker"].map(lambda t: q[t]["var"])
    d["Valeur"] = d["Cours"] * d["Quantité"]
    d["PV"] = (d["Cours"] - d["PRU"]) * d["Quantité"]
    d["PV %"] = (d["Cours"] / d["PRU"] - 1) * 100
    return d

def _rsi(c: pd.Series, n=14) -> float:
    delta = c.diff()
    up = delta.clip(lower=0).rolling(n).mean()
    dn = (-delta.clip(upper=0)).rolling(n).mean()
    return float(100 - 100 / (1 + up.iloc[-1] / dn.iloc[-1])) if dn.iloc[-1] else 100.0

@st.cache_data(ttl=900)
def get_metrics(ticker: str) -> dict:
    """RSI, volume inhabituel, croissance CA, cash runway (mois)."""
    t, m = yf.Ticker(ticker), {"Ticker": ticker}
    try:
        h = t.history(period="6mo")
        m["Prix"] = round(float(h["Close"].iloc[-1]), 2)
        m["RSI"] = round(_rsi(h["Close"]), 1)
        m["Vol x moy."] = round(float(h["Volume"].iloc[-1] / h["Volume"].tail(30).mean()), 2)
    except Exception:
        pass
    try:
        rev = t.income_stmt.loc["Total Revenue"].dropna()
        m["Croiss. CA %"] = round((rev.iloc[0] / rev.iloc[1] - 1) * 100, 1)
    except Exception:
        m["Croiss. CA %"] = None
    try:
        cash = t.balance_sheet.loc["Cash Cash Equivalents And Short Term Investments"].dropna().iloc[0]
        fcf = t.cashflow.loc["Free Cash Flow"].dropna().iloc[0]
        m["Cash (M)"] = round(cash / 1e6)
        m["Runway (mois)"] = round(cash / (-fcf / 12)) if fcf < 0 else "∞ (FCF>0)"
    except Exception:
        m["Runway (mois)"] = None
    return m

@st.cache_data(ttl=6 * 3600)
def get_earnings(tickers: tuple) -> pd.DataFrame:
    rows = []
    for tk in tickers:
        try:
            ed = yf.Ticker(tk).calendar.get("Earnings Date", [])
            if ed:
                rows.append({"Ticker": tk, "Résultats": pd.to_datetime(ed[0])})
        except Exception:
            continue
    return pd.DataFrame(rows).sort_values("Résultats") if rows else pd.DataFrame()
