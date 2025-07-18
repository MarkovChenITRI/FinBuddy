import asyncio
import json
import websockets
from datetime import datetime
import csv
import os
import requests
import logging

async def PairedTradingStreamer(symbol, verbose=True):
    logging.basicConfig(
        filename=f"./logs/{symbol}.txt", 
        level=logging.INFO, 
        format="%(message)s",
        filemode="w"
    )
    async with websockets.connect(f"wss://stream.binance.com:9443/ws/{symbol}@trade") as websocket:
        print(f"Connected to {symbol} WebSocket")
        while True:
            try:
                message = await websocket.recv()
                data = json.loads(message)
                event_time = datetime.fromtimestamp(data['E'] / 1000).strftime('%Y-%m-%d %H:%M:%S')
                role = "Maker" if data['m'] else "Taker"
                message = f"Datetime: {event_time}, Price: {data['p']}, Quantity: {data['q']}, Role: {role}"
                logging.info(message)
                if verbose:
                    print(message)
            except Exception as e:
                logging.error(f"Error: {e}")
                break

async def BinanceKlineStreamer(symbol, interval="5m", verbose=True):
    # 設定 CSV 檔案路徑
    csv_file = f"./logs/{symbol}_{interval}.csv"
    file_exists = os.path.isfile(csv_file)

    # 使用 Binance API 取得先驗資料
    base_url = "https://api.binance.com/api/v3/klines"
    params = {
        "symbol": "BTCUSDT",
        "interval": "5m",
        "limit": 180
    }
    response = requests.get(base_url, params=params)
    data = response.json()

    # 整理資料並寫入 CSV
    with open(csv_file, mode="w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow(["Datetime", "Open", "High", "Low", "Close", "Volume"])

        for entry in data:  # 忽略最後一筆資料
            close_time = datetime.fromtimestamp(entry[6] / 1000).strftime('%Y-%m-%d %H:%M:%S')
            volume_in_usd = float(entry[5]) * float(entry[4])  # 將 Volume 轉換為法幣價值
            writer.writerow([
                close_time, entry[1], entry[2], entry[3], entry[4], volume_in_usd
            ])

    async with websockets.connect(f"wss://stream.binance.com:9443/ws/{symbol}@kline_{interval}") as websocket:
        print(f"Connected to {symbol} Kline WebSocket ({interval})")
        while True:
            try:
                message = await websocket.recv()
                data = json.loads(message)
                kline = data['k']
                close_time = datetime.fromtimestamp(kline['T'] / 1000).strftime('%Y-%m-%d %H:%M:%S')

                # 寫入 CSV 檔案
                with open(csv_file, mode="a", newline="", encoding="utf-8") as file:
                    writer = csv.writer(file)
                    writer.writerow([
                        close_time, kline['o'], kline['h'], kline['l'], kline['c'], kline['v']
                    ])

                # 可選的打印輸出
                if verbose:
                    print(f"Datetime: {close_time}, Open: {kline['o']}, High: {kline['h']}, Low: {kline['l']}, Close: {kline['c']}, Volume: {kline['v']}")
            except Exception as e:
                print(f"Error: {e}")
                break

if __name__ == "__main__":
    asyncio.run(BinanceKlineStreamer("btcusdt"))