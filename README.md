# Kraken Swing Bot

A Python swing trading bot for crypto on Kraken, running on DigitalOcean App Platform. Uses the same EMA + RSI + VWAP confluence strategy as the Alpaca Swing Bot, adapted for 24/7 crypto markets.

---

## How It Works

Every day at **9:35 AM ET**, the bot:

1. Pulls 90 days of daily OHLCV data for each asset in the watchlist
2. Runs signal strategy — all three indicators must align
3. Places market buy orders (with stop-loss) for BUY signals
4. Exits positions with market sell orders on SELL signals
5. Logs every decision to DigitalOcean logs, GitHub, and Discord

---

## Signal Strategy

| Indicator | Period | Buy Condition |
|---|---|---|
| **EMA crossover** | 20 / 50 | Short EMA > Long EMA (0.5% tolerance) |
| **RSI** | 14 | RSI > 55 |
| **VWAP** | Rolling 20-day | Price > VWAP |

**Exit:** SELL signal fires when all three flip bearish. A stop-loss order is attached to every buy as a safety net.

---

## Risk Management

| Setting | Default |
|---|---|
| Trade size | 20% of USD balance |
| Max trade size | $500 |
| Max open positions | 3 |
| Stop loss | -4% (attached to every buy order) |

---

## Watchlist

Default: `XBT, ETH, SOL, ADA, DOT, LINK, AVAX`

Override via `WATCHLIST` env var (comma-separated Kraken base asset names).

---

## Logging

After every scan a Discord notification is always sent, regardless of whether trades were placed. It uses multiple color-coded embeds:

| Embed | Color | Content |
|---|---|---|
| Account Snapshot | Blue | USD balance, trade size, current holdings |
| Buy Orders | Green | Any buy orders executed this scan |
| Sell Orders | Red | Any sell orders executed this scan |
| Signals Evaluated | Yellow | Every asset that reached strategy evaluation with reason |
| Pre-filter Skips | Purple | Assets skipped before strategy (max positions, no balance, etc.) |
| Scan Summary | Blue | Total counts + next scan time |

Pre-filter and trade embeds are omitted when empty. The summary is always present.

- **DigitalOcean logs** — full detail, real-time
- **GitHub** — daily markdown committed to `storage/logs/YYYY-MM-DD.md`

---

## Project Structure

```
kraken-swing-bot/
├── app/
│   ├── config.py      # All settings, configurable via env vars
│   ├── strategy.py    # EMA + RSI + VWAP signal logic
│   ├── exchange.py    # Kraken API (balance, OHLCV, orders)
│   ├── logger.py      # DO logs, GitHub commit, Discord webhook
│   └── main.py        # Orchestration and daily scan loop
├── storage/
│   └── logs/          # Daily trade log markdown files
├── deploy.py          # Automated DigitalOcean deployment script
├── test_notify.py     # Send a test Discord notification with mock data
├── Dockerfile
└── requirements.txt
```

---

## Environment Variables

| Variable | Required | Description |
|---|---|---|
| `KRAKEN_API_KEY` | Yes | Kraken API key |
| `KRAKEN_API_SECRET` | Yes | Kraken API secret |
| `GITHUB_TOKEN` | Yes | GitHub token with `repo` scope |
| `DISCORD_WEBHOOK_URL` | Yes | Discord #kraken-bot webhook URL |
| `WATCHLIST` | No | Comma-separated base assets (default: XBT,ETH,SOL,ADA,DOT,LINK,AVAX) |
| `TRADE_SIZE_PCT` | No | Fraction of balance per trade (default: 0.20) |
| `MAX_TRADE_SIZE` | No | Hard cap per trade in dollars (default: 500) |
| `MAX_POSITIONS` | No | Max concurrent holdings (default: 3) |
| `STOP_LOSS_PCT` | No | Stop loss percentage (default: 0.04) |
| `EMA_SHORT` | No | Short EMA period (default: 20) |
| `EMA_LONG` | No | Long EMA period (default: 50) |
| `RSI_BUY_THRESHOLD` | No | RSI buy threshold (default: 55) |
| `RSI_SELL_THRESHOLD` | No | RSI sell threshold (default: 45) |

---

## Deployment

### Automated (recommended)

1. Copy `.env.example` to `.env` and fill in your credentials
2. Run:

```bash
python deploy.py
```

The script creates the DO app, sets all secrets, and tails the deployment automatically.

### Manual (DigitalOcean App Platform)

1. Connect this repo to DigitalOcean App Platform
2. Set component type to **Worker**
3. Set run command to `python -m app.main`
4. Add environment variables (see below)
5. Deploy
