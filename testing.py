
import asyncio
import websockets
import json
import datetime

# --- Settings ---
SPIKE_THRESHOLD = 0.01      # 1% upward change in BTC
GAP_THRESHOLD   = 0.002     # 0.2% gap closure threshold for XRP
STREAM_URL = "wss://stream.binance.com:9443/stream?streams=btcusdt@trade/xrpusdt@trade"

# --- Global price store and spike events log ---
latest_prices = {"BTCUSDT": None, "XRPUSDT": None}

# Each spike event is a dict that stores:
# - spike_time: datetime of BTC spike detection
# - btc_old: BTC price before spike
# - btc_new: BTC price at spike
# - xrp_baseline: the XRPUSDT price at spike time (used as baseline)
# - gap_closed: flag if the gap condition has been met
# - gap_close_time: datetime when gap closed
spike_events = []

async def process_message(message: str):
    global latest_prices, spike_events

    data = json.loads(message)
    # Combined stream messages have structure:
    # {
    #   "stream": "<symbol>@trade",
    #   "data": { ... trade event ... }
    # }
    stream = data.get("stream")
    event = data.get("data", {})
    symbol = event.get("s")  # e.g. "BTCUSDT", "XRPUSDT"
    # Convert event price to float and extract timestamp (in ms)
    try:
        price = float(event.get("p"))
        event_time = int(event.get("T"))
    except (TypeError, ValueError):
        return

    dt = datetime.datetime.fromtimestamp(event_time / 1000)

    # Get the previous price for comparison (if any)
    old_price = latest_prices.get(symbol)
    latest_prices[symbol] = price

    # --- Check for BTCUSDT spike ---
    if symbol == "BTCUSDT" and old_price is not None:
        pct_change = (price - old_price) / old_price
        # Look for an upward spike exceeding 1%
        if pct_change > SPIKE_THRESHOLD:
            print(f"[{dt}] BTC Spike detected: old={old_price:.2f}, new={price:.2f}, change={pct_change*100:.2f}%")
            # Record a spike event: capture the XRPUSDT price as baseline if available.
            xrp_baseline = latest_prices.get("XRPUSDT")
            spike_event = {
                "spike_time": dt,
                "btc_old": old_price,
                "btc_new": price,
                "xrp_baseline": xrp_baseline,  # baseline XRP price at spike
                "gap_closed": False,
                "gap_close_time": None,
            }
            spike_events.append(spike_event)

    # --- Check for XRPUSDT gap closure ---
    if symbol == "XRPUSDT":
        # For each recorded spike that hasn't had its gap closed...
        for event_dict in spike_events:
            if not event_dict["gap_closed"] and event_dict["xrp_baseline"] is not None:
                baseline = event_dict["xrp_baseline"]
                # Define gap as percent difference between current XRP price and baseline
                gap_pct = abs(price - baseline) / baseline
                if gap_pct < GAP_THRESHOLD:
                    event_dict["gap_closed"] = True
                    event_dict["gap_close_time"] = dt
                    gap_duration = (dt - event_dict["spike_time"]).total_seconds() / 60
                    print(f"[{dt}] XRP Gap closed: XRPUSDT current={price:.4f}, baseline={baseline:.4f}, gap={gap_pct*100:.2f}% (closed in {gap_duration:.2f} minutes)")

async def consumer_handler():
    async with websockets.connect(STREAM_URL) as ws:
        async for message in ws:
            await process_message(message)

async def main():
    print("Starting Binance WebSocket client for BTCUSDT and XRPUSDT trades...")
    await consumer_handler()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Client stopped.")
