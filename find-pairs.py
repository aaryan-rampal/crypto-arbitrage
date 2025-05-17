import asyncio
import json
import os
from datetime import datetime
from multiprocessing import Process
import aiohttp

# Fetch all trading symbols from Binance and find valid USDT-based triangular arbitrage opportunities
def find_usdt_triangles(symbols):
    usdt_pairs = [s for s in symbols if s.endswith("USDT")]
    other_pairs = set(symbols)
    triangles = []

    for usdt_pair in usdt_pairs:
        base = usdt_pair[:-4]  # Strip 'USDT'
        for pair in other_pairs:
            if pair.startswith(base) and pair != usdt_pair:
                alt = pair[len(base):]
                reverse_usdt = f"{alt}USDT"
                if reverse_usdt in other_pairs:
                    triangles.append((usdt_pair, pair, reverse_usdt))
    return triangles

async def fetch_all_symbols():
    url = "https://api.binance.com/api/v3/exchangeInfo"
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as resp:
            data = await resp.json()
            return [s['symbol'] for s in data['symbols'] if s['status'] == 'TRADING']

async def main():
    symbols = await fetch_all_symbols()
    triangles = find_usdt_triangles(symbols)
    print(f"Found {len(triangles)} USDT-based triangles.")
    for t in triangles:
        print(t)

def start():
    asyncio.run(main())

if __name__ == "__main__":
    start()
