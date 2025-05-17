import asyncio
import json
import websockets
import matplotlib.pyplot as plt
from collections import deque
import time

# Streams for Binance combined WebSocket
STREAM_URL = (
    "wss://stream.binance.com:9443/stream?streams="
    "btcusdt@bookTicker/"
    "ethusdt@bookTicker/"
    "ethbtc@bookTicker"
)

prices = {
    "BTCUSDT": {"ask": None, "bid": None},
    "ETHUSDT": {"ask": None, "bid": None},
    "ETHBTC": {"ask": None, "bid": None}
}

ratios = deque(maxlen=100)
timestamps = deque(maxlen=100)

def compute_arbitrage():
    try:
        a = float(prices["BTCUSDT"]["ask"])
        b = float(prices["ETHBTC"]["ask"])
        c = float(prices["ETHUSDT"]["bid"])
        # Convert USDT -> BTC -> ETH -> USDT
        ratio = (1 / a) * (1 / b) * c
        return ratio
    except (TypeError, ZeroDivisionError):
        return None

async def plot_loop():
    plt.ion()
    fig, ax = plt.subplots()
    while True:
        if ratios:
            ax.clear()
            ax.plot(list(timestamps), list(ratios))
            ax.set_title("Triangular Arbitrage Ratio")
            ax.set_ylabel("Ratio")
            ax.set_xlabel("Time")
            ax.axhline(1.0, color='red', linestyle='--')
            plt.pause(0.01)
        await asyncio.sleep(1)

async def listen():
    async with websockets.connect(STREAM_URL) as ws:
        async for message in ws:
            data = json.loads(message)
            stream = data["stream"]
            symbol = data["data"]["s"]
            bid = data["data"]["b"]
            ask = data["data"]["a"]
            prices[symbol] = {"bid": bid, "ask": ask}

            ratio = compute_arbitrage()
            if ratio:
                print(f"[{time.strftime('%H:%M:%S')}] Arbitrage ratio: {ratio:.6f}")
                ratios.append(ratio)
                timestamps.append(time.strftime('%H:%M:%S'))

async def main():
    await asyncio.gather(listen(), plot_loop())

asyncio.run(main())

