import asyncio
import json
import os
import requests
import websockets
from datetime import datetime

# Load configuration
with open('config.json') as f:
    config = json.load(f)
thresholds = config['thresholds']

# Telegram settings
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

def send_telegram(message: str):
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        return
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": message}
    try:
        requests.post(url, data=payload, timeout=5)
    except:
        pass

async def watch_large_trades():
    uri = "wss://fstream.binance.com/ws/!aggTrade@arr"
    while True:
        try:
            async with websockets.connect(uri) as ws:
                print("🟢 Connected to Binance Futures")
                while True:
                    msg = await ws.recv()
                    trades = json.loads(msg)
                    for t in trades:
                        symbol = t['s']
                        price = float(t['p'])
                        qty = float(t['q'])
                        direction = "BUY" if not t['m'] else "SELL"
                        value_usd = price * qty
                        thresh = thresholds.get(symbol, thresholds['others'])
                        if value_usd >= thresh:
                            now = datetime.utcnow().strftime('%H:%M:%S')
                            emoji = "🔥" if symbol in ["BTCUSDT","ETHUSDT","SOLUSDT"] else "⚠️"
                            text = (
                                f"{emoji} Büyük İşlem: {symbol}\n"
                                f"Yön: {direction} | Miktar: ${value_usd:,.2f}\n"
                                f"Fiyat: {price:.2f}\n"
                                f"Saat (UTC): {now}"
                            )
                            send_telegram(text)
        except Exception as e:
            print("🔄 Reconnecting in 5s...", e)
            await asyncio.sleep(5)

if __name__ == "__main__":
    import asyncio
    asyncio.run(watch_large_trades())
