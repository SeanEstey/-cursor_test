# Hyperliquid WebSocket Listener

A minimal Python WebSocket listener for Hyperliquid that subscribes to real-time streams like `trades` or `l2Book` and prints incoming messages.

## Install

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Run

- Trades for BTC on mainnet:

```bash
python hyperliquid_ws_listener.py --coin BTC --type trades
```

- L2 order book for ETH on testnet:

```bash
python hyperliquid_ws_listener.py --coin ETH --type l2Book --testnet
```

- Candles (if supported by your endpoint), e.g. 1-minute for BTC:

```bash
python hyperliquid_ws_listener.py --coin BTC --type candle --interval 1m
```

Press Ctrl+C to stop. The script will auto-reconnect with exponential backoff on errors.