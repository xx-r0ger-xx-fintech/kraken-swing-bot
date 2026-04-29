import os
import time
import logging
import requests
import pandas as pd
import krakenex

# ── Client setup ───────────────────────────────────────────────────────────────

def get_client() -> krakenex.API:
    api = krakenex.API()
    api.key    = os.getenv("KRAKEN_API_KEY", "")
    api.secret = os.getenv("KRAKEN_API_SECRET", "")
    if not api.key or not api.secret:
        raise ValueError("KRAKEN_API_KEY and KRAKEN_API_SECRET must be set")
    return api


# ── Account ────────────────────────────────────────────────────────────────────

def get_account_state(api: krakenex.API, watchlist: list) -> tuple[float, dict]:
    """
    Fetch balance once and return (usd_balance, holdings) in a single API call.
    Avoids the double Balance call that get_usd_balance + get_holdings would make.
    """
    resp = api.query_private("Balance")
    if resp.get("error"):
        raise Exception(f"Kraken Balance error: {resp['error']}")

    bal = resp["result"]

    # Sum all USD-equivalent stablecoin balances — accounts may hold any combination
    usd_balance = sum(float(bal.get(key, 0)) for key in ["ZUSD", "USD", "USDC", "USDT", "USDG"])

    # Holdings — Kraken uses X prefix for some assets (XBT → XXBT, ETH → XETH)
    holdings = {}
    for asset in watchlist:
        for key in [asset, f"X{asset}", asset.replace("XBT", "XXBT")]:
            if key in bal and float(bal[key]) > 0.0001:
                holdings[asset] = float(bal[key])
                break

    return usd_balance, holdings


# ── Market data ────────────────────────────────────────────────────────────────

def get_ohlcv(pair: str, bars: int = 90) -> pd.DataFrame | None:
    """
    Fetch daily OHLCV data from Kraken public API.
    interval=1440 = 1 day in minutes.
    """
    url    = "https://api.kraken.com/0/public/OHLC"
    params = {"pair": pair, "interval": 1440}

    try:
        resp = requests.get(url, params=params, timeout=10).json()
    except Exception as e:
        logging.warning(f"get_ohlcv({pair}): {e}")
        return None

    if resp.get("error"):
        logging.warning(f"get_ohlcv({pair}) Kraken error: {resp['error']}")
        return None

    result_key = [k for k in resp["result"] if k != "last"]
    if not result_key:
        return None

    raw = resp["result"][result_key[0]]
    df  = pd.DataFrame(
        raw,
        columns=["time", "open", "high", "low", "close", "vwap", "volume", "count"]
    )

    for col in ["open", "high", "low", "close", "volume"]:
        df[col] = df[col].astype(float)

    return df.tail(bars).reset_index(drop=True)


def get_current_price(pair: str) -> float | None:
    """Fetch latest ticker price for a pair."""
    url = f"https://api.kraken.com/0/public/Ticker?pair={pair}"
    try:
        resp = requests.get(url, timeout=10).json()
        if resp.get("error"):
            return None
        data = list(resp["result"].values())[0]
        return float(data["c"][0])
    except Exception:
        return None


# ── Orders ─────────────────────────────────────────────────────────────────────

def place_buy(api: krakenex.API, pair: str, volume: float, stop_price: float):
    """
    Place a market buy order with a conditional stop-loss close order.
    Kraken's close parameter attaches a stop-loss that triggers automatically.
    """
    params = {
        "pair":              pair,
        "type":              "buy",
        "ordertype":         "market",
        "volume":            f"{volume:.6f}",
        "close[ordertype]":  "stop-loss",
        "close[price]":      f"{stop_price:.2f}",
    }

    resp = api.query_private("AddOrder", params)
    if resp.get("error"):
        errors = resp["error"]
        if any("volume minimum not met" in e for e in errors):
            raise ValueError(f"Volume minimum not met for buy on {pair} — increase trade size")
        raise Exception(f"Buy order error: {errors}")
    return resp["result"]


def place_sell(api: krakenex.API, pair: str, volume: float):
    """Place a market sell order for the full position."""
    params = {
        "pair":      pair,
        "type":      "sell",
        "ordertype": "market",
        "volume":    f"{volume:.6f}",
    }

    resp = api.query_private("AddOrder", params)
    if resp.get("error"):
        errors = resp["error"]
        if any("volume minimum not met" in e for e in errors):
            raise ValueError(f"Volume minimum not met for sell on {pair} — dust position")
        raise Exception(f"Sell order error: {errors}")
    return resp["result"]
