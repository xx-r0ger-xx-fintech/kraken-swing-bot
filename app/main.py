import os
import time
import datetime

import pytz
from dotenv import load_dotenv

load_dotenv()

from app import config
from app.strategy import calculate_signals
from app import logger
from app import exchange

ET = pytz.timezone("America/New_York")

STRATEGY_CONFIG = {
    "EMA_SHORT":          config.EMA_SHORT,
    "EMA_LONG":           config.EMA_LONG,
    "RSI_PERIOD":         config.RSI_PERIOD,
    "RSI_BUY_THRESHOLD":  config.RSI_BUY_THRESHOLD,
    "RSI_SELL_THRESHOLD": config.RSI_SELL_THRESHOLD,
}


# ── Scan window ────────────────────────────────────────────────────────────────

def is_scan_window() -> bool:
    """Returns True during the daily 25-minute scan window."""
    now          = datetime.datetime.now(ET)
    window_open  = now.replace(hour=config.SCAN_HOUR, minute=config.SCAN_MINUTE, second=0, microsecond=0)
    window_close = window_open + datetime.timedelta(minutes=25)
    return window_open <= now <= window_close


# ── Core scan ──────────────────────────────────────────────────────────────────

def run_scan(api):
    logger.log("=== Kraken Swing Bot — daily scan ===")

    try:
        usd_balance, holdings = exchange.get_account_state(api, config.WATCHLIST)
        trade_size  = min(usd_balance * config.TRADE_SIZE_PCT, config.MAX_TRADE_SIZE)

        logger.log_scan_start(usd_balance, trade_size, holdings, len(config.WATCHLIST))

        for asset in config.WATCHLIST:
            pair = config.PAIR_MAP.get(asset)
            if not pair:
                logger.log_skipped(asset, "No pair mapping defined")
                continue

            try:
                df = exchange.get_ohlcv(pair, config.BARS_TO_FETCH)
                if df is None or len(df) < config.EMA_LONG:
                    logger.log_skipped(asset, "Insufficient data")
                    continue

                signal, reason = calculate_signals(df, STRATEGY_CONFIG)
                price          = exchange.get_current_price(pair) or float(df.iloc[-1]["close"])

                logger.log_decision(asset, signal, reason, price)

                # ── SELL: exit if we hold this asset and trend reversed ──
                if signal == "SELL" and asset in holdings:
                    volume = holdings[asset]
                    exchange.place_sell(api, pair, volume)
                    logger.log_order(asset, "SELL", price, volume, sl=0)
                    del holdings[asset]
                    usd_balance += volume * price

                # ── BUY: enter if we have room and cash ──
                elif signal == "BUY" and asset not in holdings:
                    if len(holdings) >= config.MAX_POSITIONS:
                        logger.log_skipped(asset, "Max positions reached")
                        continue
                    if usd_balance < trade_size:
                        logger.log_skipped(asset, f"Insufficient balance (${usd_balance:.2f})")
                        continue

                    volume   = round(trade_size / price, 6)
                    sl_price = round(price * (1 - config.STOP_LOSS_PCT), 2)

                    exchange.place_buy(api, pair, volume, sl_price)
                    logger.log_order(asset, "BUY", price, volume, sl=sl_price)

                    holdings[asset] = volume
                    usd_balance    -= trade_size

                time.sleep(1)  # respect Kraken rate limits

            except Exception as e:
                logger.log_error(f"{asset}: {e}")

    except Exception as e:
        logger.log_error(f"Scan aborted: {e}")

    finally:
        logger.log_scan_end()


# ── Main loop ──────────────────────────────────────────────────────────────────

def main():
    logger.log("Kraken Swing Bot started")
    api = exchange.get_client()

    scanned_today  = False
    last_scan_date = None

    while True:
        now   = datetime.datetime.now(ET)
        today = now.date()

        if last_scan_date != today:
            scanned_today  = False
            last_scan_date = today

        if not scanned_today and is_scan_window():
            run_scan(api)
            scanned_today = True

        time.sleep(60)


if __name__ == "__main__":
    main()
