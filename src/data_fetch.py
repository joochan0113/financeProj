# src/data_fetch.py
from datetime import datetime, timezone, timedelta
from pathlib import Path
import time
import random
import pandas as pd
import yfinance as yf
import requests
import matplotlib.pyplot as plt
from src.config import DATA_RAW, DATA_PROCESSED, CHARTS, ensure_dirs
from src.sync import sync_local_to_onedrive

KST = timezone(timedelta(hours=9))
today = datetime.now(KST).strftime("%Y-%m-%d")

def save_df(df: pd.DataFrame, name: str, where: str = "raw"):
    folder = DATA_RAW if where == "raw" else DATA_PROCESSED
    folder.mkdir(parents=True, exist_ok=True)
    df.to_parquet(folder / f"{today}_{name}.parquet", index=True)
    df.to_csv(folder / f"{today}_{name}.csv", index=True, encoding="utf-8")

def save_png(fig, filename: str):
    Path(CHARTS).mkdir(parents=True, exist_ok=True)
    fig.savefig(Path(CHARTS) / f"{today}_{filename}.png", dpi=150, bbox_inches="tight")
    plt.close(fig)

def fetch_stock_one(ticker: str) -> pd.DataFrame | None:
    try:
        df = yf.download(ticker, period="1y", interval="1d",
                         auto_adjust=True, progress=False, threads=False)
        if df is None or df.empty:
            raise ValueError("empty df")
        return df
    except Exception as e:
        print(f"[yfinance] download failed {ticker}: {e}  try history fallback")
        try:
            df = yf.Ticker(ticker).history(period="1y", interval="1d", auto_adjust=True)
            if df is None or df.empty:
                raise ValueError("empty df from history")
            return df
        except Exception as e2:
            print(f"[yfinance] history failed {ticker}: {e2}")
            return None

def fetch_cg(session: requests.Session, coin_id: str, days: int = 365, retries: int = 4):
    url = f"https://api.coingecko.com/api/v3/coins/{coin_id}/market_chart"
    params = {"vs_currency": "usd", "days": str(days)}
    backoff = 1.0
    for attempt in range(1, retries + 1):
        try:
            r = session.get(url, params=params, timeout=30)
            if r.status_code == 429:
                sleep_s = backoff + random.uniform(0, 0.5)
                print(f"[CG] 429 {coin_id} retry in {sleep_s:.1f}s")
                time.sleep(sleep_s)
                backoff *= 2
                continue
            r.raise_for_status()
            j = r.json()
            if "prices" not in j or not j["prices"]:
                raise ValueError("no prices key")
            df = pd.DataFrame(j["prices"], columns=["timestamp", "price"])
            df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms")
            df.set_index("timestamp", inplace=True)
            return df["price"]
        except Exception as e:
            if attempt == retries:
                print(f"[CG] failed {coin_id}: {e}")
                return None
            sleep_s = backoff + random.uniform(0, 0.5)
            print(f"[CG] error {coin_id} attempt {attempt}: {e}  retry in {sleep_s:.1f}s")
            time.sleep(sleep_s)
            backoff *= 2

if __name__ == "__main__":
    ensure_dirs()

    # 주식
    stock_tickers = ["PLTR", "TSLA", "NVDA", "GOOGL", "MSFT", "META", "AMZN", "GC=F"]
    stocks_list = []
    for t in stock_tickers:
        df_t = fetch_stock_one(t)
        if df_t is None:
            continue
        df_t.columns = [f"{t}_{str(c)}" for c in df_t.columns]
        stocks_list.append(df_t)
        time.sleep(0.2)

    if stocks_list:
        stocks_raw = pd.concat(stocks_list, axis=1).sort_index()
        save_df(stocks_raw, "mag7_gold", where="raw")

        close_cols = [c for c in stocks_raw.columns if c.endswith("_Close")]
        stocks_close = stocks_raw[close_cols].copy()
        stocks_close.columns = [c.split("_")[0] for c in close_cols]
        save_df(stocks_close, "mag7_gold_close", where="processed")

        # ret = stocks_close.pct_change().fillna(0)
        # cumret = (1 + ret).cumprod() - 1
        # fig1, ax1 = plt.subplots(figsize=(11, 6))
        # cumret.plot(ax=ax1)
        # ax1.set_title(f"MAG7 plus Gold cumulative return as of {today}")
        # ax1.set_ylabel("Cumulative return")
        # ax1.grid(True)
        # save_png(fig1, "stocks_cumret")
        #
        # fig2, ax2 = plt.subplots(figsize=(11, 6))
        # stocks_close.plot(ax=ax2)
        # ax2.set_title(f"MAG7 plus Gold close price as of {today}")
        # ax2.set_ylabel("USD")
        # ax2.grid(True)
        # save_png(fig2, "stocks_close")
    else:
        print("no stock data")

    # 크립토
    session = requests.Session()
    session.headers.update({"Accept": "application/json", "User-Agent": "financeProj/1.0"})
    crypto_ids = {
        "bitcoin": "BTC",
        "ethereum": "ETH",
        "solana": "SOL",
        "dogecoin": "DOGE",
        "shiba-inu": "SHIB",
        "nexpace": "NXPC"
    }
    crypto_series = {}
    for cid, sym in crypto_ids.items():
        s = fetch_cg(session, cid, days=365)
        if s is not None:
            crypto_series[sym] = s

    if crypto_series:
        crypto_df = pd.DataFrame(crypto_series).sort_index()
        save_df(crypto_df, "crypto_prices", where="processed")

        # cret = crypto_df.pct_change().fillna(0)
        # ccum = (1 + cret).cumprod() - 1
        # fig3, ax3 = plt.subplots(figsize=(11, 6))
        # ccum.plot(ax=ax3)
        # ax3.set_title(f"Crypto cumulative return BTC ETH SOL DOGE SHIB NXPC as of {today}")
        # ax3.set_ylabel("Cumulative return")
        # ax3.grid(True)
        # save_png(fig3, "crypto_cumret")
        #
        # fig4, ax4 = plt.subplots(figsize=(11, 6))
        # crypto_df.plot(ax=ax4)
        # ax4.set_title(f"Crypto close price BTC ETH SOL DOGE SHIB NXPC as of {today}")
        # ax4.set_ylabel("USD")
        # ax4.grid(True)
        # save_png(fig4, "crypto_close")

    # Fear and Greed Index
    try:
        r = requests.get("https://api.alternative.me/fng/", params={"limit": 0, "format": "json"}, timeout=30)
        r.raise_for_status()
        fng = pd.DataFrame(r.json()["data"])
        fng["timestamp"] = pd.to_datetime(fng["timestamp"], unit="s")
        fng = fng.sort_values("timestamp").set_index("timestamp")
        fng["value"] = pd.to_numeric(fng["value"], errors="coerce")
        save_df(fng, "fear_greed_index", where="processed")

        fig5, ax5 = plt.subplots(figsize=(11, 4))
        fng["value"].plot(ax=ax5)
        ax5.set_title(f"Crypto Fear and Greed Index as of {today}")
        ax5.set_ylabel("Index")
        ax5.grid(True)
        save_png(fig5, "fear_greed_index")
    except Exception as e:
        print(f"[FNG] failed {e}")

    # 동기화
    sync_local_to_onedrive()
