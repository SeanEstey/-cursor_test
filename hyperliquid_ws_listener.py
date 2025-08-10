#!/usr/bin/env python3
import asyncio
import json
import signal
import sys
from typing import Optional

import argparse
import websockets


MAINNET_WS_URL = "wss://api.hyperliquid.xyz/ws"
TESTNET_WS_URL = "wss://api.hyperliquid-testnet.xyz/ws"


def build_subscription_message(stream_type: str, coin: str, interval: Optional[str] = None) -> dict:
    subscription: dict = {"type": stream_type}
    # Hyperliquid docs commonly use key "coin" for asset symbol
    # Some sources show "asset"; we stick to "coin" which works for trades/l2Book
    subscription["coin"] = coin
    if stream_type == "candle" and interval:
        subscription["interval"] = interval
    return {"method": "subscribe", "subscription": subscription}


async def listen(url: str, subscription: dict) -> None:
    backoff_seconds = 1
    max_backoff = 30

    while True:
        try:
            async with websockets.connect(url, ping_interval=20, ping_timeout=20) as ws:
                await ws.send(json.dumps(subscription))
                print(f"Subscribed with: {json.dumps(subscription)}")
                backoff_seconds = 1

                async for message in ws:
                    try:
                        data = json.loads(message)
                    except json.JSONDecodeError:
                        print(f"Raw message: {message}")
                        continue
                    print(json.dumps(data, separators=(",", ":")))
        except asyncio.CancelledError:
            raise
        except Exception as exc:
            print(f"WebSocket error: {exc}. Reconnecting in {backoff_seconds}s...")
            await asyncio.sleep(backoff_seconds)
            backoff_seconds = min(max_backoff, backoff_seconds * 2)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Hyperliquid WebSocket listener")
    parser.add_argument("--coin", "--asset", dest="coin", required=True, help="Asset symbol, e.g. BTC, ETH")
    parser.add_argument(
        "--type",
        dest="stream_type",
        choices=["trades", "l2Book", "candle", "bbo", "allMids"],
        default="trades",
        help="Subscription type",
    )
    parser.add_argument("--interval", dest="interval", default=None, help="Interval for candle stream, e.g. 1m, 5m")
    parser.add_argument("--testnet", action="store_true", help="Use testnet endpoint")
    return parser.parse_args()


async def main() -> None:
    args = parse_args()
    ws_url = TESTNET_WS_URL if args.testnet else MAINNET_WS_URL
    sub = build_subscription_message(args.stream_type, args.coin, args.interval)

    stop_event = asyncio.Event()

    def handle_sigint(signum, frame):  # type: ignore[no-untyped-def]
        stop_event.set()

    signal.signal(signal.SIGINT, handle_sigint)
    signal.signal(signal.SIGTERM, handle_sigint)

    listener_task = asyncio.create_task(listen(ws_url, sub))
    await stop_event.wait()
    listener_task.cancel()
    try:
        await listener_task
    except asyncio.CancelledError:
        pass


if __name__ == "__main__":
    if sys.version_info < (3, 9):
        print("Python 3.9+ is required.")
        sys.exit(1)
    asyncio.run(main())