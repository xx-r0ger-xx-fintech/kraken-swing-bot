"""
test_notify.py — Send a test Discord notification with mock data.

Usage:
    python test_notify.py

Requires DISCORD_WEBHOOK_URL in .env (same as the bot uses).
"""

from dotenv import load_dotenv
load_dotenv()

from app import logger


def main():
    print("Sending test Discord notification...")

    # ── Mock account state ────────────────────────────────────────────────────
    mock_holdings = {
        "XBT": 0.012500,
        "ETH": 0.850000,
    }

    logger.log_scan_start(
        balance       = 3_250.00,
        trade_size    = 500.00,
        holdings      = mock_holdings,
        watchlist_size= 7,
    )

    # ── Mock strategy signals ─────────────────────────────────────────────────
    logger.log_decision("SOL",  "BUY",  "EMA20=142.80 / EMA50=135.20 | RSI=62.1 | Price=144.50 vs VWAP=139.80", 144.50)
    logger.log_decision("ADA",  None,   "No signal — EMA not crossed (0.448 vs 0.461) | RSI too low (47.3 < 55.0)", 0.448)
    logger.log_decision("DOT",  None,   "No signal — Price below VWAP (6.82 < 7.14)", 6.82)
    logger.log_decision("LINK", "SELL", "EMA20=13.90 / EMA50=14.50 | RSI=41.8 | Price=13.75 vs VWAP=14.20", 13.75)

    # ── Mock orders ───────────────────────────────────────────────────────────
    logger.log_order("SOL",  "BUY",  144.50, volume=3.460208, sl=138.72)
    logger.log_order("LINK", "SELL", 13.75,  volume=36.363636, sl=0)

    # ── Mock pre-filter skips ─────────────────────────────────────────────────
    logger.log_skipped("XBT",  "Already in position")
    logger.log_skipped("ETH",  "Already in position")
    logger.log_skipped("AVAX", "Max positions reached")

    # ── Fire the notification ─────────────────────────────────────────────────
    logger.log_scan_end()
    print("Done.")


if __name__ == "__main__":
    main()
