# Simplified Binance Futures Testnet Trading Bot

This project implements a minimal trading bot for Binance Futures Testnet (USDT-M) using REST-signed requests.

Features
- Place MARKET, LIMIT, and a simplified STOP_LIMIT orders
- Supports BUY and SELL
- Command-line interface with input validation
- Logs requests, responses, and errors to `bot.log`

Setup
1. Create testnet API keys: https://testnet.binancefuture.com
2. Install dependencies:

```bash
python -m pip install -r requirements.txt
```

3. Export API credentials or pass via CLI:

Windows (PowerShell):

```powershell
$env:API_KEY = 'your_api_key'
$env:API_SECRET = 'your_api_secret'
```

Usage

Place a market buy order for BTCUSDT with quantity 0.001:

```bash
python main.py --symbol BTCUSDT --side BUY --type MARKET --quantity 0.001
```

Place a limit sell order:

```bash
python main.py --symbol BTCUSDT --side SELL --type LIMIT --quantity 0.001 --price 55000
```

Place a simplified stop-limit order:

```bash
python main.py --symbol BTCUSDT --side SELL --type STOP_LIMIT --quantity 0.001 --stop-price 54000 --price 53900
```

Notes
- This implementation uses direct REST signed requests against the Futures Testnet base: `https://testnet.binancefuture.com`.
- Use testnet keys only; do not use mainnet keys here.
- The `STOP_LIMIT` option is a simplified representation and may need adjustments for production.


