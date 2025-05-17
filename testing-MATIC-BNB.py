import asyncio
import json
import os
from datetime import datetime
from multiprocessing import Process
import websockets

# List of symbols to track
SYMBOLS = ["BTCUSDT", "ETHUSDT", "BNBUSDT"]  # You can expand this list

# Build combined stream URL for all symbols
def build_stream_url(symbols):
    streams = "/".join([f"{symbol.lower()}@bookTicker" for symbol in symbols])
    return f"wss://stream.binance.com:9443/stream?streams={streams}"

async def listen_and_log(symbols):
    filename_map = {symbol: f"data/{symbol}.json" for symbol in symbols}
    price_log = {symbol: {} for symbol in symbols}

    async with websockets.connect(build_stream_url(symbols)) as ws:
        async for message in ws:
            data = json.loads(message)
            symbol = data["data"]["s"]
            bid = data["data"]["b"]
            ask = data["data"]["a"]

            timestamp = datetime.utcnow().isoformat(timespec='milliseconds')
            log_entry = {
                timestamp: {
                    "bid": bid,
                    "ask": ask
                }
            }

            filename = filename_map[symbol]

            if os.path.exists(filename):
                with open(filename, "r") as f:
                    existing = json.load(f)
            else:
                existing = {}

            existing.update(log_entry)

            with open(filename, "w") as f:
                json.dump(existing, f, indent=2)

async def main():
    await listen_and_log(SYMBOLS)

def start():
    asyncio.run(main())

if __name__ == "__main__":
    start()
